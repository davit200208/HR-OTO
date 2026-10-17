import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AuditLog


async def write_audit(db: AsyncSession, actor_user_id: uuid.UUID | None, action: str,
                      target_type: str, target_id: str | None = None, details: dict | None = None) -> None:
    db.add(AuditLog(actor_user_id=actor_user_id, action=action, target_type=target_type,
                    target_id=target_id, details=json.dumps(details or {}, ensure_ascii=False)))
