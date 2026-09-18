from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from packaging.version import InvalidVersion, Version

DEFAULT_KEYWORDS = (
    "introduced",
    "added",
    "new command",
    "deprecated",
    "removed",
    "remove",
    "replacement",
    "renamed",
    "breaking",
    "cli redesign",
    "command",
)
DEFAULT_COMMANDS = (
    "backend",
    "catalog",
    "dag",
    "exec",
    "find",
    "graph-dependencies",
    "hcl",
    "hclfmt",
    "hclvalidate",
    "list",
    "render",
    "run",
    "run-all",
    "scaffold",
    "stack",
    "validate-inputs",
)
VERSION_PATTERN = re.compile(r"^v?(\d+\.\d+\.\d+)$")


@dataclass(frozen=True)
class Match:
    keyword: str
    line: str


@dataclass(frozen=True)
class Candidate:
    version: str
    previous_version: str | None
    release_file: str
    matches: list[Match]
    commands: list[str]


def release_version(path: Path) -> Version:
    match = VERSION_PATTERN.match(path.stem)
    if match is None:
        raise ValueError(f"Release note filename is not a semantic version: {path.name}")
    try:
        return Version(match.group(1))
    except InvalidVersion as error:
        raise ValueError(f"Release note filename is not a valid version: {path.name}") from error


def release_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("v*.md"), key=release_version)


def find_candidates(
    directory: Path,
    *,
    keywords: tuple[str, ...] = DEFAULT_KEYWORDS,
    commands: tuple[str, ...] = DEFAULT_COMMANDS,
) -> list[dict[str, object]]:
    files = release_files(directory)
    candidates: list[dict[str, object]] = []
    for index, path in enumerate(files):
        lines = path.read_text(encoding="utf-8").splitlines()
        matches: list[Match] = []
        matched_commands: set[str] = set()
        for line in lines:
            lowered = line.casefold()
            for keyword in keywords:
                if keyword.casefold() in lowered:
                    matches.append(Match(keyword, line.strip()))
            for command in commands:
                if re.search(rf"(?<![a-z0-9-]){re.escape(command)}(?![a-z0-9-])", lowered):
                    matched_commands.add(command)
        if not matches and not matched_commands:
            continue
        candidates.append(
            asdict(
                Candidate(
                    version=path.stem.lstrip("v"),
                    previous_version=files[index - 1].stem.lstrip("v") if index else None,
                    release_file=str(path),
                    matches=matches,
                    commands=sorted(matched_commands),
                )
            )
        )
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Find Terragrunt release-note candidates.")
    parser.add_argument("--release-dir", type=Path, default=Path("reference/terragrunt-releases"))
    parser.add_argument("--output", type=Path, help="Write JSON output to a file")
    parser.add_argument("--keyword", action="append", dest="keywords")
    parser.add_argument("--command", action="append", dest="commands")
    args = parser.parse_args()
    result = find_candidates(
        args.release_dir,
        keywords=tuple(args.keywords) if args.keywords else DEFAULT_KEYWORDS,
        commands=tuple(args.commands) if args.commands else DEFAULT_COMMANDS,
    )
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
