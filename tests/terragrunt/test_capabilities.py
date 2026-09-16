import pytest
from packaging.version import Version

from terragrunt.capabilities import capabilities_for
from terragrunt.errors import TerragruntVersionError


def test_minimum_version_is_supported() -> None:
    capabilities = capabilities_for(Version("0.73.7"))

    assert capabilities.supports_render
    assert capabilities.supports_stack_commands


def test_older_version_is_rejected() -> None:
    with pytest.raises(TerragruntVersionError):
        capabilities_for(Version("0.73.6"))


def test_newer_version_warns() -> None:
    with pytest.warns(RuntimeWarning):
        capabilities_for(Version("0.74.0"))


def test_non_terragrunt_version_does_not_use_terragrunt_gate() -> None:
    capabilities = capabilities_for(Version("1.10.0"), enforce_terragrunt_version=False)

    assert not capabilities.supports_render
