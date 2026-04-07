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

This matches the **Windows** job in [`.github/workflows/test.yml`](.github/workflows/test.yml). Build in the **MSYS2 MINGW64** environment (e.g. `mingw64.exe` or Start Menu **“MSYS2 MINGW64”**), not only the default **“MSYS2 MSYS”** shell from `msys2.exe`, so you use the same MinGW-w64 Qt and compiler layout as CI.

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

### 3. Configure and build

From the repository root (under MSYS2, e.g. `cd /c/path/to/OnexExplorer`):

```bash
cmake -S . -B build -G Ninja
cmake --build build
```

Output: `build/OnexExplorer.exe`.

The Windows CMake target is linked as a **console** application so `--help` and `--cli` output appear in the terminal; starting the GUI with **no arguments** (e.g. double‑click) does not keep a stray console window open.

### 4. Optional: portable folder (Qt + freeglut DLLs)

To run outside MSYS without relying on the full MinGW `PATH`, copy the executable and run `windeployqt`, then add freeglut. This is the same sequence as in [`.github/workflows/test.yml`](.github/workflows/test.yml) (E2E folder) and [`.github/workflows/publish.yml`](.github/workflows/publish.yml) (release zip); only the output directory name differs below (`release` vs `e2e_exe` / `release` in CI).

Run this block in **MSYS2 MINGW64** (Bash). It is **not** for cmd.exe or PowerShell—those shells do not understand `shopt`, `$MINGW_PREFIX`, or the `if`/`for` syntax below.

```bash
mkdir -p release
cp build/OnexExplorer.exe release/
cd release
if [ -x "$MINGW_PREFIX/bin/windeployqt.exe" ]; then
  "$MINGW_PREFIX/bin/windeployqt.exe" --release --compiler-runtime OnexExplorer.exe
else
  "$MINGW_PREFIX/bin/windeployqt-qt5.exe" --release --compiler-runtime OnexExplorer.exe
fi
cd ..
shopt -s nullglob
for dll in "$MINGW_PREFIX"/bin/libfreeglut*.dll; do
  cp "$dll" release/
done
```

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

```text
C:\msys64\msys2_shell.cmd -mingw64 -defterm -no-start -where C:\path\to\OnexExplorer -lc "cmake -S . -B build -G Ninja && cmake --build build"
```

(Replace `C:\msys64` and the repo path as needed.)

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


