# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`fj-queue` is a read-only dashboard for the Forgejo admin Actions API. It polls runners + queued/running jobs and renders them two ways: a live Rich TUI / plain text for humans, and a byte-deterministic JSON document (backed by a committed JSON Schema) for agents/scripts.

This checkout is a **personal fork**: `github.com/reuteras/fj-queue` (`origin`), forked from `github.com/vtmocanu/fj-queue`. Work happens directly on `main` of the fork. It is hosted on GitHub, so use `gh` (not `tea`). There is no `upstream` remote configured; add one (`git remote add upstream https://github.com/vtmocanu/fj-queue`) only when explicitly syncing from upstream.

The fork has diverged from upstream in user-visible ways (see `CHANGELOG.md` `[Unreleased]`): a Running-jobs section in the human renderers, no `--token` flag, 1Password `token_ref` support, no `./fj-queue.toml` auto-discovery, and sanitizing of server-supplied strings. Don't reintroduce upstream behavior for these when syncing.

## Running it

Run from the checkout with `uv`, or straight from GitHub with `uvx --from git+https://github.com/reuteras/fj-queue fj-queue ...` (console script `fj-queue = "fj_queue:cli"` in `pyproject.toml`; the JSON schema ships as a wheel data file under `share/fj-queue/schema/`, and `load_schema` checks the checkout path first, then `sys.prefix`). There is no Homebrew install or tagged release in this fork.

```bash
uv run fj_queue.py --host git.example.com              # or ./fj-queue (symlink)
uv run fj_queue.py --host git.example.com --mode watch
uv run fj_queue.py --host git.example.com --format json | jq .totals
```

Token sources, in order: `$FORGEJO_TOKEN`, then `token_ref = "op://Vault/Item/field"` in the config file (resolved with the 1Password CLI `op read --no-newline`). There is deliberately **no `--token` flag** (argv is visible via `ps`). Config file discovery: `--config PATH` > `$XDG_CONFIG_HOME/fj-queue/config.toml` > `~/.config/fj-queue/config.toml`. A `./fj-queue.toml` in the cwd is **not** auto-loaded (security: the config sets `host`, which receives the token).

## Commands

```bash
uv sync --group dev                              # install dev deps
uv run --frozen --group dev pytest tests/        # full suite (mirrors CI exactly)
uv run --group dev pytest tests/test_render.py   # one file
uv run --group dev pytest -k watch               # by keyword
uv run --group dev pytest --snapshot-update      # regenerate syrupy snapshots after intentional render changes
uv run --frozen --group dev ruff check .        # lint (same as CI)
uv run --frozen --group dev ruff format --check .
uv run --frozen --group dev mypy fj_queue.py tests
pre-commit run --all-files                       # ruff check + format, mypy, betterleaks, markdownlint
```

ruff and mypy are in the `dev` dependency group, so their versions come from `uv.lock` (pre-commit runs them through `uv run` too). Never run linters at `@latest`. Markdown style is configured in `.markdownlint.json` (shared by pre-commit and super-linter).

## CI (GitHub Actions)

- `test.yml`: `pytest` on Python 3.11/3.12/3.13/3.14/3.15 with `uv run --frozen`, plus a `lint` job (ruff check, ruff format --check, mypy). Keep `uv.lock` in sync with `pyproject.toml`.
- `linter.yml`: super-linter (slim). Includes Trivy (fails on known CVEs in `uv.lock`), yamllint, zizmor/actionlint for workflows, gitleaks, checkov. Ruff/mypy are disabled there.
- `osv-scanner.yml`: OSV-Scanner on push to `main` + nightly, config in `.osv-scanner.toml`; results go to the Security tab.

All actions are pinned by commit SHA with a version comment; keep it that way. After pushing, check runs with `gh run list -R reuteras/fj-queue` and `gh run view <id> --log-failed`.

## Dependencies

Updates come from **Dependabot** (`.github/dependabot.yml`): grouped weekly PRs for GitHub Actions and pre-commit hooks, daily for `uv`, all with a 7-day cooldown.

`pyproject.toml` lists dependencies without versions; **`uv.lock` is the source of truth** for versions. When adding or bumping a package, check its release date and pick a version at least two weeks old (e.g. `uv lock -P 'pkg==X.Y.Z'`), including new transitive deps. The PEP-723 header at the top of `fj_queue.py` pins `httpx`/`rich` separately for standalone `uv run --script` use; keep it in agreement with `uv.lock`. Prefer stdlib over new dependencies (e.g. 1Password is called via `subprocess` on the `op` CLI, not an SDK). Transitive vulnerabilities (Trivy/OSV findings, e.g. `anyio` via httpx) are fixed by bumping the locked version in `uv.lock`.

## Architecture

Everything lives in one file, **`fj_queue.py`** (~3500 lines). It is both an importable module and a PEP-723 self-contained script (`#!/usr/bin/env -S uv run --script`). It is organized into strict layers, marked `M1`..`M6` in section-header comments, and the layering is load-bearing:

- **Config + resolution** (`Config` frozen dataclass; `resolve_token` / `resolve_host` / `resolve_metrics_url` / `load_file_config`). Precedence is **CLI flag > env var > config file > built-in default**. Hard rules: no private host/URL ships as a default (omitting a required one exits 2); a literal `token` key in a config file is dropped, only a 1Password `token_ref` is accepted; `op` is only invoked when `$FORGEJO_TOKEN` is unset.
- **`Client` (M1)**: the *only* layer that knows Forgejo URL paths and field names. Raw field names are mapped to stable internal names on frozen dataclasses (`Runner`, `RawJob`) here and nowhere else. **All server-supplied strings pass through `_safe_text`** (replaces C0/C1 control and bidi characters) at this boundary; keep that for any new field. `fetch_runners` pages via the RFC-5988 `Link` header (same-host enforcement, hard page cap); `fetch_jobs` is a single call; `resolve_repo` is per-process cached.
- **Metrics + NCPS clients**: separate no-auth httpx client hitting Prometheus. Opt-in (OFF by default), graceful degradation via `error`/`*_error` fields.
- **`aggregate()` (M2)**: **pure: no I/O, no module state, clock is injected**. Turns runners + jobs into a `Snapshot` (`queue` = waiting jobs, `running` = running jobs). Correctness anchors live in comments here: per-runner *superset* label matching, `online = active|idle`, FIFO-approximate ordering, `needs`-gated jobs excluded from `unschedulable`.
- **JSON layer (M3)**: `to_dict` / `render_json` / `render_json_error`. Output must stay byte-deterministic. `schema/fj-queue.v1.json` is the committed contract; `schema_version` (wire) is distinct from `__version__` (tool). `Snapshot.running` is intentionally **not** on the wire.
- **Renderers (M4)**: `render_plain` and `render_rich`, consuming a `Snapshot` only. In `render_rich`, **pass server-derived cells as `rich.text.Text`, never bare `str`** (bare strings are parsed as Rich markup: spoofing, and `[/x]` crashes watch mode). Rich render changes ripple into syrupy snapshots.
- **Watch loop (M5)**: `run_watch`, `rich.live.Live(screen=True)`; fetch fn, sleep, and clock are injectable.
- **CLI (M6)**: `_build_parser` / `main`, argparse + stdlib only. `--repo` / `--label` scope `queue` and `running`; totals/per_repo/runners/warnings stay instance-wide.

Data flow: `Config → Client.fetch_* → aggregate() → Snapshot → {render_json | render_plain | render_rich}`.

## Conventions that bite

- **Exit codes are contract.** Typed `FjQueueError` subclasses carry the exit code: 2 config/usage, 3 auth (non-admin token), 4 connection, 5 schema drift; 0 success; 130 on Ctrl-C. Don't invent new bare `sys.exit` codes.
- **Tokens are scrubbed** from error output (`_scrub_token`). Keep that path intact when adding error messages; never echo `op` output on success.
- Tests: `tests/conftest.py` (autouse) sets `FORGEJO_TOKEN=tok` and points `XDG_CONFIG_HOME` at an empty temp dir, so the developer's real `~/.config/fj-queue/config.toml` is never read; tests of the missing-token path `delenv` the token. Never call the real `op` in tests: inject `run=` / `which=` into `resolve_token`, or monkeypatch `fq.subprocess.run` / `fq.shutil.which`.
- Snapshot tests (`tests/__snapshots__/test_render.ambr`) use **syrupy**; HTTP is mocked with **respx**; the JSON contract is validated with **jsonschema**. `tests/test_no_env_leaks.py` fails CI on environment-specific literals in the repo.
- Version bumps: `__version__` in `fj_queue.py`, `version` in `pyproject.toml`, and a `CHANGELOG.md` entry, kept in lockstep. Bump `schema_version` *only* on a breaking JSON-contract change.

## Before committing

Run the full test suite and `pre-commit run --all-files`. For behavior changes, ask the user to try it against their Forgejo instance first (from the checkout: `uv run fj_queue.py --host <host> ...`) unless they've said to commit directly.
