from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

VERSION_PATTERN = re.compile(r"(?:version\s+)?v?(\d+\.\d+\.\d+)")
COMMAND_PATTERN = re.compile(r"^\s{3,}([a-z][a-z0-9-]*(?:,\s*[a-z][a-z0-9-]*)*)\s{2,}(.+?)\s*$")
SECTION_PATTERN = re.compile(
    r"^\s*(?:Commands:|OpenTofu shortcuts:|[A-Za-z][A-Za-z ]+ commands:)\s*$"
)


@dataclass(frozen=True)
class Command:
    path: tuple[str, ...]
    aliases: tuple[str, ...]
    summary: str
    help: str


def run_mise(version: str, args: Sequence[str]) -> str:
    command = ["mise", "exec", f"terragrunt@{version}", "--", "terragrunt", *args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}\n{output}"
        )
    return output


def parse_version(output: str) -> str:
    match = VERSION_PATTERN.search(output)
    if match is None:
        raise ValueError(f"Unable to parse Terragrunt version from: {output!r}")
    return match.group(1)


def parse_commands(
    help_text: str, parent: tuple[str, ...] = ()
) -> list[tuple[tuple[str, ...], tuple[str, ...], str]]:
    commands: list[tuple[tuple[str, ...], tuple[str, ...], str]] = []
    in_commands = False
    section = ""
    for line in help_text.splitlines():
        section_match = SECTION_PATTERN.match(line)
        if section_match:
            section = section_match.group(0).strip().removesuffix(":")
            in_commands = True
            continue
        if in_commands and line.strip().endswith(":") and not line.startswith(" "):
            in_commands = False
            continue
        if not in_commands or section == "OpenTofu shortcuts":
            continue
        match = COMMAND_PATTERN.match(line)
        if match is None:
            continue
        names = tuple(name.strip() for name in match.group(1).split(","))
        commands.append(((*parent, names[0]), names[1:], match.group(2)))
    return commands


def inventory(version: str, *, max_depth: int = 2) -> dict[str, object]:
    root_help = run_mise(version, ("--help",))
    actual_version = parse_version(run_mise(version, ("--version",)))
    discovered: dict[tuple[str, ...], tuple[tuple[str, ...], str, str]] = {}
    pending = parse_commands(root_help)

    while pending:
        path, aliases, summary = pending.pop(0)
        if path in discovered:
            continue
        command_help = run_mise(version, (*path, "--help"))
        discovered[path] = (aliases, summary, command_help)
        if len(path) < max_depth:
            pending.extend(parse_commands(command_help, path))

    commands = [
        asdict(Command(path, aliases, summary, command_help))
        for path, (aliases, summary, command_help) in sorted(discovered.items())
    ]
    return {"tool": "terragrunt", "version": actual_version, "commands": commands}


def compare(left: Mapping[str, object], right: Mapping[str, object]) -> dict[str, object]:
    left_command_list = cast(list[dict[str, object]], left["commands"])
    right_command_list = cast(list[dict[str, object]], right["commands"])
    left_commands = {
        " ".join(cast(list[str], command["path"])): command for command in left_command_list
    }
    right_commands = {
        " ".join(cast(list[str], command["path"])): command for command in right_command_list
    }
    added = sorted(set(right_commands) - set(left_commands))
    removed = sorted(set(left_commands) - set(right_commands))
    changed = []
    for path in sorted(set(left_commands) & set(right_commands)):
        before = left_commands[path]
        after = right_commands[path]
        if before["aliases"] != after["aliases"] or before["summary"] != after["summary"]:
            changed.append(
                {
                    "path": path.split(" "),
                    "before": {"aliases": before["aliases"], "summary": before["summary"]},
                    "after": {"aliases": after["aliases"], "summary": after["summary"]},
                }
            )
    return {
        "tool": "terragrunt",
        "from": left["version"],
        "to": right["version"],
        "added": [path.split(" ") for path in added],
        "removed": [path.split(" ") for path in removed],
        "changed": changed,
    }


def write_inventory(version: str, output: Path, max_depth: int = 2) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(inventory(version, max_depth=max_depth), indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Terragrunt CLI command inventory.")
    parser.add_argument("versions", nargs="*", help="Terragrunt versions to inspect")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reference/terragrunt-commands"),
        help="Directory for generated JSON inventories",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="Maximum command path depth to inspect (default: 2)",
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        type=Path,
        metavar=("FROM", "TO"),
        help="Compare two existing inventory JSON files instead of generating inventories",
    )
    args = parser.parse_args()
    if args.compare is not None:
        left = json.loads(args.compare[0].read_text(encoding="utf-8"))
        right = json.loads(args.compare[1].read_text(encoding="utf-8"))
        print(json.dumps(compare(left, right), indent=2))
        return
    if not args.versions:
        parser.error("provide at least one version or use --compare")
    if args.max_depth < 1:
        parser.error("--max-depth must be at least 1")
    for version in args.versions:
        write_inventory(version, args.output_dir / f"v{version.lstrip('v')}.json", args.max_depth)


if __name__ == "__main__":
    main()
