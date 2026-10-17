"""employee mobile schedules, self-service and communications"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "tenant_0003_employee_mobile"
down_revision: Union[str, None] = "tenant_0002_admin_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    u = sa.Uuid(as_uuid=True); dt = sa.DateTime(timezone=True)
    op.create_table("work_schedules", sa.Column("id", u, primary_key=True), sa.Column("employee_id", u, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False), sa.Column("work_date", sa.Date(), nullable=False), sa.Column("start_time", sa.Time()), sa.Column("end_time", sa.Time()), sa.Column("break_minutes", sa.Integer(), nullable=False, server_default="0"), sa.Column("status", sa.String(24), nullable=False, server_default="scheduled"))
    op.create_index("ix_work_schedules_employee_id", "work_schedules", ["employee_id"]); op.create_index("ix_work_schedules_work_date", "work_schedules", ["work_date"])
    op.create_table("attendance_records", sa.Column("id", u, primary_key=True), sa.Column("employee_id", u, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False), sa.Column("work_date", sa.Date(), nullable=False), sa.Column("worked_minutes", sa.Integer(), nullable=False, server_default="0"), sa.Column("status", sa.String(24), nullable=False, server_default="unverified"), sa.Column("verification_method", sa.String(48), nullable=False, server_default="pending"), sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_attendance_records_employee_id", "attendance_records", ["employee_id"]); op.create_index("ix_attendance_records_work_date", "attendance_records", ["work_date"])
    op.create_table("break_records", sa.Column("id", u, primary_key=True), sa.Column("employee_id", u, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False), sa.Column("break_date", sa.Date(), nullable=False), sa.Column("started_at", dt), sa.Column("ended_at", dt), sa.Column("minutes", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_break_records_employee_id", "break_records", ["employee_id"])
    op.create_table("leave_balances", sa.Column("id", u, primary_key=True), sa.Column("employee_id", u, sa.ForeignKey("employees.id", ondelete="CASCADE"), unique=True, nullable=False), sa.Column("annual_days", sa.Integer(), nullable=False, server_default="0"), sa.Column("used_days", sa.Integer(), nullable=False, server_default="0"))
    op.create_table("leave_requests", sa.Column("id", u, primary_key=True), sa.Column("employee_id", u, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False), sa.Column("starts_on", sa.Date(), nullable=False), sa.Column("ends_on", sa.Date(), nullable=False), sa.Column("reason", sa.Text(), nullable=False, server_default=""), sa.Column("status", sa.String(24), nullable=False, server_default="pending"), sa.Column("created_at", dt, server_default=sa.func.now(), nullable=False), sa.Column("updated_at", dt, server_default=sa.func.now(), nullable=False))
    op.create_index("ix_leave_requests_employee_id", "leave_requests", ["employee_id"])
    op.create_table("announcements", sa.Column("id", u, primary_key=True), sa.Column("title", sa.String(200), nullable=False), sa.Column("body", sa.Text(), nullable=False), sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", dt, server_default=sa.func.now(), nullable=False), sa.Column("updated_at", dt, server_default=sa.func.now(), nullable=False))
    op.create_table("in_app_notifications", sa.Column("id", u, primary_key=True), sa.Column("employee_id", u, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(200), nullable=False), sa.Column("body", sa.Text(), nullable=False), sa.Column("read_at", dt))
    op.create_index("ix_in_app_notifications_employee_id", "in_app_notifications", ["employee_id"])
    op.create_table("surveys", sa.Column("id", u, primary_key=True), sa.Column("title", sa.String(200), nullable=False), sa.Column("question", sa.Text(), nullable=False), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", dt, server_default=sa.func.now(), nullable=False), sa.Column("updated_at", dt, server_default=sa.func.now(), nullable=False))
    op.create_table("survey_responses", sa.Column("id", u, primary_key=True), sa.Column("survey_id", u, sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False), sa.Column("employee_id", u, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False), sa.Column("answer", sa.Text(), nullable=False), sa.Column("created_at", dt, server_default=sa.func.now(), nullable=False))

def downgrade() -> None:
    for table in ("survey_responses", "surveys", "in_app_notifications", "announcements", "leave_requests", "leave_balances", "break_records", "attendance_records", "work_schedules"):
        op.drop_table(table)
