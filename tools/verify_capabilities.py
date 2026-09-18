from __future__ import annotations

import argparse
import json
from pathlib import Path

from packaging.version import Version

from terragrunt.capabilities import capabilities_for

CAPABILITY_PATHS = {
    "render": ("render",),
    "find": ("find",),
    "list": ("list",),
    "stack_commands": ("stack",),
    "dag_graph": ("dag", "graph"),
}


def fixture_commands(path: Path) -> set[tuple[str, ...]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {tuple(command["path"]) for command in data["commands"]}


def verify_fixture(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    version = Version(data["version"])
    commands = fixture_commands(path)
    capabilities = capabilities_for(version)
    errors: list[str] = []
    for capability, command_path in CAPABILITY_PATHS.items():
        expected = command_path in commands
        actual = capabilities.supports(capability)
        if expected != actual:
            errors.append(
                f"{path}: {capability}={actual} but command {' '.join(command_path)!r} "
                f"is {'present' if expected else 'absent'}"
            )
    return errors


def verify(directory: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(directory.glob("v*.json"), key=lambda item: Version(item.stem[1:])):
        errors.extend(verify_fixture(path))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify Terragrunt capability rules against fixtures."
    )
    parser.add_argument("--fixture-dir", type=Path, default=Path("tests/fixtures/terragrunt-cli"))
    args = parser.parse_args()
    errors = verify(args.fixture_dir)
    if errors:
        parser.exit(1, "\n".join(errors) + "\n")
    print(f"Verified {len(list(args.fixture_dir.glob('v*.json')))} capability fixtures.")


if __name__ == "__main__":
    main()
