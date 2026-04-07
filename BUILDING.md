# Building OnexExplorer (Linux + Windows cross-build)

This project is a Qt5 Widgets application with OpenGL/GLU + GLUT (freeglut).

## Linux (Arch)

### Dependencies (system packages)

Install the toolchain + Qt5 + OpenGL stack:

```bash
sudo pacman -S --needed \
  base-devel \
  cmake ninja \
  qt5-base qt5-tools \
  mesa glu freeglut
```

Notes:
- `cmake` is required for the CMake build (recommended).
- `freeglut` provides GLUT headers/libs; `glu` provides `gluPerspective`.

### Build (CMake)

```bash
cmake -S . -B build -G Ninja
cmake --build build
./build/OnexExplorer
```

Notes:
- If you’re on Wayland and the app doesn’t show, try: `QT_QPA_PLATFORM=xcb ./build/OnexExplorer`

If you don’t have `cmake` installed system-wide, you can use the repo-local venv:

```bash
python -m venv .venv
./.venv/bin/pip install -U pip cmake
./.venv/bin/cmake -S . -B build -G Ninja
./.venv/bin/cmake --build build
```

## Windows (from Linux via cross-compile)

Cross-compiling a Qt app to Windows requires:
- a Windows-targeting compiler toolchain (MinGW-w64 or llvm-mingw)
- a matching Qt5 for Windows SDK (built for that toolchain)
- freeglut for Windows (or disabling the model preview)

This repo includes a CMake toolchain file and documented steps (see `cmake/toolchains/`).

### Important cross-build note (Qt tools)

When cross-compiling on Linux, you **cannot run** Windows executables like `moc.exe`/`uic.exe` during the build.
For that reason, the Windows cross-build uses the **host** tools from your Linux Qt5 install:
- `/usr/bin/moc`
- `/usr/bin/uic`
- `/usr/bin/rcc`

### Packaging on Windows (DLLs)

The produced `OnexExplorer.exe` will need Qt runtime DLLs next to it.
Easiest option is to run this **on a Windows machine** (or Windows CI):

```powershell
<QtPrefix>\bin\windeployqt.exe .\OnexExplorer.exe
```


