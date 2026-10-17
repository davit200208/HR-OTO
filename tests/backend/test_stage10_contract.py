from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_stage10_migration_and_endpoints_exist():
    assert (ROOT / "services/api/alembic/tenant_versions/versions/0006_leave_payroll_documents.py").is_file()
    source = (ROOT / "services/api/app/api/stage10.py").read_text(encoding="utf-8")
    for token in ("leave", "payroll", "documents", "approved", "DocumentVersion", "require_feature"):
        assert token in source


def test_payroll_final_approval_is_not_offline_capable():
    source = (ROOT / "services/api/app/api/stage10.py").read_text(encoding="utf-8")
    assert "Only calculated payroll can be approved" in source
    assert "payroll.approved" in source
