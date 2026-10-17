import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.identity import UserRole


class BootstrapOwnerRequest(BaseModel):
    bootstrap_token: str
    email: str
    password: str = Field(min_length=12)
    full_name: str = Field(min_length=2, max_length=160)


class LoginRequest(BaseModel):
    email: str
    password: str
    mfa_code: str | None = Field(default=None, min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    tenant_id: uuid.UUID | None
    email: str
    full_name: str
    role: UserRole
    mfa_enabled: bool


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=12)


class MfaVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)
