import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PackageCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=48, pattern=r"^[A-Z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    description: str = ""
    monthly_price: Decimal = Field(ge=0)
    annual_price: Decimal = Field(ge=0)
    currency: str = Field(default="GEL", min_length=3, max_length=3)
    discount_percent: Decimal = Field(default=0, ge=0, le=100)
    features: dict[str, bool] = Field(default_factory=dict)
    limits: dict[str, int] = Field(default_factory=dict)


class PackageUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    is_active: bool | None = None
    archive: bool | None = None


class PriceVersionRequest(BaseModel):
    monthly_price: Decimal = Field(ge=0)
    annual_price: Decimal = Field(ge=0)
    currency: str = Field(default="GEL", min_length=3, max_length=3)
    discount_percent: Decimal = Field(default=0, ge=0, le=100)
    effective_from: datetime


class FeatureUpdateRequest(BaseModel):
    enabled: bool


class LimitUpdateRequest(BaseModel):
    value: int = Field(ge=0)


class PackageResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    code: str
    name: str
    description: str
    is_active: bool
    is_archived: bool


class PackageDetailsResponse(PackageResponse):
    monthly_price: Decimal | None
    annual_price: Decimal | None
    currency: str | None
    discount_percent: Decimal | None
    features: dict[str, bool]
    limits: dict[str, int]


class OverrideRequest(BaseModel):
    kind: str = Field(pattern=r"^(feature|limit|price)$")
    key: str = Field(min_length=2, max_length=80)
    bool_value: bool | None = None
    int_value: int | None = Field(default=None, ge=0)
    decimal_value: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    effective_from: datetime
    effective_to: datetime | None = None
    reason: str = ""


class TrialGrantRequest(BaseModel):
    ends_at: datetime
    reason: str = ""


class SubscriptionAssignRequest(BaseModel):
    package_id: uuid.UUID
    agreed_monthly_price: Decimal = Field(ge=0)
    agreed_annual_price: Decimal = Field(ge=0)
    currency: str = Field(default="GEL", min_length=3, max_length=3)
    starts_at: datetime


class EffectiveEntitlementsResponse(BaseModel):
    tenant_id: uuid.UUID
    package_id: uuid.UUID | None
    features: dict[str, bool]
    limits: dict[str, int]
    monthly_price: Decimal | None
    annual_price: Decimal | None
    currency: str | None
