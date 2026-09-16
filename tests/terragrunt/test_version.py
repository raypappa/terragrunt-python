import pytest
from packaging.version import Version

from terragrunt.errors import TerragruntError
from terragrunt.version import parse_version


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("terragrunt version v0.73.7", Version("0.73.7")),
        ("Terraform v1.10.0", Version("1.10.0")),
        ("OpenTofu v1.9.0", Version("1.9.0")),
    ],
)
def test_parse_version(output: str, expected: Version) -> None:
    assert parse_version(output) == expected


def test_parse_version_rejects_missing_version() -> None:
    with pytest.raises(TerragruntError):
        parse_version("not a version")
