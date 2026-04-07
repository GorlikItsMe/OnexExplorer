import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import pytest
import requests

from tests.gfpatcher import GfPatcher


GameFileDownloader = Callable[[str], Path]
UnpackGameArchive = Callable[[str], Path]


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = Path(os.environ.get("ONEX_BUILD_DIR", REPO_ROOT / "build"))


def _default_onex_bin() -> Path:
    """CMake emits OnexExplorer.exe on Windows and OnexExplorer on Unix-like systems."""
    no_ext = BUILD_DIR / "OnexExplorer"
    exe = BUILD_DIR / "OnexExplorer.exe"
    if sys.platform == "win32":
        for candidate in (exe, no_ext):
            if candidate.is_file():
                return candidate
        return exe
    for candidate in (no_ext, exe):
        if candidate.is_file():
            return candidate
    return no_ext


def _resolved_onex_bin() -> Path:
    p = Path(os.environ["ONEX_BIN"]) if os.environ.get("ONEX_BIN") else _default_onex_bin()
    if not p.is_absolute():
        p = (REPO_ROOT / p).resolve()
    return p


ONEX_BIN = _resolved_onex_bin()

# Default for OnexExplorer CLI subprocess (--cli --unpack, etc.)
_ONEX_SUBPROCESS_TIMEOUT_SEC = 30.0


def _stdio_for_onex() -> Tuple[Optional[int], Optional[int]]:
    """
    WIN32 GUI exes often deadlock or stall subprocess PIPE readers; use DEVNULL on Windows.
    On Unix, capture combined stdout+stderr for assertion messages.
    """
    if sys.platform == "win32":
        return subprocess.DEVNULL, subprocess.DEVNULL
    return subprocess.PIPE, subprocess.STDOUT


def _run_cmd(
    cmd: List[str],
    *,
    cwd=REPO_ROOT,
    env=None,
    timeout: Optional[float] = None,
) -> Tuple[int, str]:
    if timeout is None:
        timeout = _ONEX_SUBPROCESS_TIMEOUT_SEC
    stdout_arg, stderr_arg = _stdio_for_onex()
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            stdout=stdout_arg,
            stderr=stderr_arg,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        partial = e.stdout or ""
        msg = (
            f"\n[OnexExplorer subprocess still running after {timeout}s — likely hang or pathological "
            f"slow unpack; child was terminated by pytest harness]\n{partial}"
        )
        raise AssertionError(msg) from e
    captured = (p.stdout or "") if stdout_arg is subprocess.PIPE else ""
    return p.returncode, captured


def _cli_unpack(game_file_path: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    rc, out = _run_cmd(
        [str(ONEX_BIN), "--cli", "--unpack", str(game_file_path), "--target", str(target_dir)],
        env=env,
    )
    assert rc == 0, out or "(no captured output on Windows; use raw exe debug artifact / run with console build)"


@pytest.fixture(scope="session")
def nostale_download_dir() -> Path:
    return Path(os.environ.get("ONEX_DOWNLOAD_DIR", REPO_ROOT / ".cache" / "nostale_files"))


@pytest.fixture(scope="session")
def game_file_downloader(nostale_download_dir: Path) -> GameFileDownloader:
    """
    Convenience fixture to download a single file and return its local Path.

    Usage:
        file_path = game_file_downloader(r"NostaleData\\NSgtdData.NOS")
    """
    patcher = GfPatcher(session=requests.Session())

    def _func(file_path: str) -> Path:
        return patcher.download(file_path, dir=nostale_download_dir)

    return _func


@pytest.fixture
def unpack_game_archive(game_file_downloader: GameFileDownloader) -> UnpackGameArchive:
    """
    Unpack one ``.NOS`` (by manifest path) into a **fresh temp directory per call**.
    After the test finishes, all directories created during that test are removed.
    """

    created: List[Path] = []

    def _unpack(manifest_file: str) -> Path:
        game_file_path = game_file_downloader(manifest_file)
        out = Path(tempfile.mkdtemp(prefix="onex_e2e_unpack_"))
        created.append(out)
        _cli_unpack(game_file_path, out)
        return out

    yield _unpack

    for d in created:
        shutil.rmtree(d, ignore_errors=True)
