from pathlib import Path


def test_health_contract_is_declared() -> None:
    source = Path(__file__).parents[2] / "services" / "api" / "app" / "api" / "health.py"
    content = source.read_text(encoding="utf-8")
    assert 'prefix="/health"' in content
    assert '"/live"' in content
    assert '"/ready"' in content

