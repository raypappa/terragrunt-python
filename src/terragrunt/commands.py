from collections.abc import Iterable
from pathlib import Path


def flag(name: str, value: str | Path | None) -> tuple[str, ...]:
    if value is None:
        return ()
    return (f"-{name}={value}",)


def repeated_flag(name: str, values: Iterable[str]) -> tuple[str, ...]:
    return tuple(f"-{name}={value}" for value in values)


def providers_lock_args(
    *,
    platforms: Iterable[str] = (),
    fs_mirror: str | Path | None = None,
    net_mirror: str | None = None,
    providers: Iterable[str] = (),
    extra_args: Iterable[str] = (),
) -> tuple[str, ...]:
    return (
        *repeated_flag("platform", platforms),
        *flag("fs-mirror", fs_mirror),
        *flag("net-mirror", net_mirror),
        *providers,
        *extra_args,
    )
