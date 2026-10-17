import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_token, hash_password, hash_token, verify_mfa, verify_password
from app.models.identity import PasswordResetToken, User, UserRole, UserSession


class AuthenticationService:
    async def login(self, db: AsyncSession, email: str, password: str, mfa_code: str | None = None):
        user = await db.scalar(select(User).where(User.email == email.lower()))
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            raise ValueError("invalid credentials")
        if user.mfa_enabled and (not mfa_code or not user.mfa_secret or not verify_mfa(user.mfa_secret, mfa_code)):
            raise ValueError("mfa required or invalid")
        now = datetime.now(UTC)
        session = UserSession(user_id=user.id, token_hash="pending",
                              expires_at=now + timedelta(days=get_settings().refresh_token_days))
        db.add(session)
        await db.flush()
        refresh = create_token(user.id, session.id, "refresh", timedelta(days=get_settings().refresh_token_days))
        session.token_hash = hash_token(refresh)
        access = create_token(user.id, session.id, "access", timedelta(minutes=get_settings().access_token_minutes))
        await db.commit()
        return user, access, refresh, now + timedelta(minutes=get_settings().access_token_minutes)

    async def logout(self, db: AsyncSession, session: UserSession) -> None:
        session.revoked_at = datetime.now(UTC)
        await db.commit()

    async def refresh(self, db: AsyncSession, refresh_payload: dict, raw_token: str):
        session = await db.scalar(select(UserSession).where(UserSession.id == refresh_payload["sid"]))
        user = await db.scalar(select(User).where(User.id == refresh_payload["sub"]))
        now = datetime.now(UTC)
        if (not session or not user or session.revoked_at or session.expires_at <= now or not user.is_active
                or session.token_hash != hash_token(raw_token)):
            raise ValueError("invalid refresh session")
        access = create_token(user.id, session.id, "access", timedelta(minutes=get_settings().access_token_minutes))
        return access, now + timedelta(minutes=get_settings().access_token_minutes)

    async def request_password_reset(self, db: AsyncSession, email: str) -> str | None:
        user = await db.scalar(select(User).where(User.email == email.lower()))
        if not user:
            return None
        raw = secrets.token_urlsafe(32)
        token = PasswordResetToken(user_id=user.id, token_hash=hash_token(raw),
                                   expires_at=datetime.now(UTC) + timedelta(minutes=get_settings().password_reset_minutes))
        db.add(token)
        await db.commit()
        return raw

    async def reset_password(self, db: AsyncSession, raw_token: str, new_password: str) -> None:
        token = await db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(raw_token)))
        if not token or token.used_at or token.expires_at <= datetime.now(UTC):
            raise ValueError("invalid reset token")
        user = await db.scalar(select(User).where(User.id == token.user_id))
        if not user:
            raise ValueError("invalid reset token")
        user.password_hash = hash_password(new_password)
        token.used_at = datetime.now(UTC)
        await db.commit()
