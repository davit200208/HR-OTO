import uuid

import pytest
from fastapi import HTTPException

from app.api.dependencies import PERMISSIONS
from app.core.tenant_security import enforce_tenant_access
from app.models.identity import UserRole


def test_tenant_a_cannot_access_tenant_b() -> None:
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    with pytest.raises(HTTPException) as error:
        enforce_tenant_access(tenant_a, tenant_b)
    assert error.value.status_code == 403


def test_same_tenant_is_allowed() -> None:
    tenant = uuid.uuid4()
    enforce_tenant_access(tenant, tenant)


def test_role_permissions_are_explicit() -> None:
    assert "company:create" in PERMISSIONS[UserRole.OWNER]
    assert "company:create" not in PERMISSIONS[UserRole.EMPLOYEE]
    assert "tenant:write" in PERMISSIONS[UserRole.HR_ADMIN]
    assert "tenant:write" not in PERMISSIONS[UserRole.EMPLOYEE]
