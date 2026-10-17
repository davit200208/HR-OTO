"""scheduling, shifts, clock state and break controls"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "tenant_0004_attendance_scheduling"
down_revision: Union[str, None] = "tenant_0003_employee_mobile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    u = sa.Uuid(as_uuid=True); dt = sa.DateTime(timezone=True)
    op.add_column("work_schedules", sa.Column("timezone", sa.String(64), nullable=False, server_default="Asia/Tbilisi")); op.add_column("work_schedules", sa.Column("shift_code", sa.String(64), nullable=False, server_default="")); op.add_column("work_schedules", sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table("shift_templates", sa.Column("id", u, primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("start_time", sa.Time(), nullable=False), sa.Column("end_time", sa.Time(), nullable=False), sa.Column("break_minutes", sa.Integer(), nullable=False, server_default="0"), sa.Column("timezone", sa.String(64), nullable=False, server_default="Asia/Tbilisi"), sa.Column("is_overnight", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", dt, server_default=sa.func.now(), nullable=False), sa.Column("updated_at", dt, server_default=sa.func.now(), nullable=False))
    op.create_table("schedule_changes", sa.Column("id", u, primary_key=True), sa.Column("schedule_id", u, sa.ForeignKey("work_schedules.id", ondelete="CASCADE"), nullable=False), sa.Column("actor_user_id", u), sa.Column("action", sa.String(32), nullable=False), sa.Column("reason", sa.Text(), nullable=False, server_default=""), sa.Column("created_at", dt, server_default=sa.func.now(), nullable=False))
    op.create_index("ix_schedule_changes_schedule_id", "schedule_changes", ["schedule_id"])
    op.create_table("shift_swap_requests", sa.Column("id", u, primary_key=True), sa.Column("from_employee_id", u, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False), sa.Column("to_employee_id", u, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False), sa.Column("schedule_id", u, sa.ForeignKey("work_schedules.id", ondelete="CASCADE"), nullable=False), sa.Column("reason", sa.Text(), nullable=False, server_default=""), sa.Column("status", sa.String(24), nullable=False, server_default="pending"), sa.Column("created_at", dt, server_default=sa.func.now(), nullable=False), sa.Column("updated_at", dt, server_default=sa.func.now(), nullable=False))
    op.create_index("ix_shift_swap_requests_from_employee_id", "shift_swap_requests", ["from_employee_id"]); op.create_index("ix_shift_swap_requests_to_employee_id", "shift_swap_requests", ["to_employee_id"])
    for col, typ in (("clock_in_at", dt), ("clock_out_at", dt), ("late_minutes", sa.Integer()), ("early_leave_minutes", sa.Integer()), ("overtime_minutes", sa.Integer()), ("night_minutes", sa.Integer()), ("correction_reason", sa.Text())):
        op.add_column("attendance_records", sa.Column(col, typ, nullable=False if col.endswith("minutes") or col == "correction_reason" else True, server_default="0" if col.endswith("minutes") else "" if col == "correction_reason" else None))
    op.add_column("break_records", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.false()))

def downgrade() -> None:
    op.drop_column("break_records", "active")
    for col in ("correction_reason", "night_minutes", "overtime_minutes", "early_leave_minutes", "late_minutes", "clock_out_at", "clock_in_at"): op.drop_column("attendance_records", col)
    for table in ("shift_swap_requests", "schedule_changes", "shift_templates"): op.drop_table(table)
    for col in ("published", "shift_code", "timezone"): op.drop_column("work_schedules", col)
