"""packages, pricing versions, features, limits and commercial overrides"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_commercial_entitlements"
down_revision: Union[str, None] = "0003_owner_operations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid_type = sa.Uuid(as_uuid=True)
    op.create_table("packages",
        sa.Column("id", uuid_type, nullable=False), sa.Column("code", sa.String(48), nullable=False),
        sa.Column("name", sa.String(120), nullable=False), sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_packages")), sa.UniqueConstraint("code", name=op.f("uq_packages_code")))
    op.create_index(op.f("ix_packages_code"), "packages", ["code"], unique=False)
    op.create_table("package_price_versions",
        sa.Column("id", uuid_type, nullable=False), sa.Column("package_id", uuid_type, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False), sa.Column("monthly_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("annual_price", sa.Numeric(12, 2), nullable=False), sa.Column("discount_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False), sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["packages.id"], ondelete="CASCADE", name=op.f("fk_package_price_versions_package_id_packages")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_package_price_versions")))
    op.create_index(op.f("ix_package_price_versions_package_id"), "package_price_versions", ["package_id"], unique=False)
    op.create_table("package_features",
        sa.Column("id", uuid_type, nullable=False), sa.Column("package_id", uuid_type, nullable=False),
        sa.Column("feature_key", sa.String(80), nullable=False), sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["packages.id"], ondelete="CASCADE", name=op.f("fk_package_features_package_id_packages")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_package_features")))
    op.create_index(op.f("ix_package_features_package_id"), "package_features", ["package_id"], unique=False)
    op.create_index(op.f("ix_package_features_feature_key"), "package_features", ["feature_key"], unique=False)
    op.create_table("package_limits",
        sa.Column("id", uuid_type, nullable=False), sa.Column("package_id", uuid_type, nullable=False),
        sa.Column("limit_key", sa.String(80), nullable=False), sa.Column("limit_value", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["packages.id"], ondelete="CASCADE", name=op.f("fk_package_limits_package_id_packages")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_package_limits")))
    op.create_index(op.f("ix_package_limits_package_id"), "package_limits", ["package_id"], unique=False)
    op.create_index(op.f("ix_package_limits_limit_key"), "package_limits", ["limit_key"], unique=False)
    op.create_table("company_subscriptions",
        sa.Column("id", uuid_type, nullable=False), sa.Column("tenant_id", uuid_type, nullable=False), sa.Column("package_id", uuid_type, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False), sa.Column("agreed_monthly_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("agreed_annual_price", sa.Numeric(12, 2), nullable=False), sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True)), sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE", name=op.f("fk_company_subscriptions_tenant_id_tenants")),
        sa.ForeignKeyConstraint(["package_id"], ["packages.id"], name=op.f("fk_company_subscriptions_package_id_packages")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_subscriptions")), sa.UniqueConstraint("tenant_id", name=op.f("uq_company_subscriptions_tenant_id")))
    op.create_index(op.f("ix_company_subscriptions_package_id"), "company_subscriptions", ["package_id"], unique=False)
    op.create_table("company_commercial_overrides",
        sa.Column("id", uuid_type, nullable=False), sa.Column("tenant_id", uuid_type, nullable=False), sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("key", sa.String(80), nullable=False), sa.Column("bool_value", sa.Boolean()), sa.Column("int_value", sa.Integer()),
        sa.Column("decimal_value", sa.Numeric(12, 2)), sa.Column("currency", sa.String(3)), sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True)), sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE", name=op.f("fk_company_commercial_overrides_tenant_id_tenants")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_commercial_overrides")))
    op.create_index(op.f("ix_company_commercial_overrides_tenant_id"), "company_commercial_overrides", ["tenant_id"], unique=False)
    op.create_table("trial_grants",
        sa.Column("id", uuid_type, nullable=False), sa.Column("tenant_id", uuid_type, nullable=False), sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False), sa.Column("reason", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE", name=op.f("fk_trial_grants_tenant_id_tenants")), sa.PrimaryKeyConstraint("id", name=op.f("pk_trial_grants")))
    op.create_index(op.f("ix_trial_grants_tenant_id"), "trial_grants", ["tenant_id"], unique=False)

    packages = [
        {"id": "11111111-1111-1111-1111-111111111111", "code": "START", "name": "START", "description": "საწყისი HR პაკეტი", "is_active": True, "is_archived": False},
        {"id": "22222222-2222-2222-2222-222222222222", "code": "BUSINESS", "name": "BUSINESS", "description": "ზრდადი კომპანიის HR პაკეტი", "is_active": True, "is_archived": False},
        {"id": "33333333-3333-3333-3333-333333333333", "code": "PRO", "name": "PRO", "description": "სრული HR ფუნქციონალი", "is_active": True, "is_archived": False},
    ]
    op.bulk_insert(sa.table("packages", sa.column("id", uuid_type), sa.column("code", sa.String), sa.column("name", sa.String), sa.column("description", sa.Text), sa.column("is_active", sa.Boolean), sa.column("is_archived", sa.Boolean)), packages)
    prices = [
        {"id": "11111111-1111-1111-1111-111111111112", "package_id": packages[0]["id"], "currency": "GEL", "monthly_price": 39, "annual_price": 468, "discount_percent": 0, "effective_from": datetime(2026, 1, 1, tzinfo=timezone.utc)},
        {"id": "22222222-2222-2222-2222-222222222223", "package_id": packages[1]["id"], "currency": "GEL", "monthly_price": 89, "annual_price": 1068, "discount_percent": 0, "effective_from": datetime(2026, 1, 1, tzinfo=timezone.utc)},
        {"id": "33333333-3333-3333-3333-333333333334", "package_id": packages[2]["id"], "currency": "GEL", "monthly_price": 179, "annual_price": 2148, "discount_percent": 0, "effective_from": datetime(2026, 1, 1, tzinfo=timezone.utc)},
    ]
    op.bulk_insert(sa.table("package_price_versions", sa.column("id", uuid_type), sa.column("package_id", uuid_type), sa.column("currency", sa.String), sa.column("monthly_price", sa.Numeric), sa.column("annual_price", sa.Numeric), sa.column("discount_percent", sa.Numeric), sa.column("effective_from", sa.DateTime)), prices)
    feature_sets = {
        packages[0]["id"]: ["employees", "departments", "attendance", "leave", "announcements", "notifications", "reports"],
        packages[1]["id"]: ["employees", "departments", "positions", "branches", "attendance", "leave", "documents", "kpi", "training", "announcements", "notifications", "reports"],
        packages[2]["id"]: ["employees", "departments", "positions", "branches", "schedules", "attendance", "leave", "payroll", "documents", "kpi", "discipline", "recruiting", "training", "surveys", "announcements", "notifications", "reports"],
    }
    features = []
    for package_id, keys in feature_sets.items():
        for index, key in enumerate(keys):
            features.append({"id": f"{package_id[:8]}-{index:04d}-1111-1111-111111111111", "package_id": package_id, "feature_key": key, "enabled": True})
    op.bulk_insert(sa.table("package_features", sa.column("id", uuid_type), sa.column("package_id", uuid_type), sa.column("feature_key", sa.String), sa.column("enabled", sa.Boolean)), features)
    limit_values = {packages[0]["id"]: {"employees": 15, "administrators": 2, "managers": 3, "branches": 1, "devices": 20, "storage_mb": 1024, "sms_quota": 100, "email_quota": 1000}, packages[1]["id"]: {"employees": 50, "administrators": 5, "managers": 10, "branches": 5, "devices": 75, "storage_mb": 5120, "sms_quota": 500, "email_quota": 5000}, packages[2]["id"]: {"employees": 150, "administrators": 15, "managers": 30, "branches": 15, "devices": 250, "storage_mb": 20480, "sms_quota": 2000, "email_quota": 20000}}
    limits = []
    for package_id, values in limit_values.items():
        for index, (key, value) in enumerate(values.items()):
            limits.append({"id": f"{package_id[:8]}-{index:04d}-0000-0000-000000000000", "package_id": package_id, "limit_key": key, "limit_value": value})
    op.bulk_insert(sa.table("package_limits", sa.column("id", uuid_type), sa.column("package_id", uuid_type), sa.column("limit_key", sa.String), sa.column("limit_value", sa.Integer)), limits)


def downgrade() -> None:
    op.drop_table("trial_grants")
    op.drop_table("company_commercial_overrides")
    op.drop_table("company_subscriptions")
    op.drop_table("package_limits")
    op.drop_table("package_features")
    op.drop_table("package_price_versions")
    op.drop_table("packages")
