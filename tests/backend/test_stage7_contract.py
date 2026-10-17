from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_stage7_employee_mobile_contract():
    assert (ROOT / "services/api/alembic/tenant_versions/versions/0003_employee_mobile.py").is_file()
    routes = (ROOT / "services/api/app/api/employee.py").read_text(encoding="utf-8")
    for path in ("dashboard", "profile", "schedules", "attendance", "breaks", "leave", "payroll", "documents", "announcements", "notifications", "surveys"):
        assert path in routes
    assert "UserRole.EMPLOYEE" in routes
    assert "enforce_tenant_access" in routes


def test_verification_is_pending_by_default_and_pin_is_absent():
    provider = (ROOT / "services/api/app/services/verification.py").read_text(encoding="utf-8")
    assert "PendingVerificationProvider" in provider
    assert "VerificationResult(False" in provider
    employee_ui = (ROOT / "apps/employee_flutter/lib/main.dart").read_text(encoding="utf-8")
    assert "EmployeeApi" in employee_ui and "NavigationBar" in employee_ui
    assert "PIN" not in employee_ui
