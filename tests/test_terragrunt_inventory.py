from pathlib import Path
from typing import cast

from tools.terragrunt_inventory import (
    candidate_versions,
    compact_inventory,
    compare,
    parse_commands,
    parse_version,
)


def test_parse_version() -> None:
    assert parse_version("terragrunt version v0.90.0") == "0.90.0"


def test_parse_commands_with_categories_and_aliases() -> None:
    help_text = """\
Main commands:
   run          Run a command.
   stack        Run stack commands.

Discovery commands:
   find, fd     Find configurations.
   list, ls     List configurations.

Global Options:
   --help       Show help.
"""

    assert parse_commands(help_text) == [
        (("run",), (), "Run a command.", "Main commands"),
        (("stack",), (), "Run stack commands.", "Main commands"),
        (("find",), ("fd",), "Find configurations.", "Discovery commands"),
        (("list",), ("ls",), "List configurations.", "Discovery commands"),
    ]


def test_parse_nested_commands() -> None:
    help_text = """\
Commands:
   format, fmt   Format HCL.
   validate      Validate HCL.
Global Options:
"""

    assert parse_commands(help_text, ("hcl",)) == [
        (("hcl", "format"), ("fmt",), "Format HCL.", "Commands"),
        (("hcl", "validate"), (), "Validate HCL.", "Commands"),
    ]


def test_compact_inventory_normalizes_help() -> None:
    compact = compact_inventory(
        {
            "tool": "terragrunt",
            "version": "0.90.0",
            "commands": [
                {
                    "path": ["hcl", "fmt"],
                    "aliases": ["format"],
                    "category": "Configuration commands",
                    "summary": "Format HCL.",
                    "help": (
                        "Options:\n"
                        "   --parallelism value  Number of workers.\n"
                        "   --check  Check only.\n"
                    ),
                }
            ],
        }
    )

    command = cast(list[dict[str, object]], compact["commands"])[0]
    assert command["path"] == ["hcl", "fmt"]
    assert command["category"] == "Configuration commands"
    assert command["flags"] == [
        {"name": "parallelism", "short": None, "takes_value": True, "value_hint": "value"},
        {"name": "check", "short": None, "takes_value": False, "value_hint": None},
    ]


def test_compare_inventories() -> None:
    before = {
        "tool": "terragrunt",
        "version": "0.90.0",
        "commands": [
            {"path": ["run"], "aliases": [], "summary": "Run", "help": ""},
            {"path": ["hcl", "fmt"], "aliases": [], "summary": "Format", "help": ""},
            {"path": ["list"], "aliases": [], "summary": "List", "help": ""},
        ],
    }
    after = {
        "tool": "terragrunt",
        "version": "0.93.2",
        "commands": [
            {"path": ["run"], "aliases": [], "summary": "Run commands", "help": ""},
            {"path": ["list"], "aliases": ["ls"], "summary": "List", "help": ""},
        ],
    }

    assert compare(before, after) == {
        "tool": "terragrunt",
        "from": "0.90.0",
        "to": "0.93.2",
        "commands": {
            "added": [],
            "removed": [["hcl", "fmt"]],
            "aliases_added": [{"path": ["list"], "aliases": ["ls"]}],
            "aliases_removed": [],
            "changed": [
                {
                    "path": ["run"],
                    "before": {"summary": "Run"},
                    "after": {"summary": "Run commands"},
                }
            ],
        },
        "flags": {"added": [], "removed": [], "changed": []},
    }


def test_compare_compact_fixtures() -> None:
    import json
    from pathlib import Path

    fixture_dir = Path(__file__).parent / "fixtures" / "terragrunt-cli"
    before = json.loads((fixture_dir / "v0.73.7.json").read_text())
    after = json.loads((fixture_dir / "v0.90.0.json").read_text())

    result = compare(before, after)
    commands = cast(dict[str, object], result["commands"])
    flags = cast(dict[str, object], result["flags"])

    assert commands["added"] == [["run"]]
    assert commands["removed"] == [["hclfmt"], ["run-all"]]
    assert commands["aliases_added"] == [{"path": ["hcl", "fmt"], "aliases": ["format"]}]
    assert flags["added"] == [
        {
            "path": ["hcl", "fmt"],
            "flag": {
                "name": "parallelism",
                "short": None,
                "takes_value": True,
                "value_hint": "value",
            },
        }
    ]


def test_candidate_versions_includes_predecessors(tmp_path: Path) -> None:
    candidates = tmp_path / "candidates.json"
    candidates.write_text(
        '[{"version": "0.75.4", "previous_version": "0.75.3"}, '
        '{"version": "0.90.0", "previous_version": "0.89.4"}]'
    )

    assert candidate_versions(candidates) == ["0.75.3", "0.75.4", "0.89.4", "0.90.0"]
