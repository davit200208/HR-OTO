import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commercial import (CompanyCommercialOverride, CompanySubscription, PackageFeature, PackageLimit,
                                   PackagePriceVersion)

MANDATORY_FEATURES = frozenset({"security.authentication", "security.tenant_isolation", "security.audit"})


class EffectiveEntitlements:
    def __init__(self, tenant_id: uuid.UUID, package_id: uuid.UUID | None, features: dict[str, bool],
                 limits: dict[str, int], monthly_price: Decimal | None, annual_price: Decimal | None,
                 currency: str | None):
        self.tenant_id = tenant_id
        self.package_id = package_id
        self.features = features
        self.limits = limits
        self.monthly_price = monthly_price
        self.annual_price = annual_price
        self.currency = currency


async def effective_entitlements(db: AsyncSession, tenant_id: uuid.UUID) -> EffectiveEntitlements:
    subscription = await db.scalar(select(CompanySubscription).where(CompanySubscription.tenant_id == tenant_id,
                                                                       CompanySubscription.status == "active"))
    features = {key: True for key in MANDATORY_FEATURES}
    limits: dict[str, int] = {}
    monthly = annual = None
    currency = None
    package_id = subscription.package_id if subscription else None
    if subscription:
        rows = await db.scalars(select(PackageFeature).where(PackageFeature.package_id == subscription.package_id))
        features.update({row.feature_key: row.enabled for row in rows})
        rows = await db.scalars(select(PackageLimit).where(PackageLimit.package_id == subscription.package_id))
        limits.update({row.limit_key: row.limit_value for row in rows})
        monthly, annual, currency = subscription.agreed_monthly_price, subscription.agreed_annual_price, subscription.currency
    now = datetime.now(UTC)
    overrides = await db.scalars(select(CompanyCommercialOverride).where(
        CompanyCommercialOverride.tenant_id == tenant_id,
        CompanyCommercialOverride.effective_from <= now,
        (CompanyCommercialOverride.effective_to.is_(None) | (CompanyCommercialOverride.effective_to > now)),
    ).order_by(CompanyCommercialOverride.created_at.asc()))
    for override in overrides:
        if override.kind == "feature" and override.key not in MANDATORY_FEATURES and override.bool_value is not None:
            features[override.key] = override.bool_value
        elif override.kind == "limit" and override.int_value is not None:
            limits[override.key] = override.int_value
        elif override.kind == "price" and override.decimal_value is not None:
            if override.key == "monthly_price": monthly = override.decimal_value
            if override.key == "annual_price": annual = override.decimal_value
            if override.currency: currency = override.currency
    for key in MANDATORY_FEATURES:
        features[key] = True
    return EffectiveEntitlements(tenant_id, package_id, features, limits, monthly, annual, currency)


async def require_feature(db: AsyncSession, tenant_id: uuid.UUID, feature_key: str) -> None:
    entitlements = await effective_entitlements(db, tenant_id)
    if not entitlements.features.get(feature_key, False):
        raise HTTPException(status_code=403, detail=f"Feature '{feature_key}' is not enabled for this company")


async def require_limit(db: AsyncSession, tenant_id: uuid.UUID, limit_key: str, current_value: int) -> None:
    entitlements = await effective_entitlements(db, tenant_id)
    limit = entitlements.limits.get(limit_key)
    if limit is not None and current_value >= limit:
        raise HTTPException(status_code=403, detail=f"Limit '{limit_key}' exceeded")
