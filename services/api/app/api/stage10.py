import base64
import json
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin import _ctx
from app.api.dependencies import AuthContext, require_tenant
from app.api.employee import _employee
from app.db.session import get_db
from app.models.admin import Employee, EmployeeDocument
from app.models.employee_mobile import LeaveRequest
from app.models.identity import UserRole
from app.models.payroll import DocumentVersion, LeaveComment, LeavePolicy, PayrollEntry, PayrollPeriod, PayrollRule
from app.services.audit import write_audit
from app.services.entitlements import require_feature

router = APIRouter(tags=["leave-payroll-documents"])

class Decision(BaseModel): status: str = Field(pattern="^(approved|rejected)$"); comment: str = ""
class CommentInput(BaseModel): body: str = Field(min_length=1, max_length=4000)
class PolicyInput(BaseModel): code: str; name: str; paid: bool = True; annual_days: int = Field(ge=0); requires_approval: bool = True
class RuleInput(BaseModel): code: str; name: str; rate: Decimal = Field(ge=0); config_json: dict = {}; effective_from: date
class PeriodInput(BaseModel): name: str; starts_on: date; ends_on: date
class DocumentInput(BaseModel): name: str; content_type: str = "application/pdf"; content_base64: str; expires_on: date | None = None

def _admin(context: AuthContext):
    if context.user.role not in {UserRole.COMPANY_OWNER, UserRole.HR_ADMIN, UserRole.MANAGER}: raise HTTPException(403, "Admin permission required")

@router.get("/admin/{company_code}/leave/requests")
async def leave_requests(company_code: str, status: str | None = None, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _admin(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb:
            q = select(LeaveRequest).order_by(LeaveRequest.created_at.desc())
            if status: q = q.where(LeaveRequest.status == status)
            return [{"id": str(x.id), "employee_id": str(x.employee_id), "starts_on": x.starts_on, "ends_on": x.ends_on, "reason": x.reason, "status": x.status} for x in (await tdb.scalars(q)).all()]
    finally: await engine.dispose()

@router.post("/admin/{company_code}/leave/{request_id}/decision")
async def decide_leave(company_code: str, request_id: uuid.UUID, payload: Decision, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _admin(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb:
            row = await tdb.get(LeaveRequest, request_id)
            if not row: raise HTTPException(404, "Leave request not found")
            row.status = payload.status; tdb.add(LeaveComment(leave_request_id=row.id, author_user_id=context.user.id, body=payload.comment))
            await tdb.commit(); return {"id": str(row.id), "status": row.status}
    finally: await engine.dispose()

@router.post("/employee/{company_code}/me/leave/{request_id}/comments")
async def add_leave_comment(company_code: str, request_id: uuid.UUID, payload: CommentInput, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb:
            request = await tdb.scalar(select(LeaveRequest).where(LeaveRequest.id == request_id, LeaveRequest.employee_id == employee_id))
            if not request: raise HTTPException(404, "Leave request not found")
            tdb.add(LeaveComment(leave_request_id=request.id, author_user_id=context.user.id, body=payload.body)); await tdb.commit(); return {"created": True}
    finally: await engine.dispose()

@router.post("/admin/{company_code}/leave/policies", status_code=201)
async def create_leave_policy(company_code: str, payload: PolicyInput, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _admin(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb: row = LeavePolicy(**payload.model_dump()); tdb.add(row); await tdb.commit(); return {"id": str(row.id), "code": row.code}
    finally: await engine.dispose()

@router.post("/admin/{company_code}/payroll/rules", status_code=201)
async def create_payroll_rule(company_code: str, payload: RuleInput, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _admin(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb: row = PayrollRule(code=payload.code, name=payload.name, rate=payload.rate, config_json=json.dumps(payload.config_json), effective_from=payload.effective_from); tdb.add(row); await tdb.commit(); return {"id": str(row.id), "code": row.code}
    finally: await engine.dispose()

@router.post("/admin/{company_code}/payroll/periods", status_code=201)
async def create_payroll_period(company_code: str, payload: PeriodInput, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _admin(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb: row = PayrollPeriod(**payload.model_dump()); tdb.add(row); await tdb.commit(); return {"id": str(row.id), "status": row.status}
    finally: await engine.dispose()

@router.post("/admin/{company_code}/payroll/periods/{period_id}/calculate")
async def calculate_payroll(company_code: str, period_id: uuid.UUID, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _admin(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb:
            period = await tdb.get(PayrollPeriod, period_id)
            if not period: raise HTTPException(404, "Payroll period not found")
            raise HTTPException(409, "Payroll formulas are configurable and require an approved rule set before calculation")
    finally: await engine.dispose()

@router.post("/admin/{company_code}/payroll/periods/{period_id}/approve")
async def approve_payroll(company_code: str, period_id: uuid.UUID, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _admin(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb:
            period = await tdb.get(PayrollPeriod, period_id)
            if not period: raise HTTPException(404, "Payroll period not found")
            if period.status != "calculated": raise HTTPException(409, "Only calculated payroll can be approved")
            period.status = "approved"; period.approved_at = datetime.now(UTC); period.approved_by = context.user.id; await tdb.commit(); await write_audit(db, context.user.id, "payroll.approved", "payroll_period", str(period.id)); await db.commit(); return {"status": period.status}
    finally: await engine.dispose()

@router.get("/employee/{company_code}/me/payroll/history")
async def employee_payroll_history(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    tenant, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        await require_feature(db, tenant.id, "payroll")
        async with factory() as tdb: return [{"id": str(x.id), "period_id": str(x.period_id), "gross": x.gross_amount, "deductions": x.deductions_amount, "net": x.net_amount, "status": x.status} for x in (await tdb.scalars(select(PayrollEntry).where(PayrollEntry.employee_id == employee_id, PayrollEntry.status == "approved").order_by(PayrollEntry.created_at.desc()))).all()]
    finally: await engine.dispose()

@router.post("/admin/{company_code}/employees/{employee_id}/documents", status_code=201)
async def upload_document(company_code: str, employee_id: uuid.UUID, payload: DocumentInput, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _admin(context); _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb:
            if not await tdb.get(Employee, employee_id): raise HTTPException(404, "Employee not found")
            try: content = base64.b64decode(payload.content_base64, validate=True)
            except Exception as exc: raise HTTPException(400, "Invalid document content") from exc
            doc = EmployeeDocument(employee_id=employee_id, name=payload.name, content_type=payload.content_type, content=content); tdb.add(doc); await tdb.flush(); tdb.add(DocumentVersion(employee_document_id=doc.id, version_number=1, content=content, expires_on=payload.expires_on)); await tdb.commit(); return {"id": str(doc.id), "version": 1}
    finally: await engine.dispose()

@router.get("/employee/{company_code}/me/documents/{document_id}/download")
async def download_document(company_code: str, document_id: uuid.UUID, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb:
            doc = await tdb.scalar(select(EmployeeDocument).where(EmployeeDocument.id == document_id, EmployeeDocument.employee_id == employee_id))
            if not doc: raise HTTPException(404, "Document not found")
            return {"name": doc.name, "content_type": doc.content_type, "content_base64": base64.b64encode(doc.content).decode()}
    finally: await engine.dispose()

@router.post("/employee/{company_code}/me/documents/{document_id}/acknowledge")
async def acknowledge_document(company_code: str, document_id: uuid.UUID, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, employee_id, engine, factory = await _employee(company_code, context, db)
    try:
        async with factory() as tdb:
            doc = await tdb.scalar(select(EmployeeDocument).where(EmployeeDocument.id == document_id, EmployeeDocument.employee_id == employee_id)); version = await tdb.scalar(select(DocumentVersion).where(DocumentVersion.employee_document_id == document_id).order_by(DocumentVersion.version_number.desc()))
            if not doc or not version: raise HTTPException(404, "Document not found")
            version.acknowledged_at = datetime.now(UTC); version.acknowledged_by = context.user.id; await tdb.commit(); return {"acknowledged": True}
    finally: await engine.dispose()
