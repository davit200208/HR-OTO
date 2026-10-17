from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_stage4_migration_and_routes_exist() -> None:
    assert (ROOT / "services/api/alembic/versions/0004_commercial_entitlements.py").is_file()
    routes = (ROOT / "services/api/app/api/packages.py").read_text(encoding="utf-8")
    assert "/packages" in routes
    assert "company.commercial_override_created" in routes
    assert "price_version_created" in routes


def test_seed_prices_are_not_hardcoded_in_owner_ui() -> None:
    owner_ui = (ROOT / "apps/owner_flutter/lib/main.dart").read_text(encoding="utf-8")
    assert "39 GEL" not in owner_ui
    assert "89 GEL" not in owner_ui
    assert "179 GEL" not in owner_ui
