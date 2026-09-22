# Contributing

## Development

Install the locked development environment:

```shell
uv sync --locked
```

Run checks in this order:

```shell
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

Run executable integration tests explicitly when Terragrunt, OpenTofu, or
Terraform is installed locally:

```shell
uv run pytest -m integration
```

GitHub Actions also runs the Terragrunt integration tests once for every
version represented by a committed CLI fixture. The versioned workflow uses
`mise` to install the exact binary and derives its matrix from
`tests/fixtures/terragrunt-cli/`.

Integration tests skip missing or unrunnable executables. They use temporary
configurations, disable backend access, and do not create or modify
infrastructure.

## Maintaining Terragrunt Support

Terragrunt compatibility is maintained through release-note candidates, exact
versioned CLI inventories, compact fixtures, transition reports, capability
rules, and integration tests.

### Evaluate A New Release

1. Download the latest Terragrunt release notes:

   ```shell
   uv run python tools/download_release_notes.py
   ```

2. Select releases whose notes mention possible CLI changes:

   ```shell
   uv run python tools/release_candidates.py \
     --release-dir reference/terragrunt-releases \
     --output /tmp/terragrunt-release-candidates.json
   ```

3. Generate inventories for each candidate and its immediately preceding
   release:

   ```shell
   uv run python tools/terragrunt_inventory.py \
     --candidate-file /tmp/terragrunt-release-candidates.json \
     --compact-output-dir tests/fixtures/terragrunt-cli
   ```

   Existing inventories are reused. Use `--refresh` when an inventory must be
   regenerated.

4. Scan adjacent compact fixtures for changes:

   ```shell
   uv run python tools/terragrunt_transitions.py \
     --fixture-dir tests/fixtures/terragrunt-cli \
     --output /tmp/terragrunt-transitions.json
   ```

5. Confirm reported changes against the exact versioned binary:

   ```shell
   mise exec terragrunt@1.1.0 -- terragrunt --version
   mise exec terragrunt@1.1.0 -- terragrunt <command> --help
   ```

   Release notes select candidates. Exact binary help and compact inventories
   confirm observable CLI behavior.

### Decide Whether Code Changes Are Needed

Update this project when at least one of these is true:

- An existing typed command changes, is renamed, or is removed.
- A capability introduction or removal boundary changes.
- A new stable Terragrunt-specific command should have a typed method.
- A typed command needs support for new flags.
- The release is newer than `LATEST_TESTED_VERSION`.

A release usually does not require a library change when it only contains
internal bug fixes, documentation changes, dependency updates, or commands
that callers can already invoke through `client.run(...)` without a typed
wrapper.

### Update The Wrapper

When support changes:

- Update capability rules in `src/terragrunt/capabilities.py`.
- Update `LATEST_TESTED_VERSION` when the release has been verified.
- Add or update compact fixtures under `tests/fixtures/terragrunt-cli/`.
- Add typed methods in `src/terragrunt/client.py` only when the command has a
  stable and useful Python interface.
- Preserve argument-list forwarding, output handling, timeouts, and `check`.
- Add command-construction tests in `tests/terragrunt/test_client.py`.
- Add or update capability boundary tests.
- Add safe integration coverage in `tests/terragrunt/test_integration.py`.
- Run capability verification:

  ```shell
  uv run python tools/verify_capabilities.py
  ```

### Validate Changes

```shell
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
uv run pytest -m integration
```

Keep commits focused and use Conventional Commit messages with a non-empty
body.

## Inventory Tooling

See [docs/terragrunt-command-inventories.md](docs/terragrunt-command-inventories.md)
for the inventory schema, generated output locations, comparison reports, and
tool command reference.

## Release

`uv build` creates distribution artifacts. A `v*.*.*` tag triggers the PyPI
publish workflow. Update `[project].version` in `pyproject.toml` before tagging.
