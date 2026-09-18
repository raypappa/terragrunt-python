import pytest
from packaging.version import Version

from terragrunt.capabilities import LATEST_TESTED_VERSION, capabilities_for
from terragrunt.errors import TerragruntVersionError


def test_minimum_version_is_supported() -> None:
    capabilities = capabilities_for(Version("0.73.7"))

    assert not capabilities.supports_render
    assert capabilities.supports_stack_commands


def test_capabilities_follow_command_introduction_versions() -> None:
    assert not capabilities_for(Version("0.75.3")).supports_find
    assert capabilities_for(Version("0.75.4")).supports_find
    assert not capabilities_for(Version("0.76.2")).supports_list
    assert capabilities_for(Version("0.76.3")).supports_list
    assert not capabilities_for(Version("0.77.16")).supports_render
    assert capabilities_for(Version("0.77.17")).supports_render


def test_older_version_is_rejected() -> None:
    with pytest.raises(TerragruntVersionError):
        capabilities_for(Version("0.73.6"))


def test_newer_version_warns() -> None:
    with pytest.warns(RuntimeWarning, match=str(LATEST_TESTED_VERSION)):
        capabilities_for(Version("1.0.3"))


def test_non_terragrunt_version_does_not_use_terragrunt_gate() -> None:
    capabilities = capabilities_for(Version("1.10.0"), enforce_terragrunt_version=False)

    assert not capabilities.supports_render
