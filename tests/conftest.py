"""Pytest config: make the sibling fj_queue.py importable from tests/."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _default_forgejo_token(monkeypatch):
    """fj-queue has no --token flag; the token comes from $FORGEJO_TOKEN
    (or a 1Password token_ref). Give every test a deterministic token so
    nothing depends on the developer's ambient environment; tests that
    exercise the missing-token path delenv it explicitly."""
    monkeypatch.setenv("FORGEJO_TOKEN", "tok")
