"""company admin HR foundation"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "tenant_0002_admin_core"
down_revision: Union[str, None] = "tenant_0001_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    u = sa.Uuid(as_uuid=True)
    op.create_table("departments", sa.Column("id", u, primary_key=True), sa.Column("name", sa.String(120), unique=True, nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("positions", sa.Column("id", u, primary_key=True), sa.Column("name", sa.String(120), unique=True, nullable=False), sa.Column("department_id", u, sa.ForeignKey("departments.id", ondelete="SET NULL")), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("branches", sa.Column("id", u, primary_key=True), sa.Column("name", sa.String(120), unique=True, nullable=False), sa.Column("address", sa.String(255), nullable=False, server_default=""), sa.Column("manager_user_id", u), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("employees", sa.Column("id", u, primary_key=True), sa.Column("employee_id", sa.String(48), unique=True, nullable=False), sa.Column("user_id", u, unique=True), sa.Column("first_name", sa.String(80), nullable=False), sa.Column("last_name", sa.String(80), nullable=False), sa.Column("email", sa.String(254), nullable=False, server_default=""), sa.Column("phone", sa.String(40), nullable=False, server_default=""), sa.Column("personal_id", sa.String(64), nullable=False, server_default=""), sa.Column("birth_date", sa.Date()), sa.Column("department_id", u, sa.ForeignKey("departments.id", ondelete="SET NULL")), sa.Column("position_id", u, sa.ForeignKey("positions.id", ondelete="SET NULL")), sa.Column("branch_id", u, sa.ForeignKey("branches.id", ondelete="SET NULL")), sa.Column("employment_date", sa.Date()), sa.Column("employment_status", sa.String(32), nullable=False, server_default="active"), sa.Column("salary_amount", sa.Integer()), sa.Column("bonus_amount", sa.Integer()), sa.Column("salary_currency", sa.String(3), nullable=False, server_default="GEL"), sa.Column("photo_data", sa.LargeBinary()), sa.Column("photo_content_type", sa.String(80), nullable=False, server_default=""), sa.Column("archived_at", sa.String(40), nullable=False, server_default=""), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_employees_employee_id", "employees", ["employee_id"])
    op.create_index("ix_employees_employment_status", "employees", ["employment_status"])
    op.create_table("employee_documents", sa.Column("id", u, primary_key=True), sa.Column("employee_id", u, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(160), nullable=False), sa.Column("content_type", sa.String(80), nullable=False), sa.Column("content", sa.LargeBinary(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_employee_documents_employee_id", "employee_documents", ["employee_id"])
    op.create_table("tenant_settings", sa.Column("key", sa.String(100), primary_key=True), sa.Column("value", sa.Text(), nullable=False, server_default=""))

def downgrade() -> None:
    for table in ("tenant_settings", "employee_documents", "employees", "branches", "positions", "departments"):
        op.drop_table(table)
