import json
from pathlib import Path

from tools.terragrunt_transitions import non_empty_transition, scan_transitions


def test_scan_transitions_reports_adjacent_fixture_changes() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "terragrunt-cli"

    reports = scan_transitions(fixture_dir)

    fixture_versions = [path.stem.removeprefix("v") for path in sorted(fixture_dir.glob("v*.json"))]

    adjacent_pairs = set(zip(fixture_versions, fixture_versions[1:], strict=False))

    assert all(non_empty_transition(report) for report in reports)
    assert all((report["from"], report["to"]) in adjacent_pairs for report in reports)


def test_scan_transitions_can_write_json(tmp_path: Path) -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "terragrunt-cli"
    report = scan_transitions(fixture_dir, from_version="0.90.0")

    assert json.loads(json.dumps(report)) == report
