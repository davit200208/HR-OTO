"""tenant database core table"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "tenant_0001_core"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenant_records",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("record_key", sa.String(120), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tenant_records")),
    )
    op.create_index(op.f("ix_tenant_records_record_key"), "tenant_records", ["record_key"], unique=False)


def downgrade() -> None:
    op.drop_table("tenant_records")
