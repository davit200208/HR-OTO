import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthContext, require_permission
from app.db.session import get_db
from app.models.identity import AuditLog, LicenseStatus, Tenant, TenantStatus
from app.schemas.tenant import AuditLogResponse, DashboardResponse

router = APIRouter(prefix="/owner", tags=["owner"])


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(_: AuthContext = Depends(require_permission("system:manage")), db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count(Tenant.id))) or 0
    active = await db.scalar(select(func.count(Tenant.id)).where(Tenant.status == TenantStatus.ACTIVE)) or 0
    blocked = await db.scalar(select(func.count(Tenant.id)).where(Tenant.status == TenantStatus.BLOCKED)) or 0
    trial = await db.scalar(select(func.count(Tenant.id)).where(Tenant.license_status == LicenseStatus.TRIAL)) or 0
    active_licenses = await db.scalar(select(func.count(Tenant.id)).where(Tenant.license_status == LicenseStatus.ACTIVE)) or 0
    expired = await db.scalar(select(func.count(Tenant.id)).where(Tenant.license_status == LicenseStatus.EXPIRED)) or 0
    revenue = await db.scalar(select(func.coalesce(func.sum(Tenant.monthly_revenue), 0))) or 0
    return DashboardResponse(total_companies=total, active_companies=active, blocked_companies=blocked,
                             trial_companies=trial, active_licenses=active_licenses,
                             expired_licenses=expired, monthly_revenue=revenue)


@router.get("/audit-log", response_model=list[AuditLogResponse])
async def audit_log(_: AuthContext = Depends(require_permission("system:manage")),
                    db: AsyncSession = Depends(get_db), limit: int = Query(default=100, ge=1, le=500)):
    result = await db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
    return list(result)
