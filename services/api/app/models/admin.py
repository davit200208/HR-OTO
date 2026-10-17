import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, LargeBinary, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Department(Base, TimestampMixin):
    __tablename__ = "departments"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Position(Base, TimestampMixin):
    __tablename__ = "positions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Branch(Base, TimestampMixin):
    __tablename__ = "branches"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    address: Mapped[str] = mapped_column(String(255), default="")
    manager_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, unique=True, nullable=True, index=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    personal_id: Mapped[str] = mapped_column(String(64), default="")
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    position_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("positions.id", ondelete="SET NULL"), nullable=True)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    employment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    employment_status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    salary_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bonus_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(3), default="GEL")
    photo_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    photo_content_type: Mapped[str] = mapped_column(String(80), default="")
    archived_at: Mapped[str] = mapped_column(String(40), default="")


class EmployeeDocument(Base, TimestampMixin):
    __tablename__ = "employee_documents"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    content_type: Mapped[str] = mapped_column(String(80), default="application/octet-stream")
    content: Mapped[bytes] = mapped_column(LargeBinary)


class TenantSetting(Base):
    __tablename__ = "tenant_settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
