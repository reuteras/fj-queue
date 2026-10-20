# Configuration

## Precedence

For each setting, the highest-precedence source wins:

1. CLI flag
2. Environment variable
3. Config file
4. Built-in default (where one exists)

## Settings reference

| Setting | Flag | Env var | Config key | Default |
|---|---|---|---|---|
| Forgejo host | `--host HOST` | `$FORGEJO_HOST` | `host` | none (required) |
| API token | - | `$FORGEJO_TOKEN` | `token_ref` (1Password reference only) | none (required) |
| Config file path | `--config PATH` | - | - | (auto-discovered) |
| Output format | `--format {rich,plain,json}` | - | - | `rich` |
| Run mode | `--mode {watch,once}` | - | - | `watch` at TTY, `once` when piped |
| Poll interval | `--interval SECONDS` | - | - | `2.0` |
| Request timeout | `--timeout SECONDS` | - | - | `10.0` |
| Repo filter | `--repo OWNER/REPO` | - | - | (none) |
| Label filter | `--label LABEL` | - | - | (none) |
| Metrics enabled | `--metrics` / `--no-metrics` | - | `[metrics] enabled` | `false` |
| Metrics URL | `--metrics-url URL` | `$FJ_QUEUE_METRICS_URL` | `[metrics] url` | none (required when metrics or ncps on) |
| Metrics namespace | `--metrics-namespace NS` | - | `[metrics] namespace` | `ci-runners` |
| Node prefix | `--node-prefix PREFIX` | - | `[metrics] node_prefix` | (empty, no filter) |
| NCPS enabled | `--ncps` / `--no-ncps` | - | `[ncps] enabled` | `false` |

## Config file format

The config file uses [TOML](https://toml.io/) and is parsed with the stdlib
`tomllib` (no extra dependency). The **API token itself is never read from or
written to the config file** (a `token` key is ignored). Use `$FORGEJO_TOKEN`,
or `token_ref` to reference a secret stored in 1Password.

```toml
host = "git.example.com"
token_ref = "op://Private/Forgejo admin token/credential"

[metrics]
enabled = true
url = "https://prometheus.example.com"
namespace = "ci-runners"
node_prefix = "k8s-node-"

[ncps]
enabled = true
```

See [`config.toml.example`](../config.toml.example) at the repo root for a
fully annotated template.

## Config file discovery

If `--config PATH` is not given, fj-queue looks for a config file in this
order (first found wins):

1. `$XDG_CONFIG_HOME/fj-queue/config.toml`
2. `~/.config/fj-queue/config.toml` (fallback when `$XDG_CONFIG_HOME` is
   unset)

If none is found, only CLI flags and environment variables apply.

A `./fj-queue.toml` in the current directory is **not** loaded
automatically. The config file sets `host`, and the admin token from
`$FORGEJO_TOKEN` is sent to that host, so auto-loading a file from
whatever directory you happen to be in (for example a freshly cloned
repository) could hand your token to a third party. To use a local file,
pass it explicitly: `--config ./fj-queue.toml`.

## Required settings

**Host** (`--host` / `$FORGEJO_HOST` / `host` in config) is required. If it
is not provided by any source, fj-queue exits 2 with guidance pointing at the
three resolution paths.

**Token** is required for all API calls and must have admin scope. It is
resolved in this order:

1. `$FORGEJO_TOKEN`
2. `token_ref` in the config file: a 1Password
   [secret reference](https://developer.1password.com/docs/cli/secret-references/)
   (`op://<vault>/<item>/<field>`), read with `op read --no-newline` (no
   shell; 30 s timeout so a Touch ID prompt can be answered). The value must
   start with `op://`. If `op` is missing, not signed in, or returns nothing,
   fj-queue exits 2. `op` is not invoked at all when `$FORGEJO_TOKEN` is set.

There is no `--token` flag: command-line arguments are visible to other
local users via `ps`.

Because `token_ref` lets the config file trigger `op read` and send the
result to the configured `host`, only use config files you control. This is
why `./fj-queue.toml` is never auto-loaded.

## Opt-in features: metrics and NCPS

Per-pod runner CPU/memory metrics and NCPS cache-status display are both **off
by default**. Enable them independently:

```bash
# Enable metrics for one run
uv run fj_queue.py --host git.example.com --metrics --metrics-url https://prometheus.example.com

# Enable NCPS for one run
uv run fj_queue.py --host git.example.com --ncps --metrics-url https://prometheus.example.com

# Enable both for one run
uv run fj_queue.py --host git.example.com --metrics --ncps --metrics-url https://prometheus.example.com
```

Or set them persistently in the config file (see above).

**A Prometheus URL is required whenever metrics or NCPS is enabled.** Enabling
either feature without a URL exits 2. There is no built-in default URL.

See [Metrics and NCPS](metrics-ncps.md) for what these features show and how
they work.

## `--no-metrics` and `--no-ncps`

These flags explicitly disable the features, overriding any config-file
setting. They are redundant with the default-off behavior but useful in
scripts that need to guarantee a feature is off regardless of the local
config file.
