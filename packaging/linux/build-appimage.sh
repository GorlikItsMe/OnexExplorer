#!/usr/bin/env bash
# Build OnexExplorer AppImage (linuxdeploy + Qt plugin + appimagetool).
# Run from repo root after: cmake -S . -B build -G Ninja && cmake --build build
#
# Env:
#   APPIMAGE_EXTRACT_AND_RUN=1  recommended (GitHub Actions / systems without FUSE)
#   BUILD_DIR          default: build
#   APPIMAGE_TOOLS_DIR where to store downloaded .AppImage tools; default: $RUNNER_TEMP/appimage-tools or /tmp/appimage-tools
#   GITHUB_REF_NAME    used for VERSION when VERSION unset (strip leading v)
#   VERSION            output version segment in filename; default from GITHUB_REF_NAME or 0.0.0

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="${BUILD_DIR:-build}"
BINARY="$ROOT/$BUILD_DIR/OnexExplorer"
TOOLS_DIR="${APPIMAGE_TOOLS_DIR:-${RUNNER_TEMP:-/tmp}/appimage-tools}"

if [[ ! -f "$BINARY" ]]; then
  echo "error: missing binary: $BINARY (build the project first)" >&2
  exit 1
fi

if [[ -z "${VERSION:-}" ]]; then
  if [[ -n "${GITHUB_REF_NAME:-}" ]]; then
    VERSION="${GITHUB_REF_NAME#v}"
  else
    VERSION="0.0.0"
  fi
fi
export VERSION
QMAKE="$(command -v qmake)"
export QMAKE

mkdir -p "$TOOLS_DIR"
cd "$TOOLS_DIR"
wget -q -O linuxdeploy-x86_64.AppImage \
  https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
wget -q -O linuxdeploy-plugin-qt-x86_64.AppImage \
  https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous/linuxdeploy-plugin-qt-x86_64.AppImage
wget -q -O appimagetool-x86_64.AppImage \
  https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage linuxdeploy-plugin-qt-x86_64.AppImage appimagetool-x86_64.AppImage

cd "$ROOT"
mkdir -p AppDir/usr/bin
cp "$BINARY" AppDir/usr/bin/
mkdir -p AppDir/usr/share/applications
cp packaging/linux/onexexplorer.desktop AppDir/usr/share/applications/
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
convert resources/oxe_icon_trans.ico -resize 256x256 \
  AppDir/usr/share/icons/hicolor/256x256/apps/onexexplorer.png

EXTRA=( )
declare -A bundled
while read -r _ arrow libpath _; do
  [[ "$arrow" == "=>" ]] || continue
  case "$libpath" in
    *libglut*|*libGLU*|*libXi.so*|*libXxf86vm*)
      if [[ -f "$libpath" ]] && [[ -z "${bundled[$libpath]:-}" ]]; then
        bundled[$libpath]=1
        EXTRA+=(--library "$libpath")
      fi
      ;;
  esac
done < <(ldd "$BINARY" || true)

"$TOOLS_DIR/linuxdeploy-x86_64.AppImage" --appdir AppDir \
  -e AppDir/usr/bin/OnexExplorer \
  -d AppDir/usr/share/applications/onexexplorer.desktop \
  -i AppDir/usr/share/icons/hicolor/256x256/apps/onexexplorer.png \
  --plugin "$TOOLS_DIR/linuxdeploy-plugin-qt-x86_64.AppImage" \
  "${EXTRA[@]}"

OUT="$ROOT/OnexExplorer-${VERSION}-x86_64.AppImage"
"$TOOLS_DIR/appimagetool-x86_64.AppImage" AppDir "$OUT"
echo "Built: $OUT"
