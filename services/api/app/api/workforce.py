import uuid
from datetime import UTC, date, datetime, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin import _ctx
from app.api.dependencies import AuthContext, require_tenant
from app.api.employee import _employee
from app.db.session import get_db
from app.models.admin import Employee
from app.models.employee_mobile import (AttendanceRecord, BreakRecord, ScheduleChange, ShiftSwapRequest, ShiftTemplate,
                                        WorkSchedule)
from app.models.identity import UserRole
from app.services.attendance_engine import active_break_count
from app.services.verification import PendingVerificationProvider

router = APIRouter(prefix="/workforce", tags=["attendance-scheduling"])

class ShiftTemplateInput(BaseModel):
    name: str = Field(min_length=2); start_time: time; end_time: time; break_minutes: int = Field(ge=0, le=1440); timezone: str = "Asia/Tbilisi"; is_overnight: bool = False
class ScheduleInput(BaseModel):
    employee_id: uuid.UUID; work_date: date; start_time: time | None = None; end_time: time | None = None; break_minutes: int = Field(ge=0, le=1440); timezone: str = "Asia/Tbilisi"; shift_code: str = ""; published: bool = False
class CorrectionInput(BaseModel): worked_minutes: int = Field(ge=0); reason: str = Field(min_length=3, max_length=500)
class ClockPayload(BaseModel): device_event_id: uuid.UUID

def _manager(context: AuthContext):
    if context.user.role not in {UserRole.COMPANY_OWNER, UserRole.HR_ADMIN, UserRole.MANAGER}: raise HTTPException(403, "Workforce management permission required")

@router.post("/{company_code}/shift-templates", status_code=201)
async def create_shift_template(company_code: str, payload: ShiftTemplateInput, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _manager(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb:
            row = ShiftTemplate(**payload.model_dump()); tdb.add(row); await tdb.commit(); await tdb.refresh(row); return {"id": str(row.id), "name": row.name, "is_overnight": row.is_overnight}
    finally: await engine.dispose()

@router.get("/{company_code}/shift-templates")
async def list_shift_templates(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _manager(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb: return [{"id": str(x.id), "name": x.name, "start_time": x.start_time, "end_time": x.end_time, "break_minutes": x.break_minutes, "timezone": x.timezone, "is_overnight": x.is_overnight} for x in (await tdb.scalars(select(ShiftTemplate).where(ShiftTemplate.active.is_(True)))).all()]
    finally: await engine.dispose()

@router.post("/{company_code}/schedules", status_code=201)
async def assign_schedule(company_code: str, payload: ScheduleInput, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _manager(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb:
            employee = await tdb.get(Employee, payload.employee_id)
            if not employee: raise HTTPException(404, "Employee not found")
            row = WorkSchedule(**payload.model_dump()); tdb.add(row); await tdb.flush(); tdb.add(ScheduleChange(schedule_id=row.id, actor_user_id=context.user.id, action="created", reason="")); await tdb.commit(); return {"id": str(row.id), "employee_id": str(row.employee_id), "published": row.published}
    finally: await engine.dispose()

@router.post("/{company_code}/schedules/{schedule_id}/publish")
async def publish_schedule(company_code: str, schedule_id: uuid.UUID, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _manager(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb:
            row = await tdb.get(WorkSchedule, schedule_id)
            if not row: raise HTTPException(404, "Schedule not found")
            row.published = True; tdb.add(ScheduleChange(schedule_id=row.id, actor_user_id=context.user.id, action="published", reason="")); await tdb.commit(); return {"published": True}
    finally: await engine.dispose()

@router.post("/{company_code}/attendance/{employee_id}/correct")
async def correct_attendance(company_code: str, employee_id: uuid.UUID, payload: CorrectionInput, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _manager(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb:
            row = await tdb.scalar(select(AttendanceRecord).where(AttendanceRecord.employee_id == employee_id, AttendanceRecord.work_date == date.today()))
            if not row: raise HTTPException(404, "Attendance record not found")
            row.worked_minutes = payload.worked_minutes; row.correction_reason = payload.reason; row.status = "corrected"; await tdb.commit(); return {"id": str(row.id), "status": row.status, "reason": row.correction_reason}
    finally: await engine.dispose()

@router.post("/{company_code}/me/clock-in")
async def clock_in(company_code: str, payload: ClockPayload, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    await _employee(company_code, context, db); result = await PendingVerificationProvider().verify(str(context.user.id), datetime.now(UTC), {"event_id": str(payload.device_event_id)})
    if not result.verified: raise HTTPException(409, result.reason)
    raise HTTPException(501, "No attendance verification provider is activated")

@router.post("/{company_code}/me/clock-out")
async def clock_out(company_code: str, payload: ClockPayload, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    await _employee(company_code, context, db); raise HTTPException(409, "Attendance verification method is not configured")

@router.post("/{company_code}/me/breaks/start")
async def start_break(company_code: str, payload: ClockPayload, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb:
            rows = (await tdb.scalars(select(BreakRecord).where(BreakRecord.employee_id == employee_id, BreakRecord.active.is_(True)))).all()
            if active_break_count(rows) > 0: raise HTTPException(409, "An active break already exists")
            raise HTTPException(409, "Breaks require verified attendance")
    finally: await engine.dispose()

@router.get("/{company_code}/active-breaks")
async def active_breaks(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _manager(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb: return [{"id": str(x.id), "employee_id": str(x.employee_id), "started_at": x.started_at} for x in (await tdb.scalars(select(BreakRecord).where(BreakRecord.active.is_(True)))).all()]
    finally: await engine.dispose()
