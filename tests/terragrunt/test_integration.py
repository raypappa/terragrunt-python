import os
import shutil
import subprocess
from pathlib import Path

import pytest
from packaging.version import Version

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
    expected_version = os.environ.get("TERRAGRUNT_EXPECTED_VERSION")
    if executable is Executable.TERRAGRUNT and expected_version is not None:
        assert str(client.version) == expected_version


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


@pytest.fixture
def terragrunt_client(tmp_path: Path) -> TerragruntClient:
    path = _installed_executable(Executable.TERRAGRUNT)
    _write_minimal_configuration(tmp_path, Executable.TERRAGRUNT)
    return TerragruntClient(
        executable=path,
        working_dir=tmp_path,
        output_mode=OutputMode.CAPTURE,
        timeout=60,
    )


def _require_capability(client: TerragruntClient, command: str) -> None:
    if not client.capabilities.supports(command):
        pytest.skip(f"Terragrunt {client.version} does not support {command}")


def _cli_redesign_args(client: TerragruntClient) -> tuple[str, ...]:
    if Version("0.75.4") <= client.version < Version("0.78.0"):
        return ("--experiment", "cli-redesign")
    return ()


@pytest.mark.integration
def test_terragrunt_render(terragrunt_client: TerragruntClient) -> None:
    _require_capability(terragrunt_client, "render")

    result = terragrunt_client.render(*_cli_redesign_args(terragrunt_client), "--json")

    assert result.succeeded
    assert "terraform" in result.stdout


@pytest.mark.integration
def test_terragrunt_find(terragrunt_client: TerragruntClient) -> None:
    _require_capability(terragrunt_client, "find")

    result = terragrunt_client.find(*_cli_redesign_args(terragrunt_client), "--json")

    assert result.succeeded
    assert result.stdout.strip()


@pytest.mark.integration
def test_terragrunt_list(terragrunt_client: TerragruntClient) -> None:
    _require_capability(terragrunt_client, "list")

    result = terragrunt_client.list(*_cli_redesign_args(terragrunt_client))

    assert result.succeeded
    assert result.stdout.strip()


@pytest.mark.integration
def test_terragrunt_dag_graph(terragrunt_client: TerragruntClient) -> None:
    _require_capability(terragrunt_client, "dag_graph")

    result = terragrunt_client.dag_graph()

    assert result.succeeded


@pytest.mark.integration
def test_terragrunt_exec_command(terragrunt_client: TerragruntClient) -> None:
    if terragrunt_client.version < Version("0.80.0"):
        pytest.skip("exec command is not covered before Terragrunt 0.80.0")

    result = terragrunt_client.exec_command("--", "terragrunt", "--version")

    assert result.succeeded
    assert str(terragrunt_client.version) in result.stdout + result.stderr


def _write_minimal_configuration(directory: Path, executable: Executable) -> None:
    (directory / "main.tf").write_text("terraform {}\n", encoding="utf-8")
    if executable is Executable.TERRAGRUNT:
        (directory / "terragrunt.hcl").write_text("terraform { }\n", encoding="utf-8")
