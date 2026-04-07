#!/usr/bin/env bash
# Clean CMake build and populate a portable Windows folder (windeployqt + freeglut DLLs).
# Windows does not ship bash: run this from an MSYS2 MINGW64 / MINGW32 shell, or from PowerShell via
#   .\packaging\windows\build.ps1
# (same layout as CI).
#
# Env:
#   BUILD_DIR    default: build
#   RELEASE_DIR  default: release

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="${BUILD_DIR:-build}"
RELEASE_DIR="${RELEASE_DIR:-release}"

build_path="$ROOT/$BUILD_DIR"
release_path="$ROOT/$RELEASE_DIR"

rm -rf "$build_path" "$release_path"

cmake -S "$ROOT" -B "$build_path" -G Ninja
cmake --build "$build_path"

mkdir -p "$release_path"
cp "$build_path/OnexExplorer.exe" "$release_path/"
cd "$release_path"
if [[ -x "$MINGW_PREFIX/bin/windeployqt.exe" ]]; then
  "$MINGW_PREFIX/bin/windeployqt.exe" --release --compiler-runtime OnexExplorer.exe
else
  "$MINGW_PREFIX/bin/windeployqt-qt5.exe" --release --compiler-runtime OnexExplorer.exe
fi
cd "$ROOT"
shopt -s nullglob
for dll in "$MINGW_PREFIX"/bin/libfreeglut*.dll; do
  cp "$dll" "$release_path/"
done
