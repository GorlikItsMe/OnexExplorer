"""
Fast check that the binary starts and the Qt CLI/parser path runs.

On Windows (WIN32 subsystem), avoid subprocess.PIPE — GUI apps often stall or
deadlock pipe readers. Use DEVNULL and assert only exit code.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from tests.conftest import ONEX_BIN, REPO_ROOT


@pytest.mark.timeout(60)
def test_cli_help_exits_zero():
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    kwargs = {
        "cwd": REPO_ROOT,
        "env": env,
        "timeout": 30,
    }
    if sys.platform == "win32":
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
        kwargs["text"] = True
    else:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.STDOUT
        kwargs["text"] = True

    try:
        p = subprocess.run([str(ONEX_BIN), "--help"], **kwargs)
    except subprocess.TimeoutExpired as exc:
        pytest.fail(
            "OnexExplorer --help exceeded 30s (likely stuck during Qt/DLL init or process hang). "
            "Captured output:\n"
            f"{getattr(exc, 'stdout', None) or ''}"
        )

    assert p.returncode == 0, (
        p.stdout if hasattr(p, "stdout") and p.stdout else "(no captured stdout/stderr)"
    )

    if sys.platform != "win32":
        out = (p.stdout or "").lower()
        if out.strip():
            assert "--cli" in out or "cli" in out, out[:800]
