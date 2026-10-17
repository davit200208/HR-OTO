import re
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.models.tenant import TenantRecord
from app.models.admin import Branch, Department, Employee, EmployeeDocument, Position, TenantSetting
from app.models.employee_mobile import (Announcement, AttendanceRecord, BreakRecord, InAppNotification, LeaveBalance,
                                         DeviceRegistration, LeaveRequest, ScheduleChange, ShiftSwapRequest, ShiftTemplate, Survey, SurveyResponse, SyncEvent, WorkSchedule)
from app.models.payroll import DocumentVersion, LeaveComment, LeavePolicy, PayrollEntry, PayrollPeriod, PayrollRule
from app.models.advanced_hr import Candidate, DisciplinaryCase, KpiGoal, PerformanceReview, RecruitmentJob, TrainingCourse, TrainingEnrollment


def tenant_database_name(company_code: str) -> str:
    safe = re.sub(r"[^a-z0-9]+", "_", company_code.lower()).strip("_")
    return f"hr_oto_tenant_{safe}_{uuid.uuid4().hex[:8]}"


def tenant_url(database_name: str) -> str:
    base = get_settings().database_url
    return str(make_url(base).set(database=database_name))


class TenantProvisioningService:
    async def create_database(self, database_name: str) -> None:
        settings = get_settings()
        admin_url = settings.database_admin_url or str(make_url(settings.database_url).set(database="postgres"))
        engine: AsyncEngine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
        try:
            async with engine.connect() as connection:
                exists = await connection.scalar(
                    text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": database_name}
                )
                if not exists:
                    quoted = '"' + database_name.replace('"', '""') + '"'
                    await connection.execute(text(f"CREATE DATABASE {quoted}"))
        finally:
            await engine.dispose()

    async def migrate_database(self, database_name: str) -> None:
        engine = create_async_engine(tenant_url(database_name))
        try:
            async with engine.begin() as connection:
                def create_tenant_tables(sync):
                    for table in (TenantRecord.__table__, Department.__table__, Position.__table__, Branch.__table__, Employee.__table__, EmployeeDocument.__table__, TenantSetting.__table__, WorkSchedule.__table__, ShiftTemplate.__table__, ScheduleChange.__table__, ShiftSwapRequest.__table__, AttendanceRecord.__table__, BreakRecord.__table__, LeaveBalance.__table__, LeaveRequest.__table__, Announcement.__table__, InAppNotification.__table__, Survey.__table__, SurveyResponse.__table__, DeviceRegistration.__table__, SyncEvent.__table__, LeavePolicy.__table__, LeaveComment.__table__, PayrollRule.__table__, PayrollPeriod.__table__, PayrollEntry.__table__, DocumentVersion.__table__, KpiGoal.__table__, PerformanceReview.__table__, DisciplinaryCase.__table__, RecruitmentJob.__table__, Candidate.__table__, TrainingCourse.__table__, TrainingEnrollment.__table__):
                        table.create(sync, checkfirst=True)
                await connection.run_sync(create_tenant_tables)
        finally:
            await engine.dispose()

    async def provision(self, company_code: str) -> str:
        name = tenant_database_name(company_code)
        await self.create_database(name)
        await self.migrate_database(name)
        return name
