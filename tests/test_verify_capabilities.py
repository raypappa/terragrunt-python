from pathlib import Path

from tools.verify_capabilities import verify


def test_capability_fixtures_match_rules() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "terragrunt-cli"

    assert verify(fixture_dir) == []
