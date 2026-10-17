import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis_client import redis_client
from app.models.integrations import NotificationMessage, NotificationQuota


async def enqueue_notification(db: AsyncSession, *, tenant_id: uuid.UUID | None, provider: str, channel: str,
                               recipient: str, idempotency_key: str, template_key: str = "") -> NotificationMessage:
    existing = await db.scalar(select(NotificationMessage).where(NotificationMessage.idempotency_key == idempotency_key))
    if existing:
        return existing
    quota = await db.scalar(select(NotificationQuota).where(NotificationQuota.tenant_id == tenant_id, NotificationQuota.channel == channel))
    if quota:
        now = datetime.now(UTC)
        day_count = await db.scalar(select(func.count(NotificationMessage.id)).where(NotificationMessage.tenant_id == tenant_id, NotificationMessage.channel == channel, NotificationMessage.created_at >= now - timedelta(days=1)))
        month_count = await db.scalar(select(func.count(NotificationMessage.id)).where(NotificationMessage.tenant_id == tenant_id, NotificationMessage.channel == channel, NotificationMessage.created_at >= now - timedelta(days=31)))
        if quota.daily_limit and day_count >= quota.daily_limit: raise HTTPException(429, "Daily notification quota exceeded")
        if quota.monthly_limit and month_count >= quota.monthly_limit: raise HTTPException(429, "Monthly notification quota exceeded")
    message = NotificationMessage(tenant_id=tenant_id, provider=provider, channel=channel, recipient=recipient, idempotency_key=idempotency_key, template_key=template_key)
    db.add(message); await db.flush()
    try: await redis_client.rpush("hr_oto:notifications", str(message.id))
    except Exception: pass  # delivery worker can retry after Redis becomes available
    return message
