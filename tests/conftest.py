"""Pytest config: make the sibling fj_queue.py importable from tests/."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _isolated_environment(monkeypatch, tmp_path_factory):
    """Keep every test independent of the developer's machine.

    - fj-queue has no --token flag; the token comes from $FORGEJO_TOKEN
      (or a 1Password token_ref). Give every test a deterministic token;
      tests that exercise the missing-token path delenv it explicitly.
    - Point $XDG_CONFIG_HOME at an empty directory so the developer's real
      ~/.config/fj-queue/config.toml (which may hold a token_ref and make
      a test invoke the real `op` CLI) is never auto-discovered. Tests
      that exercise discovery set their own XDG_CONFIG_HOME.
    """
    monkeypatch.setenv("FORGEJO_TOKEN", "tok")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("xdg")))
