# Agent Guidance

## Repository

- This is a single-package Python library; public package code is under `src/terragrunt/` and tests mirror it under `tests/terragrunt/`.
- The package wraps subprocess execution for Terragrunt, OpenTofu, and Terraform. Keep command arguments as argument lists; do not build shell command strings.
- The supported Python version is 3.12 or newer. Use the checked-in `uv.lock` for dependency resolution.

## Development

- Set up or refresh the environment with `uv sync --locked`.
- Run checks in this order: `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check`, then `uv run pytest`.
- `pytest` is configured with coverage reporting by default; use a focused path such as `uv run pytest tests/terragrunt/test_runner.py` for targeted work.
- Integration tests are marked `integration` and discover `terragrunt`, `tofu`, and `terraform` on `PATH`; missing or unrunnable executables are skipped. Run them explicitly with `uv run pytest -m integration`.
- Integration tests use temporary configurations, disable backend access, and only perform version, initialization, and no-change plan operations.

## Implementation Constraints

- `TerragruntClient` detects the selected executable version during construction. Terragrunt must be at least `0.73.7`; newer versions emit a warning, while OpenTofu and Terraform are not subject to that minimum.
- Output streams by default; use `OutputMode.CAPTURE` when tests or callers need `CommandResult.stdout` and `.stderr`.
- Failed commands raise `TerragruntError` by default and expose the failed `CommandResult` as `error.resp`; use `check=False` when failure inspection is intentional.
- Keep public exports in `src/terragrunt/__init__.py` aligned with the package API and update tests for public behavior changes.

## Release

- `uv build` creates the distribution artifacts. A `v*.*.*` tag triggers the PyPI publish workflow, so update `[project].version` in `pyproject.toml` before tagging.

## Commits

- Always use Conventional Commits for commit messages, such as `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, or `chore:`.
- Always include a non-empty commit body describing what changed and why it changed; separate the subject and body with a blank line.
- Keep commits focused on one logical change; split unrelated files or hunks into separate commits when appropriate.
