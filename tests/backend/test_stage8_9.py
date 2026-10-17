from datetime import datetime, time, timezone
from pathlib import Path

from app.services.attendance_engine import calculate_attendance

ROOT = Path(__file__).parents[2]


def test_overnight_attendance_calculation_and_night_minutes():
    result = calculate_attendance(datetime(2026, 1, 1, 22, 0, tzinfo=timezone.utc), datetime(2026, 1, 2, 6, 30, tzinfo=timezone.utc), time(22, 0), time(6, 0), "UTC")
    assert result.worked_minutes == 510
    assert result.overtime_minutes == 30
    assert result.night_minutes >= 1


def test_stage8_9_contracts_exist_and_verification_is_disabled():
    assert (ROOT / "services/api/alembic/tenant_versions/versions/0004_attendance_scheduling.py").is_file()
    assert (ROOT / "services/api/alembic/tenant_versions/versions/0005_offline_sync.py").is_file()
    workforce = (ROOT / "services/api/app/api/workforce.py").read_text(encoding="utf-8")
    sync = (ROOT / "services/api/app/api/sync.py").read_text(encoding="utf-8")
    assert "PendingVerificationProvider" in workforce
    assert "An active break already exists" in workforce
    assert "timedelta(hours=48)" in sync
    assert "idempotency_key" in sync and "server_version" in sync


def test_offline_client_has_lease_outbox_and_conflict_primitives():
    source = (ROOT / "packages/flutter_core/lib/offline_sync.dart").read_text(encoding="utf-8")
    for symbol in ("OfflineLease", "LocalOutbox", "SyncEvent", "SyncConflict", "syncCursor", "remaining"):
        assert symbol in source
