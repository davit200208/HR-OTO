from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthContext, get_auth_context
from app.core.config import get_settings
from app.core.security import decode_token, hash_password, new_mfa_secret, verify_mfa
from app.db.session import get_db
from app.models.identity import User, UserRole
from app.schemas.auth import (BootstrapOwnerRequest, LoginRequest, MfaVerifyRequest,
                              PasswordResetConfirm, PasswordResetRequest, RefreshRequest,
                              TokenResponse, UserResponse)
from app.services.auth_service import AuthenticationService

router = APIRouter(prefix="/auth", tags=["authentication"])
service = AuthenticationService()


@router.post("/bootstrap-owner", response_model=UserResponse, status_code=201)
async def bootstrap_owner(payload: BootstrapOwnerRequest, db: AsyncSession = Depends(get_db)):
    if payload.bootstrap_token != get_settings().bootstrap_token:
        raise HTTPException(status_code=403, detail="Invalid bootstrap token")
    if await db.scalar(select(User).where(User.role == UserRole.OWNER)):
        raise HTTPException(status_code=409, detail="Owner already exists")
    user = User(email=payload.email.lower(), full_name=payload.full_name,
                password_hash=hash_password(payload.password), role=UserRole.OWNER)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        _, access, refresh, expires_at = await service.login(db, payload.email, payload.password, payload.mfa_code)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid credentials or MFA code") from exc
    return TokenResponse(access_token=access, refresh_token=refresh, expires_at=expires_at)


@router.post("/logout", status_code=204)
async def logout(context: AuthContext = Depends(get_auth_context), db: AsyncSession = Depends(get_db)):
    await service.logout(db, context.session)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        refresh_payload = decode_token(payload.refresh_token, expected_type="refresh")
        access, expires_at = await service.refresh(db, refresh_payload, payload.refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
    return TokenResponse(access_token=access, refresh_token=payload.refresh_token, expires_at=expires_at)


@router.get("/me", response_model=UserResponse)
async def me(context: AuthContext = Depends(get_auth_context)):
    return context.user


@router.post("/password-reset/request")
async def password_reset_request(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    await service.request_password_reset(db, payload.email)
    return {"accepted": True, "message": "If the account exists, reset instructions will be delivered."}


@router.post("/password-reset/confirm")
async def password_reset_confirm(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    try:
        await service.reset_password(db, payload.token, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token") from exc
    return {"reset": True}


@router.post("/mfa/enroll")
async def mfa_enroll(context: AuthContext = Depends(get_auth_context), db: AsyncSession = Depends(get_db)):
    secret = new_mfa_secret()
    context.user.mfa_secret = secret
    context.user.mfa_enabled = False
    await db.commit()
    uri = f"otpauth://totp/{get_settings().mfa_issuer}:{context.user.email}?secret={secret}&issuer={get_settings().mfa_issuer}"
    return {"secret": secret, "otpauth_uri": uri, "confirmed": False}


@router.post("/mfa/verify")
async def mfa_verify(payload: MfaVerifyRequest, context: AuthContext = Depends(get_auth_context), db: AsyncSession = Depends(get_db)):
    if not context.user.mfa_secret or not verify_mfa(context.user.mfa_secret, payload.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    context.user.mfa_enabled = True
    await db.commit()
    return {"enabled": True}
