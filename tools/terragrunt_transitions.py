from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from packaging.version import Version

try:
    from tools.terragrunt_inventory import compare
except ModuleNotFoundError:
    from terragrunt_inventory import compare


def transition_files(directory: Path) -> list[Path]:
    return sorted(
        directory.glob("v*.json"),
        key=lambda path: Version(path.stem.removeprefix("v")),
    )


def non_empty_transition(report: dict[str, object]) -> bool:
    return any(
        section_values
        for section in ("commands", "flags")
        for section_values in cast(dict[str, list[object]], report[section]).values()
    )


def scan_transitions(
    directory: Path,
    *,
    from_version: str | None = None,
    to_version: str | None = None,
) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    files = transition_files(directory)
    lower = Version(from_version) if from_version else None
    upper = Version(to_version) if to_version else None
    for before_path, after_path in zip(files, files[1:], strict=False):
        before_version = Version(before_path.stem.removeprefix("v"))
        after_version = Version(after_path.stem.removeprefix("v"))
        if lower and before_version < lower:
            continue
        if upper and after_version > upper:
            continue
        before = json.loads(before_path.read_text(encoding="utf-8"))
        after = json.loads(after_path.read_text(encoding="utf-8"))
        report = compare(before, after)
        if non_empty_transition(report):
            reports.append(report)
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan adjacent Terragrunt CLI fixture transitions."
    )
    parser.add_argument("--fixture-dir", type=Path, default=Path("tests/fixtures/terragrunt-cli"))
    parser.add_argument("--from-version")
    parser.add_argument("--to-version")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = (
        json.dumps(
            scan_transitions(
                args.fixture_dir,
                from_version=args.from_version,
                to_version=args.to_version,
            ),
            indent=2,
        )
        + "\n"
    )
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
