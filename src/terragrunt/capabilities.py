from dataclasses import dataclass
from warnings import warn

from packaging.version import Version

from .errors import TerragruntVersionError

MINIMUM_VERSION = Version("0.73.7")


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
    if version > MINIMUM_VERSION:
        warn(
            f"Terragrunt {version} is newer than the tested version {MINIMUM_VERSION}",
            RuntimeWarning,
            stacklevel=2,
        )

    return Capabilities(
        version=version,
        supports_render=True,
        supports_stack_commands=True,
        supports_list=True,
        supports_find=True,
        supports_dag_graph=True,
    )
