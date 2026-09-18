import json
from pathlib import Path

from tools.terragrunt_transitions import scan_transitions


def test_scan_transitions_reports_adjacent_fixture_changes() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "terragrunt-cli"

    reports = scan_transitions(fixture_dir)

    assert len(reports) == 1
    assert reports[0]["from"] == "0.73.7"
    assert reports[0]["to"] == "0.90.0"


def test_scan_transitions_can_write_json(tmp_path: Path) -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "terragrunt-cli"
    report = scan_transitions(fixture_dir, from_version="0.90.0")

    assert json.loads(json.dumps(report)) == report
