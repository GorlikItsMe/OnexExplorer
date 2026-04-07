"""
Fast check that the binary starts and the Qt CLI/parser path runs.

Uses subprocess.run(..., timeout=...) so a wedged or DLL-broken executable
fails here instead of hanging the whole session. (pytest-timeout can still
time out the *test thread*, but may not always tear down a stuck native child.)
"""

from __future__ import annotations

import os
import subprocess

import pytest

from tests.conftest import ONEX_BIN, REPO_ROOT


@pytest.mark.timeout(10)
def test_cli_help_exits_zero():
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        p = subprocess.run(
            [str(ONEX_BIN), "--help"],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(
            "OnexExplorer --help exceeded 5s (likely stuck during Qt/DLL init or process hang). "
            "Captured output:\n"
            f"{exc.stdout or ''}"
        )

    assert p.returncode == 0, p.stdout or "(no captured stdout/stderr)"
    out = (p.stdout or "").lower()
    if out.strip():
        assert "--cli" in out or "cli" in out, out[:800]
