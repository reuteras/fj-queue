# fj-queue

A read-only Forgejo Actions runner and CI queue dashboard.

[![CI](https://github.com/reuteras/fj-queue/actions/workflows/test.yml/badge.svg)](https://github.com/reuteras/fj-queue/actions/workflows/test.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![fj-queue](docs/img/hero.png)

Polls the Forgejo admin Actions API and renders runner inventory, queue totals,
per-repo backlog, the jobs currently running, a FIFO-approximate queue order,
and structured warnings for unschedulable jobs and possibly wedged
workflow_call sentinels (forgejo#12127, see
[Caveats](docs/caveats.md#wedged-sentinel-detection-is-heuristic)).
Designed for two audiences:

- **Humans**: a live, in-place refreshing terminal UI (Rich), or plain text,
  so an operator can see at a glance whether CI is saturated and what is
  running right now.
- **Agents**: a stable, byte-deterministic JSON document (`--format json`)
  backed by a committed JSON Schema, so scripts can branch on global
  saturation, a repo's queue position, and structured `blocked_reason` /
  `warnings` fields.

This is a fork of [vtmocanu/fj-queue](https://github.com/vtmocanu/fj-queue).
See [Differences from upstream](#differences-from-upstream).

## Quick Start

Requirements: Python 3.11+, [`uv`](https://docs.astral.sh/uv/), an
admin-scoped Forgejo API token, and optionally the
[1Password CLI](https://developer.1password.com/docs/cli/) (`op`).

Run it straight from GitHub with `uvx`, without cloning:

```bash
# Latest commit on main (re-checked on every run)
uvx --from git+https://github.com/reuteras/fj-queue fj-queue --host git.example.com

# A specific commit (reproducible)
uvx --from git+https://github.com/reuteras/fj-queue@<commit-sha> fj-queue --host git.example.com
```

`uvx` installs the package into a cached, isolated environment; dependency
versions are resolved fresh there (`uv.lock` only applies to a checkout).

To have `fj-queue` available as a regular command on your `PATH`, install it
as a uv tool instead:

```bash
uv tool install git+https://github.com/reuteras/fj-queue
fj-queue --host git.example.com

# Later: pull the latest commit from main
uv tool upgrade fj-queue
```

Unlike `uvx`, an installed tool stays at the installed commit until you run
`uv tool upgrade`. Both ways ship the JSON Schema, so `fj-queue --schema`
works without a checkout.

Or clone the repository and run it from the checkout, which uses the
versions locked in `uv.lock`:

```bash
git clone https://github.com/reuteras/fj-queue.git
cd fj-queue

# Single snapshot
uv run fj_queue.py --host git.example.com

# Live dashboard (default at a TTY)
uv run fj_queue.py --host git.example.com --mode watch

# Agent: JSON output piped to jq
uv run fj_queue.py --host git.example.com --format json | jq '.totals'
```

`uv` resolves the dependencies on first run; `./fj-queue` is a symlink to
`fj_queue.py`.

## Token

There is no `--token` flag (command-line arguments are visible to other local
users via `ps`). The token is resolved in this order:

1. `$FORGEJO_TOKEN`
2. `token_ref` in the config file: a 1Password secret reference
   (`op://<vault>/<item>/<field>`), read with `op read` at startup.

A non-admin token exits 3. See [Installation](docs/installation.md) and
[Configuration](docs/configuration.md) for details.

## Configuration

Put persistent settings in `~/.config/fj-queue/config.toml` (or pass any file
with `--config PATH`; `./fj-queue.toml` is deliberately not auto-loaded):

```toml
host = "git.example.com"
token_ref = "op://Private/Forgejo admin token/credential"

# Metrics and NCPS are OFF by default.
# Uncomment and supply a Prometheus URL to enable them.
# [metrics]
# enabled = true
# url = "https://prometheus.example.com"
# namespace = "ci-runners"
```

See [`config.toml.example`](config.toml.example) for all supported keys.

## Documentation

| Document | Contents |
|---|---|
| [Installation](docs/installation.md) | Requirements, uv, token setup |
| [Configuration](docs/configuration.md) | Flags, env vars, config file, precedence, discovery |
| [Usage](docs/usage.md) | Formats, modes, filtering, exit codes, examples |
| [JSON contract](docs/json-contract.md) | Schema shape, ordering, stability guarantees |
| [Metrics and NCPS](docs/metrics-ncps.md) | Per-pod CPU/memory and NCPS cache status (opt-in) |
| [Caveats](docs/caveats.md) | FIFO approximation, blocked jobs, filter scope |

## Development

```bash
uv sync --group dev
uv run --frozen --group dev pytest tests/
uv run --frozen --group dev ruff check .
uv run --frozen --group dev ruff format --check .
uv run --frozen --group dev mypy fj_queue.py tests
pre-commit run --all-files
```

CI runs the test suite on Python 3.11 to 3.13 plus ruff and mypy, super-linter
(including Trivy and gitleaks), and OSV-Scanner. Dependencies are updated by
Dependabot; `uv.lock` holds the exact versions.

## Differences from upstream

- **Running jobs** are shown in the human views (a `Running` table in rich, a
  `RUNNING` section in plain). The JSON contract is unchanged.
- **No `--token` flag**; the token comes from `$FORGEJO_TOKEN` or a 1Password
  `token_ref`.
- **No `./fj-queue.toml` auto-discovery**, so a config file planted in a
  cloned repository cannot redirect your token to another host.
- **Untrusted text is sanitized**: job, runner, and repo names from the server
  can no longer inject Rich markup or terminal escape sequences.
- No Homebrew formula or release automation; run it from the checkout.

See [`CHANGELOG.md`](CHANGELOG.md) for details.

## Credits

Originally written by [vtmocanu](https://github.com/vtmocanu). See
[Homelab Adventures: fj-queue](https://hai.wxs.ro/custom-tools/fj-queue/) for
the background and design notes.
