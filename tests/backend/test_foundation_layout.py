from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_foundation_directories_exist() -> None:
    for path in ["apps/employee_flutter", "apps/admin_flutter", "apps/owner_flutter",
                 "packages/flutter_design_system", "services/api", "infra"]:
        assert (ROOT / path).is_dir()


def test_secrets_are_not_in_example() -> None:
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "BREVO_API_KEY=" not in content
    assert "SMSOFFLINE_API_KEY=" not in content

