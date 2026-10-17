import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.identity import LicenseStatus, TenantStatus


class CompanyCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    company_code: str = Field(min_length=3, max_length=32, pattern=r"^[A-Z0-9][A-Z0-9_-]+$")
    subdomain: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]+$")
    owner_email: str
    owner_name: str = Field(min_length=2, max_length=160)
    owner_password: str = Field(min_length=12)
    license_status: LicenseStatus = LicenseStatus.TRIAL
    monthly_revenue: int = Field(default=0, ge=0)


class CompanyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    company_code: str
    subdomain: str
    database_name: str
    status: TenantStatus
    license_status: LicenseStatus
    trial_ends_at: datetime | None
    license_expires_at: datetime | None
    monthly_revenue: int


class CompanyUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    subdomain: str | None = Field(default=None, min_length=3, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]+$")
    status: TenantStatus | None = None
    license_status: LicenseStatus | None = None
    monthly_revenue: int | None = Field(default=None, ge=0)


class CompanyOwnerCreateRequest(BaseModel):
    email: str
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=12)


class DashboardResponse(BaseModel):
    total_companies: int
    active_companies: int
    blocked_companies: int
    trial_companies: int
    active_licenses: int
    expired_licenses: int
    monthly_revenue: int


class AuditLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    action: str
    target_type: str
    target_id: str | None
    details: str


class TenantRecordResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    record_key: str
    payload: dict
