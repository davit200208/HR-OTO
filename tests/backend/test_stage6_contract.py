from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_stage6_tenant_migration_and_admin_routes_exist():
    assert (ROOT / "services/api/alembic/tenant_versions/versions/0002_admin_core.py").is_file()
    routes = (ROOT / "services/api/app/api/admin.py").read_text(encoding="utf-8")
    for path in ("dashboard", "employees", "departments", "positions", "branches", "entitlements", "settings", "users"):
        assert path in routes
    assert "require_limit" in routes
    assert "enforce_tenant_access" in routes


def test_admin_client_is_real_api_driven_and_adaptive():
    ui = (ROOT / "apps/admin_flutter/lib/main.dart").read_text(encoding="utf-8")
    assert "auth/login" in ui
    assert "admin/" in ui
    assert "NavigationRail" in ui and "NavigationBar" in ui
    assert "HR-OTO Admin" in ui
