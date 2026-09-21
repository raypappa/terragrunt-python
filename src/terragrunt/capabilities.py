from dataclasses import dataclass
from warnings import warn

from packaging.version import Version

from .errors import TerragruntVersionError

MINIMUM_VERSION = Version("0.73.7")
LATEST_TESTED_VERSION = Version("0.73.8")


def _at_least(version: Version, minimum: str) -> bool:
    return version >= Version(minimum)


def _before(version: Version, maximum: str) -> bool:
    return version < Version(maximum)


@dataclass(frozen=True)
class Capabilities:
    version: Version
    supports_render: bool
    supports_stack_commands: bool
    supports_list: bool
    supports_find: bool
    supports_dag_graph: bool

    def supports(self, command: str) -> bool:
        return getattr(self, f"supports_{command.replace('-', '_')}", False)


def capabilities_for(version: Version, *, enforce_terragrunt_version: bool = True) -> Capabilities:
    if not enforce_terragrunt_version:
        return Capabilities(
            version=version,
            supports_render=False,
            supports_stack_commands=False,
            supports_list=False,
            supports_find=False,
            supports_dag_graph=False,
        )

    if version < MINIMUM_VERSION:
        raise TerragruntVersionError(
            f"Terragrunt {version} is unsupported; minimum version is {MINIMUM_VERSION}"
        )
    if version > LATEST_TESTED_VERSION:
        warn(
            f"Terragrunt {version} is newer than the tested version {LATEST_TESTED_VERSION}",
            RuntimeWarning,
            stacklevel=2,
        )

    return Capabilities(
        version=version,
        supports_render=_at_least(version, "0.77.17"),
        supports_stack_commands=_at_least(version, "0.73.7"),
        supports_list=_at_least(version, "0.76.3"),
        supports_find=_at_least(version, "0.75.4"),
        supports_dag_graph=(
            _at_least(version, "0.73.7")
            and (_before(version, "0.73.8") or _at_least(version, "0.90.0"))
        ),
    )
