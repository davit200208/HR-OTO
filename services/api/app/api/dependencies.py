import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.identity import User, UserRole, UserSession

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: UserSession


PERMISSIONS: dict[UserRole, frozenset[str]] = {
    UserRole.OWNER: frozenset({"company:create", "company:read", "system:manage"}),
    UserRole.COMPANY_OWNER: frozenset({"tenant:read", "tenant:write", "user:manage"}),
    UserRole.HR_ADMIN: frozenset({"tenant:read", "tenant:write", "user:manage"}),
    UserRole.MANAGER: frozenset({"tenant:read", "tenant:write"}),
    UserRole.EMPLOYEE: frozenset({"tenant:read"}),
}


async def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
        session_id = uuid.UUID(payload["sid"])
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired access token") from exc
    session = await db.scalar(select(UserSession).where(UserSession.id == session_id))
    user = await db.scalar(select(User).where(User.id == user_id))
    from datetime import UTC, datetime
    if not session or not user or session.revoked_at or session.expires_at <= datetime.now(UTC) or not user.is_active:
        raise HTTPException(status_code=401, detail="Session is invalid or revoked")
    return AuthContext(user=user, session=session)


def require_roles(*roles: UserRole):
    async def dependency(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if context.user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return context

    return dependency


def require_permission(permission: str):
    async def dependency(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if permission not in PERMISSIONS.get(context.user.role, frozenset()):
            raise HTTPException(status_code=403, detail="Permission denied")
        return context

    return dependency


def require_tenant(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if context.user.tenant_id is None or context.user.role == UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Tenant context required")
    return context
