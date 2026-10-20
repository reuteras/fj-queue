# Installation

## Requirements

- **Python 3.11 or newer.**
- **[`uv`](https://docs.astral.sh/uv/)** installed on the host (including any
  agent host that shells out to `fj_queue.py`). Runtime libraries (`rich`,
  `httpx`) are declared in a PEP-723 inline header; `uv run` resolves and
  caches them on first invocation. No manual venv or `pip install` needed.
- **An admin-scoped Forgejo API token.** The dashboard talks to
  `/api/v1/admin/actions/runners` and `/api/v1/admin/actions/runners/jobs`,
  which require `is_admin: true`. A non-admin token returns HTTP 403 and the
  tool exits 3.

## Running from a checkout

Clone or copy `fj_queue.py` to any directory, then:

```bash
uv run fj_queue.py --host git.example.com
```

Or use the bundled `fj-queue` symlink (if you cloned the full repo):

```bash
./fj-queue --host git.example.com
```

Both forms are equivalent. The symlink calls `uv run fj_queue.py` under the
hood.

## Token setup

There is no `--token` flag (command-line arguments are visible to every
local user via `ps`). Use one of:

**1Password** (recommended for interactive use). Store the token in
1Password, install the [1Password CLI](https://developer.1password.com/docs/cli/)
(`op`), and reference the secret from your config file
(`~/.config/fj-queue/config.toml`):

```toml
host = "git.example.com"
token_ref = "op://Private/Forgejo admin token/credential"
```

fj-queue runs `op read` once at startup; with the 1Password desktop app
integration this prompts for Touch ID / your password.

**Environment variable** (recommended for scripts and CI; takes precedence
over `token_ref`):

```bash
export FORGEJO_TOKEN=<your-token>
uv run fj_queue.py --host git.example.com
```

The token itself is never read from a config file. See
[Configuration](configuration.md) for the full precedence rules.
