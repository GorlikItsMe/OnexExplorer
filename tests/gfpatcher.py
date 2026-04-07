import argparse
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Optional, Union

import requests


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
        self._manifest: Optional[Dict] = None
        self._entries_by_file: Optional[Dict[str, Dict]] = None

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
        self._manifest = json.loads(raw.decode())
        self._entries_by_file = {}
        for entry in self._manifest.get("entries", []):
            self._entries_by_file[entry["file"]] = entry

    def _ensure_index(self) -> Dict[str, Dict]:
        if self._entries_by_file is None:
            self._load_manifest()
        assert self._entries_by_file is not None
        return self._entries_by_file

    @property
    def manifest(self) -> Dict:
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

        # Check if file is already downloaded (and have the same hash)
        file_path = Path(dir) / filename
        if file_path.exists():
            # compute hash of the file
            computed_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            if computed_hash == entry["hash"]:
                return file_path

        # Download file
        url = self._patch_base_url + entry["path"]
        data = self._get_bytes(url, timeout=300)

        if target_path is not None:
            save_path = Path(target_path).expanduser()
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(data)
            return save_path

        out_root = Path(dir).expanduser()
        out_root.mkdir(parents=True, exist_ok=True)
        clean_name = entry["file"].replace("\\", "/")
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

