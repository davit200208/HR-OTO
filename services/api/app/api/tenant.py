import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import AuthContext, require_tenant
from app.core.tenant_security import enforce_tenant_access
from app.db.session import get_db
from app.models.identity import Tenant, TenantStatus, UserRole
from app.models.tenant import TenantRecord
from app.schemas.tenant import TenantRecordResponse
from app.services.tenant_provisioning import tenant_url
from app.services.entitlements import require_feature

router = APIRouter(prefix="/tenant", tags=["tenant"])


async def _tenant_session(tenant: Tenant):
    engine = create_async_engine(tenant_url(tenant.database_name))
    return engine, async_sessionmaker(engine, expire_on_commit=False)


@router.get("/{company_code}/feature-access/{feature_key}")
async def feature_access(company_code: str, feature_key: str,
                         context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    tenant = await db.scalar(select(Tenant).where(Tenant.company_code == company_code.upper()))
    if not tenant or tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Company not found")
    enforce_tenant_access(context.user.tenant_id, tenant.id)
    await require_feature(db, tenant.id, feature_key)
    return {"feature": feature_key, "enabled": True}


@router.get("/{company_code}/records", response_model=list[TenantRecordResponse])
async def list_records(
    company_code: str,
    context: AuthContext = Depends(require_tenant),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.scalar(select(Tenant).where(Tenant.company_code == company_code.upper()))
    if not tenant or tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Company not found")
    enforce_tenant_access(context.user.tenant_id, tenant.id)
    engine, factory = await _tenant_session(tenant)
    try:
        async with factory() as tenant_db:
            result = await tenant_db.scalars(select(TenantRecord).order_by(TenantRecord.created_at.desc()))
            return list(result)
    finally:
        await engine.dispose()


@router.post("/{company_code}/records", response_model=TenantRecordResponse, status_code=201)
async def create_record(
    company_code: str,
    record_key: str,
    context: AuthContext = Depends(require_tenant),
    db: AsyncSession = Depends(get_db),
):
    if context.user.role not in {UserRole.COMPANY_OWNER, UserRole.HR_ADMIN, UserRole.MANAGER}:
        raise HTTPException(status_code=403, detail="Permission denied")
    tenant = await db.scalar(select(Tenant).where(Tenant.company_code == company_code.upper()))
    if not tenant or tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Company not found")
    enforce_tenant_access(context.user.tenant_id, tenant.id)
    engine, factory = await _tenant_session(tenant)
    try:
        async with factory() as tenant_db:
            row = TenantRecord(record_key=record_key, payload={"created_by": str(context.user.id)})
            tenant_db.add(row)
            await tenant_db.commit()
            await tenant_db.refresh(row)
            return row
    finally:
        await engine.dispose()
