import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ProviderIntegration(Base, TimestampMixin):
    __tablename__ = "provider_integrations"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    base_url: Mapped[str] = mapped_column(String(255), default="")
    sender_name: Mapped[str] = mapped_column(String(160), default="")
    sender_email: Mapped[str] = mapped_column(String(255), default="")
    reply_to_email: Mapped[str] = mapped_column(String(255), default="")
    sender_id: Mapped[str] = mapped_column(String(80), default="")
    default_country_code: Mapped[str] = mapped_column(String(8), default="+995")
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=10)
    retry_max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    secret_ref: Mapped[str] = mapped_column(String(255), default="")
    secret_version: Mapped[int] = mapped_column(Integer, default=0)
    secret_last4: Mapped[str] = mapped_column(String(4), default="")
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_status: Mapped[str] = mapped_column(String(24), default="never")
    last_error: Mapped[str] = mapped_column(Text, default="")


class NotificationTemplate(Base, TimestampMixin):
    __tablename__ = "notification_templates"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    template_key: Mapped[str] = mapped_column(String(100), index=True)
    provider_template_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subject: Mapped[str] = mapped_column(String(255), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class NotificationQuota(Base, TimestampMixin):
    __tablename__ = "notification_quotas"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(16), index=True)
    daily_limit: Mapped[int] = mapped_column(Integer, default=0)
    monthly_limit: Mapped[int] = mapped_column(Integer, default=0)


class NotificationMessage(Base):
    __tablename__ = "notification_messages"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    channel: Mapped[str] = mapped_column(String(16), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    recipient: Mapped[str] = mapped_column(String(255))
    template_key: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(24), default="queued", index=True)
    provider_message_id: Mapped[str] = mapped_column(String(255), default="")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationEvent(Base):
    __tablename__ = "notification_events"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("notification_messages.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
