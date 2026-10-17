from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.admin import _ctx, _admin
from app.api.dependencies import AuthContext, require_tenant
from app.db.session import get_db
from app.models.employee_mobile import AttendanceRecord, BreakRecord, LeaveRequest
from app.models.payroll import PayrollEntry

router=APIRouter(prefix="/reports",tags=["reporting"])
@router.get("/{company_code}/summary")
async def summary(company_code:str,from_date:date|None=None,to_date:date|None=None,context:AuthContext=Depends(require_tenant),db:AsyncSession=Depends(get_db)):
    _admin(context);_,engine,factory=await _ctx(company_code,context,db)
    try:
        async with factory() as tdb:
            attendance=(select(func.count(AttendanceRecord.id),func.coalesce(func.sum(AttendanceRecord.worked_minutes),0)).where(AttendanceRecord.verified.is_(True)))
            if from_date: attendance=attendance.where(AttendanceRecord.work_date>=from_date)
            if to_date: attendance=attendance.where(AttendanceRecord.work_date<=to_date)
            a=await tdb.execute(attendance); row=a.one(); leave=await tdb.scalar(select(func.count(LeaveRequest.id)).where(LeaveRequest.status=="approved")); breaks=await tdb.scalar(select(func.coalesce(func.sum(BreakRecord.minutes),0))); payroll=await tdb.scalar(select(func.coalesce(func.sum(PayrollEntry.net_amount),0)).where(PayrollEntry.status=="approved")); return {"attendance_records":row[0] or 0,"worked_minutes":row[1] or 0,"approved_leave_requests":leave or 0,"break_minutes":breaks or 0,"approved_payroll_net":payroll or 0}
    finally: await engine.dispose()
