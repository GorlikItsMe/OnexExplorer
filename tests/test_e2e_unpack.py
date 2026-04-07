import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from tests.conftest import UnpackGameArchive

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTATIONS_PATH = REPO_ROOT / "tests" / "expectations.json"


def sha256_rgba_png(path: Path) -> str:
    """
    Compute SHA256 hash of a PNG image, converted to RGBA.

    Why not just hash file?
    Because diffrent platforms (Linux, Windows) use diffrent encodings and the same image may have diffrent hashes.
    """
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    payload = w.to_bytes(4, "little") + h.to_bytes(4, "little") + img.tobytes()
    return hashlib.sha256(payload).hexdigest()


def test_e2e_unpack_nsgtd_contains_items_dat(unpack_game_archive: UnpackGameArchive):
    out_dir = unpack_game_archive(r"NostaleData\NSgtdData.NOS")

    items = out_dir / "Item.dat"
    assert items.exists(), f"Missing {items}"
    assert items.stat().st_size > 0


def test_e2e_unpack_nsip_and_check_icons_hashes(unpack_game_archive: UnpackGameArchive):
    out_dir = unpack_game_archive(r"NostaleData\NSipData.NOS")

    exp = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))

    for icon_name, icon_hash in exp.get("NSipData.NOS", {}).items():
        img = out_dir / icon_name
        assert img.exists(), f"Missing {img}"
        assert sha256_rgba_png(img) == icon_hash, f"Hash mismatch for {img} ({icon_hash} != {sha256_rgba_png(img)})"
