import uuid
import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.models.commercial import CompanyCommercialOverride, CompanySubscription, PackageFeature, PackageLimit
from app.services.entitlements import MANDATORY_FEATURES, effective_entitlements


class Result:
    def __init__(self, values):
        self.values = values

    def __iter__(self):
        return iter(self.values)


def test_effective_entitlements_apply_package_and_override() -> None:
    asyncio.run(_test_effective_entitlements_apply_package_and_override())


async def _test_effective_entitlements_apply_package_and_override() -> None:
    tenant_id = uuid.uuid4()
    package_id = uuid.uuid4()
    subscription = CompanySubscription(tenant_id=tenant_id, package_id=package_id, currency="GEL",
                                       agreed_monthly_price=Decimal("89"), agreed_annual_price=Decimal("1068"),
                                       starts_at=datetime.now(UTC), status="active")
    feature = PackageFeature(package_id=package_id, feature_key="payroll", enabled=False)
    limit = PackageLimit(package_id=package_id, limit_key="employees", limit_value=50)
    override = CompanyCommercialOverride(tenant_id=tenant_id, kind="feature", key="payroll", bool_value=True,
                                         effective_from=datetime(2020, 1, 1, tzinfo=UTC), reason="contract")
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=subscription)
    db.scalars = AsyncMock(side_effect=[Result([feature]), Result([limit]), Result([override])])
    result = await effective_entitlements(db, tenant_id)
    assert result.features["payroll"] is True
    assert result.limits["employees"] == 50
    assert result.monthly_price == Decimal("89")


def test_mandatory_security_features_are_always_declared() -> None:
    assert {"security.authentication", "security.tenant_isolation", "security.audit"} == MANDATORY_FEATURES
