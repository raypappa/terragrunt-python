import re
import shutil
import subprocess
from pathlib import Path

from packaging.version import Version

from .errors import TerragruntError

VERSION_PATTERN = re.compile(r"\bv?(\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?)\b")


def resolve_executable(executable: str | Path) -> str:
    candidate = str(executable)
    resolved = shutil.which(candidate)
    if resolved is None:
        raise FileNotFoundError(f"Executable not found: {candidate}")
    return resolved


def parse_version(output: str) -> Version:
    match = VERSION_PATTERN.search(output)
    if match is None:
        raise TerragruntError(f"Unable to parse executable version from: {output!r}")
    return Version(match.group(1))


def detect_version(executable: str, *, timeout: float | None = 30.0) -> Version:
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
    except OSError as exc:
        raise TerragruntError(f"Unable to execute {executable}: {exc}") from exc

    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    if result.returncode != 0:
        raise TerragruntError(
            f"Version command failed with exit code {result.returncode}: {output}"
        )
    return parse_version(output)
