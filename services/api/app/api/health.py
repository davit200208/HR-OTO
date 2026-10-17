from fastapi import APIRouter
from sqlalchemy import text

from app.db.redis_client import redis_client
from app.db.session import SessionLocal

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok", "service": "hr-oto-server"}


@router.get("/ready")
async def ready() -> dict[str, str | bool]:
    checks: dict[str, str | bool] = {"database": False, "redis": False}
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    try:
        checks["redis"] = bool(await redis_client.ping())
    except Exception:
        pass
    checks["status"] = "ok" if all(checks.values()) else "degraded"
    return checks

