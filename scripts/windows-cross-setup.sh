#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TP="${ROOT}/third_party"

mkdir -p "${TP}"

echo "==> This script documents the recommended cross-build setup."
echo "==> It does NOT require sudo, but it downloads large SDKs."
echo

echo "1) Download and unpack llvm-mingw (portable Windows cross toolchain)"
echo "   Expected path: ${TP}/llvm-mingw"
echo

echo "2) Download a Qt5 Windows SDK (Qt 5.15.2 MinGW 8.1 64-bit)"
echo "   Expected path: ${TP}/qt/5.15.2/mingw81_64"
echo

echo "3) Build freeglut for Windows (needed by the model preview)"
echo "   Expected install prefix: ${TP}/freeglut-install-win"
echo

cat <<'EOF'

## Repro steps (commands)

# From repo root:
python -m venv .venv
./.venv/bin/pip install -U pip cmake aqtinstall

# Download Qt for Windows (needs network access):
HOME="$PWD/third_party/home" TMPDIR="$PWD/third_party/tmp" \
  ./.venv/bin/python -m aqt install-qt windows desktop 5.15.2 win64_mingw81 -O third_party/qt

# Download llvm-mingw and unpack into third_party/llvm-mingw (manual step)

# Build freeglut (Windows static lib):
LLVM_MINGW_ROOT="$PWD/third_party/llvm-mingw" \
  ./.venv/bin/cmake -S third_party/freeglut-src -B third_party/freeglut-build-win -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$PWD/cmake/toolchains/windows-llvm-mingw-x86_64.cmake" \
  -DCMAKE_INSTALL_PREFIX="$PWD/third_party/freeglut-install-win" \
  -DFREEGLUT_BUILD_DEMOS=OFF -DFREEGLUT_BUILD_SHARED_LIBS=OFF
./.venv/bin/cmake --build third_party/freeglut-build-win
./.venv/bin/cmake --install third_party/freeglut-build-win

# Build OnexExplorer.exe:
rm -rf build-mingw
LLVM_MINGW_ROOT="$PWD/third_party/llvm-mingw" \
QT_WIN_PREFIX="$PWD/third_party/qt/5.15.2/mingw81_64" \
  ./.venv/bin/cmake -S . -B build-mingw -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$PWD/cmake/toolchains/windows-llvm-mingw-x86_64.cmake" \
  -DGLUT_INCLUDE_DIR="$PWD/third_party/freeglut-install-win/include" \
  -DGLUT_glut_LIBRARY_RELEASE="$PWD/third_party/freeglut-install-win/lib/libfreeglut_static.a" \
  -DCMAKE_AUTOMOC_EXECUTABLE=/usr/bin/moc \
  -DCMAKE_AUTOUIC_EXECUTABLE=/usr/bin/uic \
  -DCMAKE_AUTORCC_EXECUTABLE=/usr/bin/rcc
./.venv/bin/cmake --build build-mingw

EOF

