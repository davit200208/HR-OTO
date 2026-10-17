"""owner dashboard, licensing and audit fields"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_owner_operations"
down_revision: Union[str, None] = "0002_multitenant_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("license_status", sa.String(24), nullable=False, server_default="trial"))
    op.add_column("tenants", sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tenants", sa.Column("license_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tenants", sa.Column("monthly_revenue", sa.Integer(), nullable=False, server_default="0"))
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(80), nullable=False),
        sa.Column("target_id", sa.String(120), nullable=True),
        sa.Column("details", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name=op.f("fk_audit_logs_actor_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_column("tenants", "monthly_revenue")
    op.drop_column("tenants", "license_expires_at")
    op.drop_column("tenants", "trial_ends_at")
    op.drop_column("tenants", "license_status")
