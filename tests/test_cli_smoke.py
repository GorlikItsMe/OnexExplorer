"""
Verify the Windows/Linux binary runs far enough to execute Qt CLI code.

On Windows (WIN32 subsystem), ``--help`` often hangs or misbehaves under
``subprocess``; instead we assert a fast error path: ``--cli`` with a missing
input file exits with ``Cli::CannotOpenInput`` (3). On Unix, ``--help`` is used.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from tests.conftest import ONEX_BIN, REPO_ROOT


@pytest.mark.timeout(60)
def test_cli_smoke_quick():
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")

    if sys.platform == "win32":
        target = REPO_ROOT / ".cache" / "cli_smoke_target"
        target.mkdir(parents=True, exist_ok=True)
        missing = REPO_ROOT / "__nonexistent_cli_smoke__.nos"
        try:
            p = subprocess.run(
                [
                    str(ONEX_BIN),
                    "--cli",
                    "--unpack",
                    str(missing),
                    "--target",
                    str(target),
                ],
                cwd=REPO_ROOT,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
        except subprocess.TimeoutExpired as exc:
            pytest.fail(
                f"OnexExplorer CLI smoke exceeded 30s: {exc}"
            )
        # Cli::CannotOpenInput — see Source/cli.h
        assert p.returncode == 3, f"expected CannotOpenInput exit 3, got {p.returncode}"
        return

    try:
        p = subprocess.run(
            [str(ONEX_BIN), "--help"],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(
            "OnexExplorer --help exceeded 30s. "
            f"Captured:\n{getattr(exc, 'stdout', None) or ''}"
        )
    assert p.returncode == 0, p.stdout or ""
    out = (p.stdout or "").lower()
    if out.strip():
        assert "--cli" in out or "cli" in out, out[:800]
