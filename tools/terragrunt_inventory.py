from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from packaging.version import Version

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


@dataclass(frozen=True)
class CompactCommand:
    path: list[str]
    aliases: list[str]
    category: str
    kind: str
    summary: str
    flags: list[dict[str, object]]
    help_sha256: str


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
) -> list[tuple[tuple[str, ...], tuple[str, ...], str, str]]:
    commands: list[tuple[tuple[str, ...], tuple[str, ...], str, str]] = []
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
        commands.append(((*parent, names[0]), names[1:], match.group(2), section))
    return commands


def parse_flags(help_text: str) -> list[dict[str, object]]:
    flags: list[dict[str, object]] = []
    in_options = False
    for line in help_text.splitlines():
        if line.strip() in {"Options:", "Flags:", "Global Options:"}:
            in_options = True
            continue
        if in_options and line.strip().endswith(":") and not line.startswith(" "):
            in_options = False
            continue
        if not in_options:
            continue
        match = re.match(r"^\s+--([a-z0-9-]+)(?:,\s*(-[a-z]))?(?:\s+([^ ]+))?\s{2,}", line)
        if match is None:
            continue
        flags.append(
            {
                "name": match.group(1),
                "short": match.group(2),
                "takes_value": match.group(3) is not None,
                "value_hint": match.group(3),
            }
        )
    return flags


def compact_inventory(data: Mapping[str, object]) -> dict[str, object]:
    commands = cast(list[dict[str, object]], data["commands"])
    compact = []
    for command in commands:
        raw_help = cast(str, command["help"])
        path = cast(list[str], command["path"])
        category = cast(str, command.get("category", ""))
        compact.append(
            asdict(
                CompactCommand(
                    path=path,
                    aliases=cast(list[str], command["aliases"]),
                    category=category,
                    kind="terragrunt",
                    summary=cast(str, command["summary"]),
                    flags=parse_flags(raw_help),
                    help_sha256=hashlib.sha256(raw_help.encode()).hexdigest(),
                )
            )
        )
    return {
        "schema_version": 1,
        "tool": data["tool"],
        "version": data["version"],
        "commands": compact,
    }


def inventory(version: str, *, max_depth: int = 2) -> dict[str, object]:
    root_help = run_mise(version, ("--help",))
    actual_version = parse_version(run_mise(version, ("--version",)))
    discovered: dict[tuple[str, ...], tuple[tuple[str, ...], str, str, str]] = {}
    pending = parse_commands(root_help)

    while pending:
        path, aliases, summary, category = pending.pop(0)
        if path in discovered:
            continue
        command_help = run_mise(version, (*path, "--help"))
        discovered[path] = (aliases, summary, category, command_help)
        if len(path) < max_depth:
            pending.extend(parse_commands(command_help, path))

    commands = [
        asdict(Command(path, aliases, summary, command_help)) | {"category": category}
        for path, (aliases, summary, category, command_help) in sorted(discovered.items())
    ]
    return {"tool": "terragrunt", "version": actual_version, "commands": commands}


def command_map(data: Mapping[str, object]) -> dict[tuple[str, ...], dict[str, object]]:
    commands = cast(list[dict[str, object]], data["commands"])
    return {tuple(cast(list[str], command["path"])): command for command in commands}


def compare(left: Mapping[str, object], right: Mapping[str, object]) -> dict[str, object]:
    left_commands = command_map(left)
    right_commands = command_map(right)
    added = sorted(set(right_commands) - set(left_commands))
    removed = sorted(set(left_commands) - set(right_commands))
    aliases_added: list[dict[str, object]] = []
    aliases_removed: list[dict[str, object]] = []
    changed: list[dict[str, object]] = []
    flags_added: list[dict[str, object]] = []
    flags_removed: list[dict[str, object]] = []
    flags_changed: list[dict[str, object]] = []
    for path in sorted(set(left_commands) & set(right_commands)):
        before = left_commands[path]
        after = right_commands[path]
        before_aliases = set(cast(list[str], before["aliases"]))
        after_aliases = set(cast(list[str], after["aliases"]))
        if before_aliases != after_aliases:
            if after_aliases - before_aliases:
                aliases_added.append(
                    {"path": list(path), "aliases": sorted(after_aliases - before_aliases)}
                )
            if before_aliases - after_aliases:
                aliases_removed.append(
                    {"path": list(path), "aliases": sorted(before_aliases - after_aliases)}
                )
        before_fields = {
            field: before.get(field)
            for field in ("category", "kind", "summary")
            if before.get(field) != after.get(field)
        }
        if before_fields:
            changed.append(
                {
                    "path": list(path),
                    "before": {field: before.get(field) for field in before_fields},
                    "after": {field: after.get(field) for field in before_fields},
                }
            )
        before_flags = {
            cast(str, flag["name"]): flag
            for flag in cast(list[dict[str, object]], before.get("flags", []))
        }
        after_flags = {
            cast(str, flag["name"]): flag
            for flag in cast(list[dict[str, object]], after.get("flags", []))
        }
        for name in sorted(set(after_flags) - set(before_flags)):
            flags_added.append({"path": list(path), "flag": after_flags[name]})
        for name in sorted(set(before_flags) - set(after_flags)):
            flags_removed.append({"path": list(path), "flag": before_flags[name]})
        for name in sorted(set(before_flags) & set(after_flags)):
            if before_flags[name] != after_flags[name]:
                flags_changed.append(
                    {
                        "path": list(path),
                        "name": name,
                        "before": before_flags[name],
                        "after": after_flags[name],
                    }
                )
    return {
        "tool": "terragrunt",
        "from": left["version"],
        "to": right["version"],
        "commands": {
            "added": [list(path) for path in added],
            "removed": [list(path) for path in removed],
            "aliases_added": aliases_added,
            "aliases_removed": aliases_removed,
            "changed": changed,
        },
        "flags": {
            "added": flags_added,
            "removed": flags_removed,
            "changed": flags_changed,
        },
    }


def write_inventory(version: str, output: Path, max_depth: int = 2) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(inventory(version, max_depth=max_depth), indent=2) + "\n", encoding="utf-8"
    )


def write_compact_inventory(version: str, output: Path, max_depth: int = 2) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(compact_inventory(inventory(version, max_depth=max_depth)), indent=2) + "\n",
        encoding="utf-8",
    )


def candidate_versions(path: Path) -> list[str]:
    candidates = cast(list[dict[str, object]], json.loads(path.read_text(encoding="utf-8")))
    versions: set[str] = set()
    for candidate in candidates:
        versions.add(cast(str, candidate["version"]))
        previous = candidate.get("previous_version")
        if previous is not None:
            versions.add(cast(str, previous))
    return sorted(versions, key=Version)


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
        "--compact-output-dir",
        type=Path,
        help="Also write normalized inventories to this directory",
    )
    parser.add_argument(
        "--candidate-file",
        type=Path,
        help="Generate versions named by a release candidate JSON report",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Regenerate inventories even when output files already exist",
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        type=Path,
        metavar=("FROM", "TO"),
        help="Compare two compact inventory JSON files instead of generating inventories",
    )
    args = parser.parse_args()
    if args.compare is not None:
        left = json.loads(args.compare[0].read_text(encoding="utf-8"))
        right = json.loads(args.compare[1].read_text(encoding="utf-8"))
        print(json.dumps(compare(left, right), indent=2))
        return
    versions = list(args.versions)
    if args.candidate_file is not None:
        versions.extend(candidate_versions(args.candidate_file))
    versions = sorted(set(versions), key=Version)
    if not versions:
        parser.error("provide at least one version or use --compare")
    if args.max_depth < 1:
        parser.error("--max-depth must be at least 1")
    for version in versions:
        full_output = args.output_dir / f"v{version.lstrip('v')}.json"
        if args.refresh or not full_output.exists():
            write_inventory(version, full_output, args.max_depth)
        if args.compact_output_dir is not None:
            compact_output = args.compact_output_dir / f"v{version.lstrip('v')}.json"
            if args.refresh or not compact_output.exists():
                write_compact_inventory(version, compact_output, args.max_depth)


if __name__ == "__main__":
    main()
