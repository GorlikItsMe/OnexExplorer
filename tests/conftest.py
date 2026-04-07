import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, List

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


def _run_cmd(cmd: List[str], *, cwd=REPO_ROOT, env=None) -> tuple:
    p = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return p.returncode, p.stdout


def _cli_unpack(game_file_path: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    rc, out = _run_cmd(
        [str(ONEX_BIN), "--cli", "--unpack", str(game_file_path), "--target", str(target_dir)],
        env=env,
    )
    assert rc == 0, out


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
