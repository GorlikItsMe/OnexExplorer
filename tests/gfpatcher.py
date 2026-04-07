from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests


_SHA1_HEX_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def _normalize_sha1_hex(raw: Dict[str, Any]) -> Optional[str]:
    for key in ("sha1", "sha1Hash"):
        v = raw.get(key)
        if isinstance(v, str) and _SHA1_HEX_RE.match(v):
            return v.lower()
    return None


def _sha1_hex_digest(data: bytes) -> str:
    try:
        return hashlib.sha1(data, usedforsecurity=False).hexdigest()
    except TypeError:
        return hashlib.sha1(data).hexdigest()


@dataclass(frozen=True)
class ManifestEntry:
    """
    One row from Gameforge patch manifest ``entries`` (e.g. NosTale).

    File rows: ``path``, ``sha1``, ``file``, ``flags``, ``size``, ``folder=False``.
    Folder rows: only ``file``, ``flags``, ``size``, ``folder=True`` (no patch path/hash).
    """

    path: str  # URL path part; empty for folder-only rows
    sha1: str  # hex lowercase; empty for folder-only rows
    file: str  # e.g. NostaleData\\NSgtdData.NOS
    flags: int
    size: int  # file size in bytes
    folder: bool

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> ManifestEntry:
        file = str(raw["file"])
        folder = bool(raw.get("folder", False))
        flags = int(raw.get("flags", 0))
        sz = raw.get("size")
        size = int(sz) if sz is not None else 0

        if folder:
            return cls(path="", sha1="", file=file, flags=flags, size=size, folder=True)

        if not raw.get("path"):
            raise ValueError(f"manifest file entry missing path: {file!r}")

        path = str(raw["path"])
        sha1 = _normalize_sha1_hex(raw) or ""
        return cls(
            path=path,
            sha1=sha1,
            file=file,
            flags=flags,
            size=size,
            folder=False,
        )

    def matches_cached_payload(self, data: bytes) -> bool:
        if self.folder:
            return False
        if self.sha1:
            return _sha1_hex_digest(data) == self.sha1
        return self.size > 0 and len(data) == self.size


@dataclass(frozen=True)
class GameforgeManifest:
    """Parsed manifest payload (``entries`` plus top-level metadata when present)."""

    entries: list[ManifestEntry]
    size: int = 0
    build: int = 0

    @classmethod
    def from_api_dict(cls, raw: Dict[str, Any]) -> GameforgeManifest:
        rows = [ManifestEntry.from_dict(e) for e in raw.get("entries", [])]
        sz_top = raw.get("size")
        b_top = raw.get("build")
        return cls(
            entries=rows,
            size=int(sz_top) if sz_top is not None else 0,
            build=int(b_top) if b_top is not None else 0,
        )


DEFAULT_API_URL = (
    "https://spark.gameforge.com/api/v1/patching/download/latest/nostale/default?"
    "locale=pl&architecture=x64"
)
DEFAULT_PATCH_BASE_URL = "http://patches.gameforge.com"


class GfPatcher:
    """
    Download individual game files listed in the Gameforge NosTale manifest.
    """

    def __init__(
        self,
        *,
        session: Optional[requests.Session] = None,
        api_url: str = DEFAULT_API_URL,
        patch_base_url: str = DEFAULT_PATCH_BASE_URL,
    ) -> None:
        self._session = session or requests.Session()
        self._api_url = api_url
        self._patch_base_url = patch_base_url.rstrip("/")
        self._manifest: Optional[GameforgeManifest] = None
        self._entries_by_file: Optional[Dict[str, ManifestEntry]] = None

    _TRANSIENT_GET_EXCEPTIONS = (
        requests.exceptions.ChunkedEncodingError,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
    )

    def _get_bytes(self, url: str, *, timeout: int) -> bytes:
        """GET whole body with retries (CI/CD and CDNs sometimes drop large transfers)."""
        for attempt in range(5):
            try:
                r = self._session.get(url, timeout=timeout)
                r.raise_for_status()
                return r.content
            except self._TRANSIENT_GET_EXCEPTIONS:
                if attempt == 4:
                    raise
                time.sleep(min(30, 2**attempt))
        raise RuntimeError("_get_bytes retry loop fell through")

    def _load_manifest(self) -> None:
        raw = self._get_bytes(self._api_url, timeout=120)
        payload = json.loads(raw.decode())
        self._manifest = GameforgeManifest.from_api_dict(payload)
        self._entries_by_file = {e.file: e for e in self._manifest.entries if not e.folder}

    def _ensure_index(self) -> Dict[str, ManifestEntry]:
        if self._entries_by_file is None:
            self._load_manifest()
        assert self._entries_by_file is not None
        return self._entries_by_file

    @property
    def manifest(self) -> GameforgeManifest:
        if self._manifest is None:
            self._load_manifest()
        assert self._manifest is not None
        return self._manifest

    def download(
        self,
        filename: str,
        *,
        dir: Optional[Union[str, Path]] = None,
        target_path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Download one file from the manifest.

        Exactly one of ``dir`` or ``target_path`` must be given.

        - ``dir``: output root; file is written under the relative path from the manifest
          (e.g. ``NostaleData\\foo.NOS`` -> ``<dir>/NostaleData/foo.NOS``).
        - ``target_path``: exact file path to write (parent directories are created).
        """
        if (dir is None) == (target_path is None):
            raise ValueError("Pass exactly one of `dir=` or `target_path=`")

        entries = self._ensure_index()
        if filename not in entries:
            raise KeyError(f"File not found in manifest: {filename}")
        entry = entries[filename]

        if entry.folder:
            raise ValueError(f"Manifest entry is a folder, not a downloadable file: {filename!r}")

        file_path = Path(dir) / filename
        if file_path.exists():
            data = file_path.read_bytes()
            if entry.matches_cached_payload(data):
                return file_path

        url = self._patch_base_url + entry.path
        data = self._get_bytes(url, timeout=300)

        if target_path is not None:
            save_path = Path(target_path).expanduser()
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(data)
            return save_path

        out_root = Path(dir).expanduser()
        out_root.mkdir(parents=True, exist_ok=True)
        clean_name = entry.file.replace("\\", "/")
        save_path = out_root / clean_name
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(data)
        return save_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Download selected .NOS files from Gameforge manifest.")
    ap.add_argument(
        "--out",
        required=True,
        help="Output directory for downloaded files (e.g. .cache/nostale_files).",
    )
    ap.add_argument(
        "--file",
        action="append",
        required=True,
        help=r"Manifest file path to download (repeatable), e.g. NostaleData\\NSgtdData.NOS",
    )
    args = ap.parse_args()

    out_root = Path(args.out)
    patcher = GfPatcher()
    downloaded = [patcher.download(f, dir=out_root) for f in args.file]

    print(json.dumps({"downloaded": [str(p) for p in downloaded]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
