"""device registration and idempotent sync event ledger"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "tenant_0005_offline_sync"
down_revision: Union[str, None] = "tenant_0004_attendance_scheduling"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    u = sa.Uuid(as_uuid=True); dt = sa.DateTime(timezone=True)
    op.create_table("device_registrations", sa.Column("id", u, primary_key=True), sa.Column("user_id", u, nullable=False), sa.Column("device_id", sa.String(160), unique=True, nullable=False), sa.Column("platform", sa.String(24), nullable=False), sa.Column("last_seen_at", dt, server_default=sa.func.now(), nullable=False), sa.Column("last_server_version", sa.Integer(), nullable=False, server_default="0"), sa.Column("clock_skew_seconds", sa.Integer(), nullable=False, server_default="0"), sa.Column("created_at", dt, server_default=sa.func.now(), nullable=False), sa.Column("updated_at", dt, server_default=sa.func.now(), nullable=False))
    op.create_index("ix_device_registrations_user_id", "device_registrations", ["user_id"])
    op.create_table("sync_events", sa.Column("id", u, primary_key=True), sa.Column("event_id", u, unique=True, nullable=False), sa.Column("idempotency_key", sa.String(160), unique=True, nullable=False), sa.Column("user_id", u, nullable=False), sa.Column("entity", sa.String(100), nullable=False), sa.Column("payload", sa.Text(), nullable=False), sa.Column("server_version", sa.Integer(), nullable=False, server_default="0"), sa.Column("status", sa.String(24), nullable=False, server_default="accepted"), sa.Column("created_at", dt, server_default=sa.func.now(), nullable=False))
    op.create_index("ix_sync_events_event_id", "sync_events", ["event_id"]); op.create_index("ix_sync_events_idempotency_key", "sync_events", ["idempotency_key"]); op.create_index("ix_sync_events_user_id", "sync_events", ["user_id"])

def downgrade() -> None:
    op.drop_table("sync_events"); op.drop_table("device_registrations")
