# Terragrunt Python

`terragrunt-python` is a typed Python wrapper for running Terragrunt,
OpenTofu, and Terraform executables. It keeps subprocess execution, executable
discovery, version checks, capability checks, output handling, and common
infrastructure commands in one small API.

The library is useful when Python code needs to orchestrate infrastructure
commands without depending on an unstable Go or Terragrunt internal API.

## Features

- Select Terragrunt, OpenTofu, or Terraform with a typed `Executable` enum.
- Resolve executables by name through `PATH` or use an explicit executable path.
- Stream command output by default, with capture mode available per client or call.
- Raise a `TerragruntError` for failed commands with the `CommandResult` in `.resp`.
- Configure the working directory, environment, output streams, and timeout.
- Check Terragrunt capabilities against the installed version.
- Reject Terragrunt versions older than `0.73.7`.
- Warn when the installed Terragrunt version is newer than the tested version.
- Run provider lock operations with platform and mirror options.
- Use `run(...)` as an escape hatch for commands not yet represented by a typed method.

## Prerequisites

Install the following tools before using the library:

- [Python](https://www.python.org/) 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- At least one supported executable:
  - [Terragrunt](https://terragrunt.gruntwork.io/docs/getting-started/install/)
  - [OpenTofu](https://opentofu.org/docs/intro/install/)
  - [Terraform](https://developer.hashicorp.com/terraform/install)

Verify the tools you plan to use:

```shell
python --version
uv --version
terragrunt --version
```

Replace `terragrunt --version` with `tofu --version` or `terraform --version`
when using another executable.

## Installation

Install the package from a checked-out copy with `uv`:

```shell
uv sync
```

For an application that consumes this package, install it from the package
index after it is published:

```shell
uv add terragrunt-python
```

The project does not currently have a configured Git remote. Once a remote is
assigned, clone it with the repository's URL and then run `uv sync`.

## Quick Start

The client resolves `terragrunt` through `PATH`, checks its version, and
streams command output to the process's standard streams:

```python
from terragrunt import TerragruntClient


client = TerragruntClient(working_dir="infrastructure/dev")
client.init()
client.plan()
```

Use an explicit executable path when the binary is not on `PATH`:

```python
from pathlib import Path

from terragrunt import Executable, TerragruntClient


client = TerragruntClient(
    executable=Path("/opt/tools/terragrunt"),
    working_dir=Path("infrastructure/prod"),
)
```

Select OpenTofu or Terraform with the typed enum:

```python
from terragrunt import Executable, TerragruntClient


tofu = TerragruntClient(executable=Executable.OPENTOFU)
terraform = TerragruntClient(executable=Executable.TERRAFORM)

tofu.plan()
terraform.output("-raw", "instance_ip")
```

The common typed methods are `init`, `plan`, `apply`, `destroy`, `output`, and
`providers_lock`. Terragrunt-specific methods include `render`, `list`, `find`,
`stack_run`, and `dag_graph`.

## Output Handling

Commands stream output by default. Set the client-wide mode to capture output
instead:

```python
from terragrunt import OutputMode, TerragruntClient


client = TerragruntClient(output_mode=OutputMode.CAPTURE)
result = client.plan()

print(result.stdout)
print(result.stderr)
```

Override the mode for one command without changing the client default:

```python
result = client.plan(output_mode=OutputMode.CAPTURE)
```

Every successful command returns a `CommandResult` containing `args`,
`returncode`, `stdout`, and `stderr`.

## Errors

Non-zero exit codes raise `TerragruntError`. The failed command result is
available as `error.resp`:

```python
from terragrunt import TerragruntClient, TerragruntError


try:
    TerragruntClient().plan()
except TerragruntError as error:
    if error.resp is not None:
        print(error.resp.returncode)
        print(error.resp.stderr)
```

Pass `check=False` when a caller needs to inspect a failure without raising:

```python
result = client.run("validate", check=False)
if not result.succeeded:
    print(result.stderr)
```

## Provider Locking

`providers_lock` supports the common provider lock options and accepts extra
arguments for CLI features that are not yet modeled by the library:

```python
from pathlib import Path


result = client.providers_lock(
    platforms=["darwin_arm64", "linux_amd64"],
    fs_mirror=Path("/opt/provider-mirror"),
    providers=["registry.terraform.io/hashicorp/aws"],
    extra_args=["-var-file=dev.tfvars"],
)
```

This produces the equivalent of:

```shell
terragrunt providers lock \
  -platform=darwin_arm64 \
  -platform=linux_amd64 \
  -fs-mirror=/opt/provider-mirror \
  registry.terraform.io/hashicorp/aws \
  -var-file=dev.tfvars
```

## Compatibility

The initial compatibility baseline is Terragrunt `0.73.7`.

- Older Terragrunt versions raise `TerragruntVersionError` during client setup.
- Newer Terragrunt versions emit a warning because they have not been tested.
- OpenTofu and Terraform use their own versioning and are not subject to the
  Terragrunt `0.73.7` minimum.
- `run(...)` remains available for commands that are not covered by a typed
  method.

## Development

Install the locked development environment:

```shell
uv sync
```

Run the same checks used by GitHub Actions:

```shell
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

Tests use pytest and mirror the source package under `tests/terragrunt/`.
Coverage is reported automatically by the pytest configuration.

## Terragrunt Command Inventories

Use the repository tooling to inspect the command tree for exact Terragrunt
versions. `mise` downloads the requested binary and runs it without changing
the active project tool configuration:

```shell
uv run python tools/terragrunt_inventory.py 0.73.7 0.90.0 1.0.2
```

The default depth of two captures top-level commands and their subcommands.
Use `--max-depth 1` when only the top-level command set is needed.

Full inventories are written to ignored `reference/terragrunt-commands/`
JSON files. Each command includes its canonical path, aliases, summary, and
raw version-specific help text. Write compact normalized inventories for
committed fixtures with:

```shell
uv run python tools/terragrunt_inventory.py 0.73.7 0.90.0 \
  --compact-output-dir tests/fixtures/terragrunt-cli
```

Compact fixtures contain stable command paths, aliases, categories, parsed
flags, and help hashes. Raw help remains generated data and is not committed.

Release notes are downloaded into ignored `reference/terragrunt-releases/`:

```shell
uv run python tools/download_release_notes.py
```

Find release-note candidates for command inventory review:

```shell
uv run python tools/release_candidates.py \
  --release-dir reference/terragrunt-releases \
  --output /tmp/terragrunt-release-candidates.json
```

The candidate report is deterministic and includes matched keywords, matched
command names, and the immediately preceding release version. Release notes
select candidates; exact binary inventories remain the source of truth for
confirming CLI transitions.

Compare two generated inventories:

```shell
uv run python tools/terragrunt_inventory.py --compare \
  tests/fixtures/terragrunt-cli/v0.73.7.json \
  tests/fixtures/terragrunt-cli/v0.90.0.json
```

## Releases

Pushing a tag matching `v*.*.*` runs the checks and publishes the package to
[PyPI](https://pypi.org/project/terragrunt-python/) using GitHub Actions and
PyPI trusted publishing. No PyPI token is stored in GitHub Actions.

Before the first release, configure a PyPI trusted publisher for this GitHub
repository with:

- Owner and repository name
- Workflow filename: `.github/workflows/publish.yml`
- Environment name: `pypi`

Then create and push a version tag after updating the version in
`pyproject.toml`:

```shell
git tag v0.1.0
git push origin v0.1.0
```

Run the executable integration tests explicitly when Terragrunt, OpenTofu, or
Terraform is installed locally:

```shell
uv run pytest -m integration
```

The integration tests skip executables that are not installed. They use a
temporary directory with a minimal configuration, disable backend access, and
only run version, initialization, and no-change plan commands. They do not
create or modify infrastructure.

## Project Layout

```text
src/terragrunt/       Library source
tests/terragrunt/     Mirrored pytest suite
pyproject.toml        Project metadata and tool configuration
.github/workflows/    GitHub Actions checks
```

## Contributing

Bug reports, feature requests, and merge requests are welcome once the project
remote and issue tracker are configured.

Before opening a merge request:

1. Add or update tests for behavior changes.
2. Run all four development checks locally.
3. Update this README when public APIs or supported commands change.
4. Keep command arguments as argument lists rather than shell strings.

## License

This project is licensed under the [MIT License](LICENSE).
