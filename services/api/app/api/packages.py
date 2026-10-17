import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthContext, require_permission
from app.db.session import get_db
from app.models.commercial import (CompanyCommercialOverride, CompanySubscription, Package, PackageFeature,
                                   PackageLimit, PackagePriceVersion, TrialGrant)
from app.models.identity import Tenant
from app.schemas.commercial import (EffectiveEntitlementsResponse, FeatureUpdateRequest,
                                    LimitUpdateRequest, OverrideRequest, PackageCreateRequest, PackageDetailsResponse,
                                    PackageResponse, PackageUpdateRequest, PriceVersionRequest, SubscriptionAssignRequest,
                                    TrialGrantRequest)
from app.services.audit import write_audit
from app.services.entitlements import MANDATORY_FEATURES, effective_entitlements

router = APIRouter(prefix="/owner", tags=["owner-commercial"])


async def _package_details(db: AsyncSession, package: Package) -> PackageDetailsResponse:
    price = await db.scalar(select(PackagePriceVersion).where(PackagePriceVersion.package_id == package.id,
                                                               PackagePriceVersion.effective_from <= datetime.now(UTC),
                                                               (PackagePriceVersion.effective_to.is_(None) | (PackagePriceVersion.effective_to > datetime.now(UTC))))
                            .order_by(PackagePriceVersion.effective_from.desc()))
    features = await db.scalars(select(PackageFeature).where(PackageFeature.package_id == package.id))
    limits = await db.scalars(select(PackageLimit).where(PackageLimit.package_id == package.id))
    return PackageDetailsResponse(id=package.id, code=package.code, name=package.name, description=package.description,
                                  is_active=package.is_active, is_archived=package.is_archived,
                                  monthly_price=price.monthly_price if price else None,
                                  annual_price=price.annual_price if price else None,
                                  currency=price.currency if price else None,
                                  discount_percent=price.discount_percent if price else None,
                                  features={row.feature_key: row.enabled for row in features},
                                  limits={row.limit_key: row.limit_value for row in limits})


@router.get("/packages", response_model=list[PackageDetailsResponse])
async def list_packages(_: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    packages = await db.scalars(select(Package).order_by(Package.created_at.asc()))
    return [await _package_details(db, package) for package in packages]


@router.post("/packages", response_model=PackageDetailsResponse, status_code=201)
async def create_package(payload: PackageCreateRequest, context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    package = Package(code=payload.code, name=payload.name, description=payload.description)
    db.add(package)
    try:
        await db.flush()
        db.add(PackagePriceVersion(package_id=package.id, currency=payload.currency, monthly_price=payload.monthly_price,
                                   annual_price=payload.annual_price, discount_percent=payload.discount_percent,
                                   effective_from=datetime.now(UTC)))
        for key, enabled in payload.features.items():
            if key in MANDATORY_FEATURES and not enabled:
                raise HTTPException(status_code=400, detail=f"Mandatory security feature cannot be disabled: {key}")
            db.add(PackageFeature(package_id=package.id, feature_key=key, enabled=enabled))
        for key, value in payload.limits.items():
            db.add(PackageLimit(package_id=package.id, limit_key=key, limit_value=value))
        await write_audit(db, context.user.id, "package.created", "package", str(package.id), {"code": package.code})
        await db.commit()
        await db.refresh(package)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Package code already exists") from exc
    return await _package_details(db, package)


@router.patch("/packages/{package_id}", response_model=PackageResponse)
async def update_package(package_id: uuid.UUID, payload: PackageUpdateRequest,
                         context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    package = await db.scalar(select(Package).where(Package.id == package_id))
    if not package: raise HTTPException(status_code=404, detail="Package not found")
    changes = payload.model_dump(exclude_unset=True)
    if "archive" in changes:
        package.is_archived = changes.pop("archive")
        if package.is_archived: package.is_active = False
    for key, value in changes.items(): setattr(package, key, value)
    await write_audit(db, context.user.id, "package.updated", "package", str(package.id), changes)
    await db.commit()
    await db.refresh(package)
    return package


@router.post("/packages/{package_id}/prices", response_model=PackageDetailsResponse)
async def add_price_version(package_id: uuid.UUID, payload: PriceVersionRequest,
                            context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    package = await db.scalar(select(Package).where(Package.id == package_id))
    if not package: raise HTTPException(status_code=404, detail="Package not found")
    db.add(PackagePriceVersion(package_id=package.id, **payload.model_dump()))
    await write_audit(db, context.user.id, "package.price_version_created", "package", str(package.id), payload.model_dump(mode="json"))
    await db.commit()
    return await _package_details(db, package)


@router.put("/packages/{package_id}/features/{feature_key}")
async def update_feature(package_id: uuid.UUID, feature_key: str, payload: FeatureUpdateRequest,
                         context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    if feature_key in MANDATORY_FEATURES and not payload.enabled:
        raise HTTPException(status_code=400, detail="Mandatory security features cannot be disabled")
    row = await db.scalar(select(PackageFeature).where(PackageFeature.package_id == package_id, PackageFeature.feature_key == feature_key))
    if row: row.enabled = payload.enabled
    else: db.add(PackageFeature(package_id=package_id, feature_key=feature_key, enabled=payload.enabled))
    await write_audit(db, context.user.id, "package.feature_updated", "package", str(package_id), {"feature": feature_key, "enabled": payload.enabled})
    await db.commit()
    return {"package_id": package_id, "feature_key": feature_key, "enabled": payload.enabled}


@router.put("/packages/{package_id}/limits/{limit_key}")
async def update_limit(package_id: uuid.UUID, limit_key: str, payload: LimitUpdateRequest,
                       context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    row = await db.scalar(select(PackageLimit).where(PackageLimit.package_id == package_id, PackageLimit.limit_key == limit_key))
    if row: row.limit_value = payload.value
    else: db.add(PackageLimit(package_id=package_id, limit_key=limit_key, limit_value=payload.value))
    await write_audit(db, context.user.id, "package.limit_updated", "package", str(package_id), {"limit": limit_key, "value": payload.value})
    await db.commit()
    return {"package_id": package_id, "limit_key": limit_key, "value": payload.value}


@router.post("/companies/{tenant_id}/subscription")
async def assign_subscription(tenant_id: uuid.UUID, payload: SubscriptionAssignRequest,
                              context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    package = await db.scalar(select(Package).where(Package.id == payload.package_id, Package.is_archived.is_(False)))
    if not tenant or not package: raise HTTPException(status_code=404, detail="Tenant or package not found")
    subscription = await db.scalar(select(CompanySubscription).where(CompanySubscription.tenant_id == tenant_id))
    if subscription: subscription.package_id = package.id; subscription.currency = payload.currency; subscription.agreed_monthly_price = payload.agreed_monthly_price; subscription.agreed_annual_price = payload.agreed_annual_price; subscription.starts_at = payload.starts_at; subscription.status = "active"
    else: db.add(CompanySubscription(tenant_id=tenant_id, package_id=package.id, currency=payload.currency, agreed_monthly_price=payload.agreed_monthly_price, agreed_annual_price=payload.agreed_annual_price, starts_at=payload.starts_at, status="active"))
    await write_audit(db, context.user.id, "company.subscription_assigned", "tenant", str(tenant_id), payload.model_dump(mode="json"))
    await db.commit()
    return {"tenant_id": tenant_id, "package_id": package.id, "price_locked": True}


@router.post("/companies/{tenant_id}/overrides")
async def create_override(tenant_id: uuid.UUID, payload: OverrideRequest,
                          context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    if payload.kind == "feature" and payload.key in MANDATORY_FEATURES and payload.bool_value is False:
        raise HTTPException(status_code=400, detail="Mandatory security features cannot be overridden off")
    if payload.kind == "feature" and payload.bool_value is None: raise HTTPException(status_code=400, detail="feature override requires bool_value")
    if payload.kind == "limit" and payload.int_value is None: raise HTTPException(status_code=400, detail="limit override requires int_value")
    if payload.kind == "price" and payload.decimal_value is None: raise HTTPException(status_code=400, detail="price override requires decimal_value")
    row = CompanyCommercialOverride(tenant_id=tenant_id, **payload.model_dump())
    db.add(row)
    await write_audit(db, context.user.id, "company.commercial_override_created", "tenant", str(tenant_id), payload.model_dump(mode="json"))
    await db.commit()
    return {"id": row.id, "tenant_id": tenant_id, "kind": row.kind, "key": row.key}


@router.post("/companies/{tenant_id}/trial")
async def grant_trial(tenant_id: uuid.UUID, payload: TrialGrantRequest,
                      context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if not tenant: raise HTTPException(status_code=404, detail="Tenant not found")
    grant = TrialGrant(tenant_id=tenant_id, starts_at=datetime.now(UTC), ends_at=payload.ends_at, reason=payload.reason)
    db.add(grant)
    tenant.license_status = "trial"
    tenant.trial_ends_at = payload.ends_at
    await write_audit(db, context.user.id, "company.trial_granted", "tenant", str(tenant_id), payload.model_dump(mode="json"))
    await db.commit()
    return {"tenant_id": tenant_id, "trial_ends_at": payload.ends_at}


@router.get("/companies/{tenant_id}/entitlements", response_model=EffectiveEntitlementsResponse)
async def get_entitlements(tenant_id: uuid.UUID, _: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    result = await effective_entitlements(db, tenant_id)
    return EffectiveEntitlementsResponse(tenant_id=result.tenant_id, package_id=result.package_id, features=result.features,
                                         limits=result.limits, monthly_price=result.monthly_price, annual_price=result.annual_price, currency=result.currency)
