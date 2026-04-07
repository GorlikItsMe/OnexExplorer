import hashlib
import json
import time
from pathlib import Path

import pytest
import requests

from tests.conftest import UnpackGameArchive
from tests.gfpatcher import GfPatcher

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTATIONS_PATH = REPO_ROOT / "tests" / "expectations.json"

_E2E_MANIFEST_FILES = (
    r"NostaleData\NSgtdData.NOS",
    r"NostaleData\NSipData.NOS",
)


@pytest.fixture(scope="session")
def e2e_nos_downloaded(nostale_download_dir: Path) -> None:
    """Download all E2E blobs once; per-test timeout stays ~unpack-only (pytest timeout_func_only)."""
    patcher = GfPatcher(session=requests.Session())
    session_t0 = time.perf_counter()
    print(f"\n[e2e] NOS download session: cache dir = {nostale_download_dir}", flush=True)
    for rel in _E2E_MANIFEST_FILES:
        print(f"[e2e] NOS fetching: {rel!r} ...", flush=True)
        t0 = time.perf_counter()
        path = patcher.download(rel, dir=nostale_download_dir)
        dt = time.perf_counter() - t0
        size = path.stat().st_size if path.is_file() else 0
        print(f"[e2e] NOS done: {rel!r} -> {path} | {dt:.2f}s | {size} bytes", flush=True)
    session_dt = time.perf_counter() - session_t0
    print(f"[e2e] NOS download session total: {session_dt:.2f}s\n", flush=True)


def sha256_rgba_png(path: Path) -> str:
    """
    Compute SHA256 hash of a PNG image, converted to RGBA.

    Why not just hash file?
    Because diffrent platforms (Linux, Windows) use diffrent encodings and the same image may have diffrent hashes.
    """
    from PIL import Image

    img = Image.open(path).convert("RGBA")
    w, h = img.size
    payload = w.to_bytes(4, "little") + h.to_bytes(4, "little") + img.tobytes()
    return hashlib.sha256(payload).hexdigest()


def test_e2e_unpack_nsgtd_contains_items_dat(
    e2e_nos_downloaded: None,
    unpack_game_archive: UnpackGameArchive,
):
    out_dir = unpack_game_archive(r"NostaleData\NSgtdData.NOS")

    items = out_dir / "Item.dat"
    assert items.exists(), f"Missing {items}"
    assert items.stat().st_size > 0


def test_e2e_unpack_nsip_and_check_icons_hashes(
    e2e_nos_downloaded: None,
    unpack_game_archive: UnpackGameArchive,
):
    out_dir = unpack_game_archive(r"NostaleData\NSipData.NOS")

    exp = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))

    for icon_name, icon_hash in exp.get("NSipData.NOS", {}).items():
        img = out_dir / icon_name
        assert img.exists(), f"Missing {img}"
        assert sha256_rgba_png(img) == icon_hash, f"Hash mismatch for {img} ({icon_hash} != {sha256_rgba_png(img)})"
