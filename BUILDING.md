# Building OnexExplorer (Linux, native Windows, and Windows cross-build)

This project is a Qt5 Widgets application with OpenGL/GLU + GLUT (freeglut).

## Linux — install without compiling (recommended for most users)

From **Releases**, download **`OnexExplorer-*-x86_64.AppImage`**, then:

```bash
chmod +x OnexExplorer-*-x86_64.AppImage
./OnexExplorer-*-x86_64.AppImage
```

To build the AppImage yourself (e.g. CI parity), use **`packaging/linux/build-appimage.sh`** after a normal CMake build (see script header for environment variables).

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

## Windows (native, MSYS2 MINGW64)

CI and releases run **`packaging/windows/build.sh`** inside **MSYS2** (GitHub Actions uses the MSYS2 bash shell; MINGW64 in [`.github/workflows/test.yml`](.github/workflows/test.yml); MINGW64 or MINGW32 in [`.github/workflows/publish.yml`](.github/workflows/publish.yml)). Stock **Windows does not include bash**—it comes with MSYS2 (or Git Bash). Locally, use the **MSYS2 MINGW64** terminal (e.g. `mingw64.exe` or Start Menu **“MSYS2 MINGW64”**), not only **“MSYS2 MSYS”**, so `$MINGW_PREFIX`, Qt, and the compiler layout match CI.

### 1. Install MSYS2

Install [MSYS2](https://www.msys2.org/), then update the package databases (from any MSYS2 shell):

```bash
pacman -Syu
```

Close the terminal if the updater asks you to, then run `pacman -Syu` again until there is nothing left to do.

### 2. Install build dependencies

Open **“MSYS2 MINGW64”** and run:

```bash
pacman -S --needed \
  mingw-w64-x86_64-toolchain \
  mingw-w64-x86_64-cmake \
  mingw-w64-x86_64-ninja \
  mingw-w64-x86_64-qt5 \
  mingw-w64-x86_64-qt5-tools \
  mingw-w64-x86_64-angleproject \
  mingw-w64-x86_64-freeglut
```

### 3. One-shot: clean build + portable `release/` (recommended)

**From PowerShell** (repo root; requires [MSYS2](https://www.msys2.org/) installed, default `C:\msys64`, or set **`MSYS2_ROOT`**):

```powershell
.\packaging\windows\build.ps1
```

For a **32-bit** MinGW toolchain, use `.\packaging\windows\build.ps1 -Msystem mingw32`.

**From an MSYS2 MINGW64 shell** (e.g. `cd /c/path/to/OnexExplorer`):

```bash
bash packaging/windows/build.sh
```

This removes **`build/`** and **`release/`**, runs a fresh CMake **Ninja** build, then fills **`release/`** with `OnexExplorer.exe`, Qt runtime via `windeployqt`, and `libfreeglut*.dll`—the same layout as the Windows jobs in CI and the shipped zip. The real work is done by **`build.sh`** in MSYS2’s bash environment (`$MINGW_PREFIX`, `windeployqt`, MinGW `cmake`/`ninja`).

Optional environment variables (see script header): `BUILD_DIR`, `RELEASE_DIR`.

The Windows CMake target is linked as a **console** application so `--help` and `--cli` output appear in the terminal; starting the GUI with **no arguments** (e.g. double‑click) does not keep a stray console window open.

### 4. Incremental configure and build (optional)

If you do not want to wipe **`build/`** each time, configure and build only:

```bash
cmake -S . -B build -G Ninja
cmake --build build
```

Output: `build/OnexExplorer.exe`. To get a runnable portable folder without the full MinGW `PATH`, run **`bash packaging/windows/build.sh`** (that script always cleans first), or reproduce its steps yourself using the same `windeployqt` and `libfreeglut*.dll` copy logic inside **`packaging/windows/build.sh`**.

### 5. If the default GCC (`cc`) fails to compile

On some machines the MinGW GCC toolchain is broken (CMake’s compiler test or `windres` preprocessing fails). Install Clang and LLVM, then configure with **`llvm-windres`** so `.rc` files still build:

```bash
pacman -S --needed mingw-w64-x86_64-clang mingw-w64-x86_64-llvm

rm -rf build
CC=clang CXX=clang++ cmake -S . -B build -G Ninja -DCMAKE_RC_COMPILER=llvm-windres
cmake --build build
```

### Running CMake from cmd.exe / PowerShell

You can invoke the same environment without opening the MINGW64 window manually, for example:

Same idea as **`build.ps1`**: from cmd.exe you can call `msys2_shell.cmd` directly (adjust paths):

```text
C:\msys64\msys2_shell.cmd -mingw64 -defterm -no-start -where C:\path\to\OnexExplorer -lc "bash packaging/windows/build.sh"
```

(For an incremental build without cleaning, use `cmake -S . -B build -G Ninja && cmake --build build` inside the same MSYS2 environment instead of the script.)

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


