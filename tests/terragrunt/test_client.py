from unittest.mock import patch

from packaging.version import Version

from terragrunt.capabilities import capabilities_for
from terragrunt.client import TerragruntClient
from terragrunt.models import CommandResult, Executable
from terragrunt.runner import Runner


def test_client_builds_provider_lock_command() -> None:
    runner = Runner("terragrunt")

    with (
        patch("terragrunt.client.detect_version", return_value=Version("0.73.7")),
        patch.object(
            runner,
            "run",
            return_value=CommandResult(("terragrunt",), 0, "", ""),
        ) as run,
    ):
        client = TerragruntClient(runner=runner)
        client.capabilities = capabilities_for(client.version)
        client.providers_lock(platforms=("linux_amd64",), providers=("hashicorp/aws",))

    run.assert_called_once()
    assert run.call_args.args[0] == ("providers", "lock", "-platform=linux_amd64", "hashicorp/aws")


def test_executable_enum_values() -> None:
    assert Executable.TERRAGRUNT.value == "terragrunt"
