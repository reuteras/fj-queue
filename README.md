# fj-queue

A read-only Forgejo Actions runner and CI queue dashboard.

[![CI](https://github.com/reuteras/fj-queue/actions/workflows/test.yml/badge.svg)](https://github.com/reuteras/fj-queue/actions/workflows/test.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![fj-queue](docs/img/hero.png)

Polls the Forgejo admin Actions API and renders runner inventory, queue totals,
per-repo backlog, a FIFO-approximate queue order, and structured warnings for
unschedulable jobs and possibly wedged workflow_call sentinels (forgejo#12127,
see [Caveats](docs/caveats.md#wedged-sentinel-detection-is-heuristic)).
Designed for two audiences:

- **Humans**: a live, in-place refreshing terminal UI (Rich) so an operator
  can see at a glance whether CI is saturated.
- **Agents**: a stable, byte-deterministic JSON document (`--format json`)
  backed by a committed JSON Schema, so scripts can branch on global
  saturation, a repo's queue position, and structured `blocked_reason` /
  `warnings` fields.

## Quick Start

Clone the repository and run it with [`uv`](https://docs.astral.sh/uv/),
which resolves the dependencies on first run (`./fj-queue` is a symlink to
`fj_queue.py`):

```bash
# Single snapshot
uv run fj_queue.py --host git.example.com

# Live dashboard (default at a TTY)
uv run fj_queue.py --host git.example.com --mode watch

# Agent: JSON output piped to jq
uv run fj_queue.py --host git.example.com --format json | jq '.totals'
```

Provide an **admin-scoped** Forgejo API token via `$FORGEJO_TOKEN`, or store
it in 1Password and point the config file at it with
`token_ref = "op://Vault/Item/field"` (read with the `op` CLI). A non-admin
token exits 3.

See [Installation](docs/installation.md) for requirements and token setup.

For persistent settings, create `~/.config/fj-queue/config.toml` (or pass
any file with `--config PATH`; `./fj-queue.toml` is not auto-loaded):

```toml
host = "git.example.com"

# Metrics and NCPS are OFF by default.
# Uncomment and supply a Prometheus URL to enable them.
# [metrics]
# enabled = true
# url = "https://prometheus.example.com"
# namespace = "ci-runners"
```

See [`config.toml.example`](config.toml.example) for the full format with
all supported keys.

## Documentation

| Document | Contents |
|---|---|
| [Installation](docs/installation.md) | Requirements, uv, token setup |
| [Configuration](docs/configuration.md) | Flags, env vars, config file, precedence, discovery |
| [Usage](docs/usage.md) | Formats, modes, filtering, exit codes, examples |
| [JSON contract](docs/json-contract.md) | Schema shape, ordering, stability guarantees |
| [Metrics and NCPS](docs/metrics-ncps.md) | Per-pod CPU/memory and NCPS cache status (opt-in) |
| [Caveats](docs/caveats.md) | FIFO approximation, blocked jobs, filter scope |

See also: [Homelab Adventures: fj-queue](https://hai.wxs.ro/custom-tools/fj-queue/) for the background and design notes.
