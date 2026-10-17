import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.models.commercial import CompanySubscription, PackageFeature, PackageLimit
from app.services.entitlements import require_feature, require_limit


class Result:
    def __init__(self, values): self.values = values
    def __iter__(self): return iter(self.values)


def test_disabled_feature_is_rejected_server_side() -> None:
    async def run() -> None:
        tenant_id, package_id = uuid.uuid4(), uuid.uuid4()
        subscription = CompanySubscription(tenant_id=tenant_id, package_id=package_id, currency="GEL", agreed_monthly_price=0, agreed_annual_price=0, status="active")
        db = AsyncMock(); db.scalar = AsyncMock(return_value=subscription); db.scalars = AsyncMock(side_effect=[Result([PackageFeature(package_id=package_id, feature_key="payroll", enabled=False)]), Result([]), Result([])])
        with pytest.raises(HTTPException) as error: await require_feature(db, tenant_id, "payroll")
        assert error.value.status_code == 403
    asyncio.run(run())


def test_reduced_limit_blocks_new_operation_without_deleting_data() -> None:
    async def run() -> None:
        tenant_id, package_id = uuid.uuid4(), uuid.uuid4()
        subscription = CompanySubscription(tenant_id=tenant_id, package_id=package_id, currency="GEL", agreed_monthly_price=0, agreed_annual_price=0, status="active")
        db = AsyncMock(); db.scalar = AsyncMock(return_value=subscription); db.scalars = AsyncMock(side_effect=[Result([]), Result([PackageLimit(package_id=package_id, limit_key="employees", limit_value=2)]), Result([])])
        with pytest.raises(HTTPException): await require_limit(db, tenant_id, "employees", 2)
    asyncio.run(run())
