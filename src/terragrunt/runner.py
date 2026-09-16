import os
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TextIO

from .errors import TerragruntError
from .models import CommandResult, OutputMode


class Runner:
    def __init__(
        self,
        executable: str,
        *,
        working_dir: str | Path = ".",
        environment: Mapping[str, str] | None = None,
        output_mode: OutputMode = OutputMode.STREAM,
        timeout: float | None = None,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
    ) -> None:
        self.executable = executable
        self.working_dir = Path(working_dir)
        self.environment = dict(environment or {})
        self.output_mode = output_mode
        self.timeout = timeout
        self.stdout = stdout
        self.stderr = stderr

    def run(
        self,
        args: Sequence[str],
        *,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        command = (self.executable, *args)
        mode = output_mode or self.output_mode
        try:
            completed = subprocess.run(
                command,
                cwd=self.working_dir,
                env={**os.environ, **self.environment},
                check=False,
                text=True,
                timeout=self.timeout if timeout is None else timeout,
                capture_output=mode == OutputMode.CAPTURE,
                stdout=None if mode == OutputMode.CAPTURE else self.stdout,
                stderr=None if mode == OutputMode.CAPTURE else self.stderr,
            )
        except subprocess.TimeoutExpired as exc:
            result = CommandResult(command, -1, _text(exc.stdout), _text(exc.stderr))
            raise TerragruntError(f"Command timed out: {' '.join(command)}", result) from exc
        except OSError as exc:
            raise TerragruntError(f"Unable to execute command: {' '.join(command)}") from exc

        result = CommandResult(
            command, completed.returncode, completed.stdout or "", completed.stderr or ""
        )
        if check and not result.succeeded:
            raise TerragruntError(
                f"Command failed with exit code {result.returncode}: {' '.join(command)}",
                result,
            )
        return result


def _text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    return value.decode() if isinstance(value, bytes) else value
