from tools.terragrunt_inventory import compare, parse_commands, parse_version


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
        (("run",), (), "Run a command."),
        (("stack",), (), "Run stack commands."),
        (("find",), ("fd",), "Find configurations."),
        (("list",), ("ls",), "List configurations."),
    ]


def test_parse_nested_commands() -> None:
    help_text = """\
Commands:
   format, fmt   Format HCL.
   validate      Validate HCL.
Global Options:
"""

    assert parse_commands(help_text, ("hcl",)) == [
        (("hcl", "format"), ("fmt",), "Format HCL."),
        (("hcl", "validate"), (), "Validate HCL."),
    ]


def test_compare_inventories() -> None:
    before = {
        "tool": "terragrunt",
        "version": "0.90.0",
        "commands": [
            {"path": ["run"], "aliases": [], "summary": "Run", "help": ""},
            {"path": ["hcl", "fmt"], "aliases": [], "summary": "Format", "help": ""},
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
        "added": [["list"]],
        "removed": [["hcl", "fmt"]],
        "changed": [
            {
                "path": ["run"],
                "before": {"aliases": [], "summary": "Run"},
                "after": {"aliases": [], "summary": "Run commands"},
            }
        ],
    }
