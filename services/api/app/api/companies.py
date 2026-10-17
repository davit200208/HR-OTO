import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthContext, require_permission
from app.core.security import hash_password
from app.db.session import get_db
from app.models.identity import LicenseStatus, Tenant, TenantStatus, User, UserRole
from app.schemas.tenant import (CompanyCreateRequest, CompanyOwnerCreateRequest, CompanyResponse,
                                 CompanyUpdateRequest)
from app.services.audit import write_audit
from app.services.tenant_provisioning import TenantProvisioningService

router = APIRouter(prefix="/companies", tags=["companies"])
provisioner = TenantProvisioningService()


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(
    payload: CompanyCreateRequest,
    context: AuthContext = Depends(require_permission("company:create")),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.scalar(select(Tenant).where(
        (Tenant.company_code == payload.company_code) | (Tenant.subdomain == payload.subdomain)
    ))
    if existing:
        raise HTTPException(status_code=409, detail="Company code or subdomain already exists")
    tenant = Tenant(name=payload.name, company_code=payload.company_code,
                    subdomain=payload.subdomain, database_name="pending", status=TenantStatus.PROVISIONING,
                    license_status=payload.license_status, monthly_revenue=payload.monthly_revenue)
    db.add(tenant)
    try:
        await db.flush()
        database_name = await provisioner.provision(payload.company_code)
        tenant.database_name = database_name
        tenant.status = TenantStatus.ACTIVE
        db.add(User(tenant_id=tenant.id, email=payload.owner_email.lower(), full_name=payload.owner_name,
                    password_hash=hash_password(payload.owner_password), role=UserRole.COMPANY_OWNER))
        await write_audit(db, context.user.id, "company.created", "tenant", str(tenant.id),
                          {"company_code": tenant.company_code})
        await db.commit()
        await db.refresh(tenant)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Company data conflicts with an existing record") from exc
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=503, detail="Tenant provisioning failed") from exc
    return tenant


@router.get("", response_model=list[CompanyResponse])
async def list_companies(
    _: AuthContext = Depends(require_permission("company:read")),
    db: AsyncSession = Depends(get_db),
    search: str | None = Query(default=None, max_length=100),
    status: TenantStatus | None = None,
    license_status: LicenseStatus | None = None,
):
    query = select(Tenant).order_by(Tenant.created_at.desc())
    if search:
        term = f"%{search}%"
        query = query.where(or_(Tenant.name.ilike(term), Tenant.company_code.ilike(term), Tenant.subdomain.ilike(term)))
    if status:
        query = query.where(Tenant.status == status)
    if license_status:
        query = query.where(Tenant.license_status == license_status)
    result = await db.scalars(query)
    return list(result)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: uuid.UUID, _: AuthContext = Depends(require_permission("company:read")),
                      db: AsyncSession = Depends(get_db)):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == company_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="Company not found")
    return tenant


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: uuid.UUID, payload: CompanyUpdateRequest,
                         context: AuthContext = Depends(require_permission("company:create")),
                         db: AsyncSession = Depends(get_db)):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == company_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="Company not found")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(tenant, key, value)
    await write_audit(db, context.user.id, "company.updated", "tenant", str(tenant.id), changes)
    try:
        await db.commit()
        await db.refresh(tenant)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Company update conflicts with existing data") from exc
    return tenant


@router.post("/{company_id}/owner", status_code=201)
async def create_company_owner(company_id: uuid.UUID, payload: CompanyOwnerCreateRequest,
                               context: AuthContext = Depends(require_permission("company:create")),
                               db: AsyncSession = Depends(get_db)):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == company_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="Company not found")
    if await db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status_code=409, detail="Email already exists")
    user = User(tenant_id=tenant.id, email=payload.email.lower(), full_name=payload.full_name,
                password_hash=hash_password(payload.password), role=UserRole.COMPANY_OWNER)
    db.add(user)
    await write_audit(db, context.user.id, "company.owner_created", "user", str(user.id),
                      {"tenant_id": str(tenant.id), "email": user.email})
    await db.commit()
    return {"id": user.id, "email": user.email, "role": user.role, "tenant_id": tenant.id}
