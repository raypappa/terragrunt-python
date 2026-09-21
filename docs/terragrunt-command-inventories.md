# Terragrunt Command Inventories

The repository uses exact Terragrunt binaries to discover CLI behavior. `mise`
downloads the requested version and runs it without changing the active project
tool configuration.

## Generated Data

Full inventories are written to the ignored directory:

```text
reference/terragrunt-commands/
```

They contain raw version-specific help text and are intended for local review.

Compact normalized inventories are committed as test fixtures:

```text
tests/fixtures/terragrunt-cli/
```

Compact fixtures contain:

- `schema_version`
- Terragrunt `version`
- Command paths
- Aliases
- Categories
- Command kind
- Summaries
- Parsed flag metadata
- SHA-256 hashes of raw help text

Release notes are generated locally under:

```text
reference/terragrunt-releases/
```

Neither full inventories nor downloaded release notes are committed.

## Commands

Before running commands that may download Terragrunt releases, configure
`mise` to authenticate GitHub API requests:

```shell
export MISE_GITHUB_TOKEN=$(gh auth token)
```

Download release notes:

```shell
uv run python tools/download_release_notes.py
```

Generate inventories for explicit versions:

```shell
uv run python tools/terragrunt_inventory.py 0.73.7 0.90.0 1.0.2
```

Limit command discovery to top-level commands:

```shell
uv run python tools/terragrunt_inventory.py 1.0.2 --max-depth 1
```

Write compact fixtures:

```shell
uv run python tools/terragrunt_inventory.py 0.73.7 0.90.0 \
  --compact-output-dir tests/fixtures/terragrunt-cli
```

Generate inventories for release-note candidates and their predecessors:

```shell
uv run python tools/terragrunt_inventory.py \
  --candidate-file /tmp/terragrunt-release-candidates.json \
  --compact-output-dir tests/fixtures/terragrunt-cli
```

Candidate-file generation excludes releases before the supported `0.73.7`
baseline. Explicit versions passed as positional arguments are not filtered.

Existing output files are reused. Use `--refresh` to regenerate them.

Find release-note candidates:

```shell
uv run python tools/release_candidates.py \
  --release-dir reference/terragrunt-releases \
  --output /tmp/terragrunt-release-candidates.json
```

Compare two compact inventories:

```shell
uv run python tools/terragrunt_inventory.py --compare \
  tests/fixtures/terragrunt-cli/v0.73.7.json \
  tests/fixtures/terragrunt-cli/v0.90.0.json
```

The report identifies:

- Added and removed command paths
- Added and removed aliases
- Changed category, kind, or summary metadata
- Added and removed flags
- Changed flag metadata

Scan all adjacent fixtures:

```shell
uv run python tools/terragrunt_transitions.py \
  --fixture-dir tests/fixtures/terragrunt-cli \
  --output /tmp/terragrunt-transitions.json
```

Restrict the transition range:

```shell
uv run python tools/terragrunt_transitions.py \
  --fixture-dir tests/fixtures/terragrunt-cli \
  --from-version 0.73.7 \
  --to-version 1.0.2
```

Verify capability rules against fixtures:

```shell
uv run python tools/verify_capabilities.py
```

## Source Of Truth

Release notes select versions for review, but they do not establish CLI
behavior. The exact binary is authoritative:

```shell
mise exec terragrunt@1.1.0 -- terragrunt --version
mise exec terragrunt@1.1.0 -- terragrunt --help
mise exec terragrunt@1.1.0 -- terragrunt stack --help
```

The generated compact fixture records the observed command tree in a stable
form that can be compared and tested without invoking an LLM.
