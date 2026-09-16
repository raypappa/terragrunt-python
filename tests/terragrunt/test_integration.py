import shutil
import subprocess
from pathlib import Path

import pytest

from terragrunt import Executable, OutputMode, TerragruntClient

EXECUTABLES = tuple(Executable)


def _installed_executable(executable: Executable) -> str:
    path = shutil.which(executable.value)
    if path is None:
        pytest.skip(f"{executable.value} is not installed")
        raise AssertionError("pytest.skip should stop execution")
    result = subprocess.run(
        [path, "--version"],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"{executable.value} is not runnable: {result.stderr.strip()}")
        raise AssertionError("pytest.skip should stop execution")
    return path


@pytest.mark.integration
@pytest.mark.parametrize("executable", EXECUTABLES)
def test_installed_executable_reports_version(executable: Executable, tmp_path: Path) -> None:
    client = TerragruntClient(
        executable=_installed_executable(executable),
        working_dir=tmp_path,
        output_mode=OutputMode.CAPTURE,
    )

    result = client.run("--version")

    assert result.succeeded
    assert result.returncode == 0
    assert str(client.version) in result.stdout + result.stderr


@pytest.mark.integration
@pytest.mark.parametrize("executable", EXECUTABLES)
def test_installed_executable_can_initialize_and_plan(
    executable: Executable,
    tmp_path: Path,
) -> None:
    _write_minimal_configuration(tmp_path, executable)
    client = TerragruntClient(
        executable=_installed_executable(executable),
        working_dir=tmp_path,
        output_mode=OutputMode.CAPTURE,
        timeout=60,
    )

    init_result = client.init(
        "-backend=false",
        "-input=false",
        "-no-color",
    )
    plan_result = client.plan(
        "-input=false",
        "-no-color",
    )

    assert init_result.succeeded
    assert plan_result.succeeded
    assert "No changes" in plan_result.stdout


def _write_minimal_configuration(directory: Path, executable: Executable) -> None:
    (directory / "main.tf").write_text("terraform {}\n", encoding="utf-8")
    if executable is Executable.TERRAGRUNT:
        (directory / "terragrunt.hcl").write_text("terraform { }\n", encoding="utf-8")
