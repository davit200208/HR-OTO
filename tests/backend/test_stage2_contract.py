from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_stage2_migrations_exist() -> None:
    assert (ROOT / "services/api/alembic/versions/0002_multitenant_identity.py").is_file()
    assert (ROOT / "services/api/alembic/tenant_versions/versions/0001_tenant_core.py").is_file()


def test_auth_and_tenant_routes_are_registered() -> None:
    main = (ROOT / "services/api/app/main.py").read_text(encoding="utf-8")
    assert "auth_router" in main
    assert "companies_router" in main
    assert "tenant_router" in main


def test_owner_stage3_routes_are_registered() -> None:
    main = (ROOT / "services/api/app/main.py").read_text(encoding="utf-8")
    companies = (ROOT / "services/api/app/api/companies.py").read_text(encoding="utf-8")
    owner = (ROOT / "services/api/app/api/owner.py").read_text(encoding="utf-8")
    assert "owner_router" in main
    assert "/dashboard" in owner
    assert "company.owner_created" in companies
    assert "company.updated" in companies


def test_secret_material_is_not_in_env_example() -> None:
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "JWT_SECRET_KEY=replace_with" in env
    assert "BREVO_API_KEY=" not in env
    assert "SMSOFFLINE_API_KEY=" not in env
