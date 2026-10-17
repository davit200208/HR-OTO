from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.companies import router as companies_router
from app.api.tenant import router as tenant_router
from app.api.owner import router as owner_router
from app.api.packages import router as packages_router
from app.api.integrations import router as integrations_router
from app.api.admin import router as admin_router
from app.api.employee import router as employee_router
from app.api.workforce import router as workforce_router
from app.api.sync import router as sync_router
from app.api.stage10 import router as stage10_router
from app.api.advanced_hr import router as advanced_hr_router
from app.api.reports import router as reports_router
from app.core.config import get_settings
from app.db.redis_client import redis_client


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await redis_client.aclose()


app = FastAPI(title=get_settings().app_name, version="0.1.0", lifespan=lifespan)
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(companies_router, prefix="/api/v1")
app.include_router(tenant_router, prefix="/api/v1")
app.include_router(owner_router, prefix="/api/v1")
app.include_router(packages_router, prefix="/api/v1")
app.include_router(integrations_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(employee_router, prefix="/api/v1")
app.include_router(workforce_router, prefix="/api/v1")
app.include_router(sync_router, prefix="/api/v1")
app.include_router(stage10_router, prefix="/api/v1")
app.include_router(advanced_hr_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")

