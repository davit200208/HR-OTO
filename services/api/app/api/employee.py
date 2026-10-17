import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import AuthContext, require_tenant
from app.core.tenant_security import enforce_tenant_access
from app.db.session import get_db
from app.models.admin import Employee, EmployeeDocument
from app.models.employee_mobile import (Announcement, AttendanceRecord, BreakRecord, InAppNotification, LeaveBalance,
                                         LeaveRequest, Survey, SurveyResponse, WorkSchedule)
from app.models.identity import Tenant, TenantStatus, UserRole
from app.services.entitlements import effective_entitlements, require_feature
from app.services.tenant_provisioning import tenant_url
from app.services.verification import PendingVerificationProvider

router = APIRouter(prefix="/employee", tags=["employee-mobile"])

class LeaveRequestInput(BaseModel):
    starts_on: date; ends_on: date; reason: str = Field(default="", max_length=2000)
class SurveyResponseInput(BaseModel): answer: str = Field(min_length=1, max_length=5000)

async def _employee(company_code: str, context: AuthContext, db: AsyncSession):
    if context.user.role != UserRole.EMPLOYEE: raise HTTPException(403, "Employee role required")
    tenant = await db.scalar(select(Tenant).where(Tenant.company_code == company_code.upper(), Tenant.status == TenantStatus.ACTIVE))
    if not tenant: raise HTTPException(404, "Company not found")
    enforce_tenant_access(context.user.tenant_id, tenant.id)
    engine = create_async_engine(tenant_url(tenant.database_name)); factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as tdb:
        row = await tdb.scalar(select(Employee).where(Employee.user_id == context.user.id, Employee.archived_at == ""))
        if row is None: row = await tdb.scalar(select(Employee).where(Employee.email == context.user.email, Employee.archived_at == ""))
        if row is None: raise HTTPException(404, "Employee profile is not linked to this account")
    return tenant, row.id, engine, factory

def _profile(e: Employee): return {"id": str(e.id), "employee_id": e.employee_id, "first_name": e.first_name, "last_name": e.last_name, "email": e.email, "phone": e.phone, "employment_date": e.employment_date, "employment_status": e.employment_status, "department_id": str(e.department_id) if e.department_id else None, "position_id": str(e.position_id) if e.position_id else None, "branch_id": str(e.branch_id) if e.branch_id else None, "has_photo": e.photo_data is not None}

@router.get("/{company_code}/me/dashboard")
async def dashboard(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    tenant, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb:
            employee = await tdb.get(Employee, employee_id); today = date.today(); schedule = await tdb.scalar(select(WorkSchedule).where(WorkSchedule.employee_id == employee_id, WorkSchedule.work_date == today)); balance = await tdb.scalar(select(LeaveBalance).where(LeaveBalance.employee_id == employee_id)); attendance = await tdb.scalar(select(AttendanceRecord).where(AttendanceRecord.employee_id == employee_id, AttendanceRecord.work_date == today));
            return {"profile": _profile(employee), "today_schedule": {"start": schedule.start_time, "end": schedule.end_time, "break_minutes": schedule.break_minutes, "status": schedule.status} if schedule else None, "today_attendance": {"worked_minutes": attendance.worked_minutes, "status": attendance.status, "verified": attendance.verified} if attendance else None, "leave_balance": {"annual_days": balance.annual_days, "used_days": balance.used_days, "remaining_days": balance.annual_days - balance.used_days} if balance else {"annual_days": 0, "used_days": 0, "remaining_days": 0}}
    finally: await engine.dispose()

@router.get("/{company_code}/me/profile")
async def profile(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb: return _profile(await tdb.get(Employee, employee_id))
    finally: await engine.dispose()

@router.get("/{company_code}/me/schedules")
async def schedules(company_code: str, from_date: date | None = None, to_date: date | None = None, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db); from_date = from_date or date.today(); to_date = to_date or (from_date + timedelta(days=31))
    try:
        async with factory() as tdb: return [{"date": x.work_date, "start": x.start_time, "end": x.end_time, "break_minutes": x.break_minutes, "status": x.status} for x in (await tdb.scalars(select(WorkSchedule).where(WorkSchedule.employee_id == employee_id, WorkSchedule.work_date >= from_date, WorkSchedule.work_date <= to_date).order_by(WorkSchedule.work_date))).all()]
    finally: await engine.dispose()

@router.get("/{company_code}/me/attendance")
async def attendance(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb: return [{"date": x.work_date, "worked_minutes": x.worked_minutes, "status": x.status, "verified": x.verified, "verification_method": x.verification_method} for x in (await tdb.scalars(select(AttendanceRecord).where(AttendanceRecord.employee_id == employee_id).order_by(AttendanceRecord.work_date.desc()))).all()]
    finally: await engine.dispose()

@router.get("/{company_code}/me/breaks")
async def breaks(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb: return [{"date": x.break_date, "started_at": x.started_at, "ended_at": x.ended_at, "minutes": x.minutes} for x in (await tdb.scalars(select(BreakRecord).where(BreakRecord.employee_id == employee_id).order_by(BreakRecord.break_date.desc()))).all()]
    finally: await engine.dispose()

@router.get("/{company_code}/me/leave")
async def leave(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb:
            balance = await tdb.scalar(select(LeaveBalance).where(LeaveBalance.employee_id == employee_id)); requests = (await tdb.scalars(select(LeaveRequest).where(LeaveRequest.employee_id == employee_id).order_by(LeaveRequest.created_at.desc()))).all(); return {"balance": {"annual_days": balance.annual_days, "used_days": balance.used_days, "remaining_days": balance.annual_days - balance.used_days} if balance else {}, "requests": [{"id": str(x.id), "starts_on": x.starts_on, "ends_on": x.ends_on, "reason": x.reason, "status": x.status} for x in requests]}
    finally: await engine.dispose()

@router.post("/{company_code}/me/leave", status_code=201)
async def request_leave(company_code: str, payload: LeaveRequestInput, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    if payload.ends_on < payload.starts_on: raise HTTPException(400, "Invalid leave range")
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb: row = LeaveRequest(employee_id=employee_id, **payload.model_dump()); tdb.add(row); await tdb.commit(); await tdb.refresh(row); return {"id": str(row.id), "status": row.status}
    finally: await engine.dispose()

@router.get("/{company_code}/me/payroll")
async def payroll(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    tenant, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        await require_feature(db, tenant.id, "payroll")
        async with factory() as tdb:
            e = await tdb.get(Employee, employee_id); return {"salary_amount": e.salary_amount, "bonus_amount": e.bonus_amount, "currency": e.salary_currency}
    finally: await engine.dispose()

@router.get("/{company_code}/me/documents")
async def documents(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb: return [{"id": str(x.id), "name": x.name, "content_type": x.content_type, "created_at": x.created_at} for x in (await tdb.scalars(select(EmployeeDocument).where(EmployeeDocument.employee_id == employee_id).order_by(EmployeeDocument.created_at.desc()))).all()]
    finally: await engine.dispose()

@router.get("/{company_code}/me/announcements")
async def announcements(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, _, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb: return [{"id": str(x.id), "title": x.title, "body": x.body, "created_at": x.created_at} for x in (await tdb.scalars(select(Announcement).where(Announcement.published.is_(True)).order_by(Announcement.created_at.desc()))).all()]
    finally: await engine.dispose()

@router.get("/{company_code}/me/notifications")
async def notifications(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb: return [{"id": str(x.id), "title": x.title, "body": x.body, "read": x.read_at is not None} for x in (await tdb.scalars(select(InAppNotification).where(InAppNotification.employee_id == employee_id).order_by(InAppNotification.id.desc()))).all()]
    finally: await engine.dispose()

@router.get("/{company_code}/me/surveys")
async def surveys(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb:
            rows = (await tdb.scalars(select(Survey).where(Survey.active.is_(True)))).all(); answered = {x.survey_id for x in (await tdb.scalars(select(SurveyResponse).where(SurveyResponse.employee_id == employee_id))).all()}; return [{"id": str(x.id), "title": x.title, "question": x.question, "answered": x.id in answered} for x in rows]
    finally: await engine.dispose()

@router.post("/{company_code}/me/surveys/{survey_id}/responses", status_code=201)
async def survey_response(company_code: str, survey_id: uuid.UUID, payload: SurveyResponseInput, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb:
            survey = await tdb.scalar(select(Survey).where(Survey.id == survey_id, Survey.active.is_(True))); existing = await tdb.scalar(select(SurveyResponse).where(SurveyResponse.survey_id == survey_id, SurveyResponse.employee_id == employee_id))
            if not survey: raise HTTPException(404, "Survey not found")
            if existing: raise HTTPException(409, "Survey already answered")
            tdb.add(SurveyResponse(survey_id=survey_id, employee_id=employee_id, answer=payload.answer)); await tdb.commit(); return {"submitted": True}
    finally: await engine.dispose()

@router.get("/{company_code}/verification/status")
async def verification_status(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    await _employee(company_code, context, db); return {"configured": False, "provider": "pending", "attendance_writes_enabled": False}
