import json
from pathlib import Path

from tools.release_candidates import find_candidates


def test_find_candidates_matches_keywords_and_commands() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "terragrunt-releases"

    candidates = find_candidates(fixture_dir)

    assert [candidate["version"] for candidate in candidates] == ["0.73.7", "0.75.4"]
    assert candidates[0]["previous_version"] is None
    assert candidates[0]["commands"] == ["stack"]
    assert candidates[1]["previous_version"] == "0.74.0"
    assert candidates[1]["commands"] == ["find"]
    assert candidates[1]["matches"] == [
        {"keyword": "cli redesign", "line": "## CLI Redesign"},
        {
            "keyword": "introduced",
            "line": "The `find` command was introduced as an experimental command.",
        },
        {
            "keyword": "command",
            "line": "The `find` command was introduced as an experimental command.",
        },
    ]


def test_candidate_output_is_json_serializable() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "terragrunt-releases"

    assert json.loads(json.dumps(find_candidates(fixture_dir)))
