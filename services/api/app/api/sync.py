import json
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin import _ctx
from app.api.dependencies import AuthContext, require_tenant
from app.db.session import get_db
from app.models.admin import TenantSetting
from app.models.employee_mobile import DeviceRegistration, SyncEvent
from app.models.identity import UserRole
from app.services.tenant_provisioning import tenant_url
from app.core.config import get_settings

router = APIRouter(prefix="/sync", tags=["offline-sync"])

class DeviceInput(BaseModel): device_id: str = Field(min_length=8, max_length=160); platform: str = Field(min_length=2, max_length=24); client_time: datetime | None = None
class SyncEventInput(BaseModel): event_id: uuid.UUID; idempotency_key: str = Field(min_length=8, max_length=160); entity: str = Field(min_length=2, max_length=100); payload: dict; base_version: int = Field(ge=0)

@router.post("/{company_code}/device")
async def register_device(company_code: str, payload: DeviceInput, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    if context.user.role not in {UserRole.EMPLOYEE, UserRole.COMPANY_OWNER, UserRole.HR_ADMIN, UserRole.MANAGER}: raise HTTPException(403, "Device registration is not allowed")
    tenant, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb:
            row = await tdb.scalar(select(DeviceRegistration).where(DeviceRegistration.device_id == payload.device_id)) or DeviceRegistration(device_id=payload.device_id, user_id=context.user.id, platform=payload.platform)
            row.user_id = context.user.id; row.platform = payload.platform; row.last_seen_at = datetime.now(UTC)
            if payload.client_time: row.clock_skew_seconds = int((datetime.now(UTC) - payload.client_time.astimezone(UTC)).total_seconds())
            tdb.add(row); await tdb.commit(); return {"device_id": row.device_id, "clock_skew_seconds": row.clock_skew_seconds, "server_time": datetime.now(UTC)}
    finally: await engine.dispose()

@router.get("/{company_code}/lease")
async def offline_lease(company_code: str, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    tenant, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb:
            setting = await tdb.get(TenantSetting, "sync_server_version"); version = int(setting.value) if setting and setting.value.isdigit() else 0
        now = datetime.now(UTC); expires = now + timedelta(hours=48); payload = {"sub": str(context.user.id), "tenant": str(tenant.id), "type": "offline_lease", "iat": now, "exp": expires, "server_version": version}
        token = jwt.encode(payload, get_settings().jwt_secret_key, algorithm=get_settings().jwt_algorithm)
        return {"lease_token": token, "issued_at": now, "expires_at": expires, "server_version": version, "max_offline_hours": 48}
    finally: await engine.dispose()

@router.post("/{company_code}/events")
async def sync_event(company_code: str, payload: SyncEventInput, context: AuthContext = Depends(require_tenant), db: AsyncSession = Depends(get_db)):
    _, engine, factory = await _ctx(company_code, context, db)
    try:
        async with factory() as tdb:
            existing = await tdb.scalar(select(SyncEvent).where(SyncEvent.idempotency_key == payload.idempotency_key))
            if existing: return {"status": existing.status, "duplicate": True, "server_version": existing.server_version}
            setting = await tdb.get(TenantSetting, "sync_server_version"); version = int(setting.value) + 1 if setting and setting.value.isdigit() else 1
            if setting is None: setting = TenantSetting(key="sync_server_version", value=str(version)); tdb.add(setting)
            else: setting.value = str(version)
            event = SyncEvent(event_id=payload.event_id, idempotency_key=payload.idempotency_key, user_id=context.user.id, entity=payload.entity, payload=json.dumps(payload.payload, ensure_ascii=False), server_version=version); tdb.add(event); await tdb.commit(); return {"status": "accepted", "duplicate": False, "server_version": version}
    finally: await engine.dispose()
