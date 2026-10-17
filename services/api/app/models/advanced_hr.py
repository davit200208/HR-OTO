import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class KpiGoal(Base, TimestampMixin):
    __tablename__ = "kpi_goals"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200)); target: Mapped[str] = mapped_column(Text, default=""); status: Mapped[str] = mapped_column(String(24), default="active")

class PerformanceReview(Base, TimestampMixin):
    __tablename__ = "performance_reviews"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(Uuid); score: Mapped[int | None] = mapped_column(Integer, nullable=True); feedback: Mapped[str] = mapped_column(Text, default=""); status: Mapped[str] = mapped_column(String(24), default="draft")

class DisciplinaryCase(Base, TimestampMixin):
    __tablename__ = "disciplinary_cases"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200)); description: Mapped[str] = mapped_column(Text); status: Mapped[str] = mapped_column(String(24), default="open"); restricted_level: Mapped[int] = mapped_column(Integer, default=2)

class RecruitmentJob(Base, TimestampMixin):
    __tablename__ = "recruitment_jobs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200)); description: Mapped[str] = mapped_column(Text, default=""); status: Mapped[str] = mapped_column(String(24), default="open")

class Candidate(Base, TimestampMixin):
    __tablename__ = "candidates"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recruitment_jobs.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160)); email: Mapped[str] = mapped_column(String(254), default=""); cv_document_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True); status: Mapped[str] = mapped_column(String(32), default="new")

class TrainingCourse(Base, TimestampMixin):
    __tablename__ = "training_courses"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200)); description: Mapped[str] = mapped_column(Text, default=""); status: Mapped[str] = mapped_column(String(24), default="active")

class TrainingEnrollment(Base, TimestampMixin):
    __tablename__ = "training_enrollments"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_courses.id", ondelete="CASCADE"), index=True); employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True); score: Mapped[int | None] = mapped_column(Integer, nullable=True); status: Mapped[str] = mapped_column(String(24), default="enrolled")
