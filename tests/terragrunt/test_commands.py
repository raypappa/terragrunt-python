from pathlib import Path

from terragrunt.commands import providers_lock_args


def test_providers_lock_args_builds_repeatable_and_extra_arguments() -> None:
    assert providers_lock_args(
        platforms=("darwin_arm64", "linux_amd64"),
        fs_mirror=Path("/mirror"),
        net_mirror="https://mirror.example.com",
        providers=("registry.terraform.io/hashicorp/aws",),
        extra_args=("-var-file=dev.tfvars",),
    ) == (
        "-platform=darwin_arm64",
        "-platform=linux_amd64",
        "-fs-mirror=/mirror",
        "-net-mirror=https://mirror.example.com",
        "registry.terraform.io/hashicorp/aws",
        "-var-file=dev.tfvars",
    )
