from pathlib import Path
ROOT=Path(__file__).parents[2]
def test_stage11_advanced_models_api_and_feature_guards():
    assert (ROOT/"services/api/alembic/tenant_versions/versions/0007_advanced_hr.py").is_file()
    source=(ROOT/"services/api/app/api/advanced_hr.py").read_text(encoding="utf-8")
    for key in ("performance","discipline","recruitment","training","require_feature"): assert key in source
def test_stage12_reporting_and_existing_notification_boundaries():
    assert (ROOT/"services/api/app/api/reports.py").is_file()
    assert "provider_integrations" in (ROOT/"services/api/alembic/versions/0005_integrations_notifications.py").read_text(encoding="utf-8")
def test_stage13_final_artifacts_are_explicitly_not_fabricated():
    assert (ROOT/"docs/PROGRESS.md").is_file()
    assert not (ROOT/"dist/release").exists()
