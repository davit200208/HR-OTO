import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthContext, require_permission
from app.db.session import get_db
from app.integrations.providers import BrevoEmailAdapter, SmsOfflineMockAdapter
from app.models.integrations import NotificationMessage, NotificationQuota, NotificationTemplate, ProviderIntegration
from app.services.audit import write_audit
from app.services.secrets import SecretStoreUnavailable, get_secret_store, mask_secret

router = APIRouter(prefix="/owner/integrations", tags=["owner-integrations"])

class ProviderUpdate(BaseModel):
    enabled: bool | None = None
    base_url: str | None = None
    sender_name: str | None = None
    sender_email: str | None = None
    reply_to_email: str | None = None
    sender_id: str | None = None
    default_country_code: str | None = None
    timeout_seconds: int = Field(default=10, ge=1, le=120)
    retry_max_attempts: int = Field(default=3, ge=0, le=10)

class SecretReplace(BaseModel):
    api_key: str = Field(min_length=8)
    confirmation: Literal["CONFIRM"]

class TestRequest(BaseModel):
    confirmation: Literal["CONFIRM"] = "CONFIRM"

class TestMessage(BaseModel):
    recipient: str
    subject: str = "HR-OTO test message"
    body: str = "HR-OTO provider test"
    confirmation: Literal["CONFIRM"]

class QuotaUpdate(BaseModel):
    tenant_id: uuid.UUID | None = None
    channel: Literal["sms", "email"]
    daily_limit: int = Field(ge=0)
    monthly_limit: int = Field(ge=0)

class TemplateUpsert(BaseModel):
    provider: Literal["brevo", "smsoffline"]
    template_key: str = Field(min_length=2, max_length=100)
    provider_template_id: int | None = None
    subject: str = ""
    body: str = ""
    enabled: bool = True

async def _provider(db: AsyncSession, name: str) -> ProviderIntegration:
    item = await db.scalar(select(ProviderIntegration).where(ProviderIntegration.provider == name))
    if item is None:
        item = ProviderIntegration(provider=name, base_url="https://api.brevo.com/v3" if name == "brevo" else "")
        db.add(item); await db.flush()
    return item

def _require_mfa(context: AuthContext) -> None:
    if not context.user.mfa_enabled:
        raise HTTPException(403, "Owner MFA is required for provider changes")

@router.get("/providers")
async def list_providers(_: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    rows = (await db.scalars(select(ProviderIntegration).order_by(ProviderIntegration.provider))).all()
    return [{"provider": p.provider, "enabled": p.enabled, "base_url": p.base_url, "sender_name": p.sender_name,
             "sender_email": p.sender_email, "reply_to_email": p.reply_to_email, "sender_id": p.sender_id,
             "default_country_code": p.default_country_code, "timeout_seconds": p.timeout_seconds,
             "retry_max_attempts": p.retry_max_attempts, "secret_configured": bool(p.secret_last4),
             "secret_masked": mask_secret(p.secret_last4), "last_test_status": p.last_test_status, "last_error": p.last_error} for p in rows]

@router.patch("/providers/{provider}")
async def update_provider(provider: str, payload: ProviderUpdate, context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    _require_mfa(context); item = await _provider(db, provider)
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(item, key, value)
    await write_audit(db, context.user.id, "integration.provider.updated", "provider", provider, {"enabled": item.enabled})
    await db.commit(); return {"provider": item.provider, "enabled": item.enabled}

@router.post("/providers/{provider}/secret")
async def replace_secret(provider: str, payload: SecretReplace, context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    _require_mfa(context); item = await _provider(db, provider)
    try: get_secret_store().put(provider, payload.api_key, item.secret_version + 1)
    except SecretStoreUnavailable as exc: raise HTTPException(503, str(exc)) from exc
    item.secret_version += 1; item.secret_ref = f"{provider}/api-key/v{item.secret_version}"; item.secret_last4 = payload.api_key[-4:]
    await write_audit(db, context.user.id, "integration.secret.rotated", "provider", provider, {"version": item.secret_version})
    await db.commit(); return {"provider": provider, "secret_masked": mask_secret(item.secret_last4), "version": item.secret_version}

@router.post("/providers/{provider}/test-connection")
async def test_connection(provider: str, _: TestRequest, context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    item = await _provider(db, provider); key = get_secret_store().get(provider)
    if provider == "brevo" and key: result = await BrevoEmailAdapter(key, item.timeout_seconds).test_connection()
    elif provider == "smsoffline": result = await SmsOfflineMockAdapter().test_connection()
    else: result = type("Result", (), {"success": False, "status": "not_configured", "error": "Provider secret is not configured"})()
    item.last_tested_at = datetime.now(UTC); item.last_test_status = result.status; item.last_error = result.error
    await db.commit(); return {"success": result.success, "status": result.status, "error": result.error, "live_verified": result.success}

@router.post("/providers/{provider}/test-message")
async def test_message(provider: str, payload: TestMessage, context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    _require_mfa(context); item = await _provider(db, provider); key = get_secret_store().get(provider)
    if provider != "brevo" or not key: raise HTTPException(503, "Only Brevo test email is live-configurable; SMSOffline remains mock until documented")
    result = await BrevoEmailAdapter(key, item.timeout_seconds).send_email(to=payload.recipient, subject=payload.subject, html_content=payload.body, sender_name=item.sender_name, sender_email=item.sender_email, reply_to=item.reply_to_email, idempotency_key=f"owner-test-{uuid.uuid4()}")
    await db.commit(); return {"success": result.success, "status": result.status, "provider_message_id": result.provider_message_id, "error": result.error, "live_verified": result.success}

@router.put("/quotas")
async def set_quota(payload: QuotaUpdate, context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    _require_mfa(context)
    row = await db.scalar(select(NotificationQuota).where(NotificationQuota.tenant_id == payload.tenant_id, NotificationQuota.channel == payload.channel))
    if not row: row = NotificationQuota(tenant_id=payload.tenant_id, channel=payload.channel); db.add(row)
    row.daily_limit, row.monthly_limit = payload.daily_limit, payload.monthly_limit
    await write_audit(db, context.user.id, "integration.quota.updated", "quota", str(row.id), payload.model_dump(mode="json")); await db.commit()
    return {"id": str(row.id), "tenant_id": payload.tenant_id, "channel": row.channel, "daily_limit": row.daily_limit, "monthly_limit": row.monthly_limit}

@router.get("/templates")
async def list_templates(_: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    rows = (await db.scalars(select(NotificationTemplate).order_by(NotificationTemplate.provider, NotificationTemplate.template_key))).all()
    return [{"id": str(x.id), "provider": x.provider, "template_key": x.template_key, "provider_template_id": x.provider_template_id, "subject": x.subject, "body": x.body, "enabled": x.enabled} for x in rows]

@router.post("/templates")
async def upsert_template(payload: TemplateUpsert, context: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    _require_mfa(context)
    row = await db.scalar(select(NotificationTemplate).where(NotificationTemplate.provider == payload.provider, NotificationTemplate.template_key == payload.template_key))
    if row is None: row = NotificationTemplate(provider=payload.provider, template_key=payload.template_key); db.add(row)
    for key, value in payload.model_dump().items(): setattr(row, key, value)
    await write_audit(db, context.user.id, "integration.template.updated", "notification_template", payload.template_key, {"provider": payload.provider})
    await db.commit(); return {"id": str(row.id), "provider": row.provider, "template_key": row.template_key, "provider_template_id": row.provider_template_id, "enabled": row.enabled}

@router.get("/history")
async def history(limit: int = 100, _: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    rows = (await db.scalars(select(NotificationMessage).order_by(NotificationMessage.created_at.desc()).limit(min(limit, 500)))).all()
    return [{"id": str(m.id), "tenant_id": str(m.tenant_id) if m.tenant_id else None, "provider": m.provider, "channel": m.channel, "recipient": m.recipient, "status": m.status, "attempts": m.attempts, "error": m.error_message, "created_at": m.created_at} for m in rows]
