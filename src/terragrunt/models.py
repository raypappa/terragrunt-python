from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TextIO


class Executable(StrEnum):
    TERRAGRUNT = "terragrunt"
    OPENTOFU = "tofu"
    TERRAFORM = "terraform"


class OutputMode(StrEnum):
    STREAM = "stream"
    CAPTURE = "capture"


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class RunnerConfig:
    working_dir: Path
    environment: dict[str, str]
    output_mode: OutputMode
    timeout: float | None
    stdout: TextIO | None
    stderr: TextIO | None
