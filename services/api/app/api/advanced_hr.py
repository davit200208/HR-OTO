import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.admin import _ctx
from app.api.dependencies import AuthContext, require_tenant
from app.db.session import get_db
from app.models.advanced_hr import Candidate, DisciplinaryCase, KpiGoal, PerformanceReview, RecruitmentJob, TrainingCourse, TrainingEnrollment
from app.models.identity import UserRole
from app.services.entitlements import require_feature

router=APIRouter(prefix="/advanced-hr",tags=["advanced-hr"])
class TitleInput(BaseModel): title:str=Field(min_length=2); description:str=""
class GoalInput(BaseModel): employee_id:uuid.UUID; title:str; target:str=""
class ReviewInput(BaseModel): employee_id:uuid.UUID; score:int|None=None; feedback:str=""
class CaseInput(BaseModel): employee_id:uuid.UUID; title:str; description:str
class CandidateInput(BaseModel): name:str; email:str=""
class EnrollmentInput(BaseModel): employee_id:uuid.UUID
def _admin(c:AuthContext):
    if c.user.role not in {UserRole.COMPANY_OWNER,UserRole.HR_ADMIN,UserRole.MANAGER}: raise HTTPException(403,"Admin permission required")
async def _create(company_code,context,db,model,values,feature):
    _admin(context); tenant,engine,factory=await _ctx(company_code,context,db)
    try:
        await require_feature(db,tenant.id,feature)
        async with factory() as tdb:
            row=model(**values);tdb.add(row);await tdb.commit();await tdb.refresh(row);return {"id":str(row.id),**{k:getattr(row,k) for k in values if k in {"title","name","status"}}}
    finally: await engine.dispose()
@router.post("/{company_code}/kpi/goals",status_code=201)
async def create_goal(company_code:str,payload:GoalInput,context:AuthContext=Depends(require_tenant),db:AsyncSession=Depends(get_db)): return await _create(company_code,context,db,KpiGoal,payload.model_dump(),"performance")
@router.post("/{company_code}/performance/reviews",status_code=201)
async def create_review(company_code:str,payload:ReviewInput,context:AuthContext=Depends(require_tenant),db:AsyncSession=Depends(get_db)): return await _create(company_code,context,db,PerformanceReview,{**payload.model_dump(),"reviewer_user_id":context.user.id},"performance")
@router.post("/{company_code}/discipline/cases",status_code=201)
async def create_case(company_code:str,payload:CaseInput,context:AuthContext=Depends(require_tenant),db:AsyncSession=Depends(get_db)): return await _create(company_code,context,db,DisciplinaryCase,payload.model_dump(),"discipline")
@router.post("/{company_code}/recruitment/jobs",status_code=201)
async def create_job(company_code:str,payload:TitleInput,context:AuthContext=Depends(require_tenant),db:AsyncSession=Depends(get_db)): return await _create(company_code,context,db,RecruitmentJob,payload.model_dump(),"recruitment")
@router.post("/{company_code}/training/courses",status_code=201)
async def create_course(company_code:str,payload:TitleInput,context:AuthContext=Depends(require_tenant),db:AsyncSession=Depends(get_db)): return await _create(company_code,context,db,TrainingCourse,payload.model_dump(),"training")
@router.post("/{company_code}/training/{course_id}/enroll",status_code=201)
async def enroll(company_code:str,course_id:uuid.UUID,payload:EnrollmentInput,context:AuthContext=Depends(require_tenant),db:AsyncSession=Depends(get_db)):
    _admin(context);tenant,engine,factory=await _ctx(company_code,context,db)
    try:
        await require_feature(db,tenant.id,"training")
        async with factory() as tdb:
            row=TrainingEnrollment(course_id=course_id,employee_id=payload.employee_id);tdb.add(row);await tdb.commit();return {"id":str(row.id),"status":row.status}
    finally: await engine.dispose()
