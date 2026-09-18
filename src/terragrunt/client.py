from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import TextIO

from packaging.version import Version

from .capabilities import Capabilities, capabilities_for
from .commands import providers_lock_args
from .errors import UnsupportedCommandError
from .models import CommandResult, Executable, OutputMode
from .runner import Runner
from .version import detect_version, resolve_executable


class TerragruntClient:
    def __init__(
        self,
        executable: Executable | str | Path = Executable.TERRAGRUNT,
        *,
        working_dir: str | Path = ".",
        environment: Mapping[str, str] | None = None,
        output_mode: OutputMode = OutputMode.STREAM,
        timeout: float | None = None,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
        runner: Runner | None = None,
    ) -> None:
        executable_name = executable.value if isinstance(executable, Executable) else executable
        resolved = runner.executable if runner is not None else resolve_executable(executable_name)
        self.executable = resolved
        self.runner = runner or Runner(
            resolved,
            working_dir=working_dir,
            environment=environment,
            output_mode=output_mode,
            timeout=timeout,
            stdout=stdout,
            stderr=stderr,
        )
        self._version = detect_version(resolved)
        self.capabilities: Capabilities = capabilities_for(
            self._version,
            enforce_terragrunt_version=Path(resolved).name == Executable.TERRAGRUNT.value,
        )

    @property
    def version(self) -> Version:
        return self._version

    def run(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        return self.runner.run(args, output_mode=output_mode, timeout=timeout, check=check)

    def init(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        return self.run("init", *args, output_mode=output_mode, timeout=timeout, check=check)

    def plan(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        return self.run("plan", *args, output_mode=output_mode, timeout=timeout, check=check)

    def apply(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        return self.run("apply", *args, output_mode=output_mode, timeout=timeout, check=check)

    def destroy(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        return self.run("destroy", *args, output_mode=output_mode, timeout=timeout, check=check)

    def output(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        return self.run("output", *args, output_mode=output_mode, timeout=timeout, check=check)

    def providers_lock(
        self,
        *,
        platforms: Iterable[str] = (),
        fs_mirror: str | Path | None = None,
        net_mirror: str | None = None,
        providers: Iterable[str] = (),
        extra_args: Iterable[str] = (),
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        args = providers_lock_args(
            platforms=platforms,
            fs_mirror=fs_mirror,
            net_mirror=net_mirror,
            providers=providers,
            extra_args=extra_args,
        )
        return self.run(
            "providers",
            "lock",
            *args,
            output_mode=output_mode,
            timeout=timeout,
            check=check,
        )

    def render(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        self._require("render")
        return self.run("render", *args, output_mode=output_mode, timeout=timeout, check=check)

    def list(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        self._require("list")
        return self.run("list", *args, output_mode=output_mode, timeout=timeout, check=check)

    def find(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        self._require("find")
        return self.run("find", *args, output_mode=output_mode, timeout=timeout, check=check)

    def stack_run(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        self._require("stack_commands")
        return self.run(
            "stack",
            "run",
            *args,
            output_mode=output_mode,
            timeout=timeout,
            check=check,
        )

    def stack_generate(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        self._require("stack_commands")
        return self.run(
            "stack",
            "generate",
            *args,
            output_mode=output_mode,
            timeout=timeout,
            check=check,
        )

    def stack_output(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        self._require("stack_commands")
        return self.run(
            "stack",
            "output",
            *args,
            output_mode=output_mode,
            timeout=timeout,
            check=check,
        )

    def stack_clean(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        self._require("stack_commands")
        return self.run(
            "stack",
            "clean",
            *args,
            output_mode=output_mode,
            timeout=timeout,
            check=check,
        )

    def exec_command(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        return self.run("exec", *args, output_mode=output_mode, timeout=timeout, check=check)

    def dag_graph(
        self,
        *args: str,
        output_mode: OutputMode | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> CommandResult:
        self._require("dag_graph")
        return self.run(
            "dag",
            "graph",
            *args,
            output_mode=output_mode,
            timeout=timeout,
            check=check,
        )

    def _require(self, command: str) -> None:
        if not self.capabilities.supports(command):
            raise UnsupportedCommandError(
                f"Command {command!r} is unsupported by Terragrunt {self.version}"
            )
