import uuid

from fastapi import HTTPException


def enforce_tenant_access(authenticated_tenant_id: uuid.UUID | None, requested_tenant_id: uuid.UUID | None) -> None:
    """Tenant identity is taken from the authenticated user, never from the URL."""
    if not authenticated_tenant_id or not requested_tenant_id or authenticated_tenant_id != requested_tenant_id:
        raise HTTPException(status_code=403, detail="Tenant isolation violation")
