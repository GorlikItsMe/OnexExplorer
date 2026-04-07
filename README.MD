# OnexExplorer #

OnexExplorer is an open-source tool for unpacking and repacking .NOS data files from game called NosTale. It can open almost all .NOS files and allows to view the Content, export and replace it and even add own Content to them. Our software works on Qt 5.5+ with OpenGl.

Client Modding Discord:  [<img src="https://discordapp.com/api/guilds/590958760374042657/widget.png?style=shield">](https://discord.gg/t73Ayca)


## Currently supported archives ##

- NSgtdData (Items, quests, skills, mobs etc. data)
- NSlangData (_code_lang_list (ztsXXXe))
- NScliData (constring.dat)
- NSetcData (Word list for Memory & TabooStr.lst)
- NS4BbData (Big images)
- NSipData (Icons)
- NStpData (Map and model textures)
- NStpeData (Effect textures)
- NStpuData (UI textures)
- NStcData (Map Grids)
- NSmpData (Monster-related sprites)
- NSppData (Player-related sprites)
- NSmnData (Mob-related sprite infos)
- NSpnData (Player-related sprite infos)
- NSmcData (Monster-related animation kits)
- NSpcData (Player-related animation kits)
- NStgData (3D Models)
- NStgeData (3D VFX models)


**Other files will be added in future updates.**


## Unsupported archives ##

- NStuData (Map configs)
- NSeffData (VFX configs)
- NStsData
- NStkData
- NSemData
- NSesData
- NSedData
- NSgrdData
- NSpmData


## License ##

Our project is based on **Boost Software License**:
> [LICENSE](/LICENSE)


## Installation ##

Downloads: **Releases** (tagged versions). Pre-releases are experimental.

### Linux (x86_64)

Official Linux builds are shipped as an **AppImage** (bundled Qt and freeglut; you do **not** need to install those from your distro).

1. Download `OnexExplorer-*-x86_64.AppImage` from the release assets.
2. Make it executable and run it:

```bash
chmod +x OnexExplorer-*-x86_64.AppImage
./OnexExplorer-*-x86_64.AppImage
```

**Notes**

- You still need a normal **desktop/OpenGL stack** (Mesa or vendor drivers are usually already there). This is standard on almost all Linux desktops.
- To build from source instead (Arch, Ubuntu, etc.), see **[BUILDING.md](/BUILDING.md)**.

### Windows

1. Download the **`OnexExplorer-windows-*.zip`** for your architecture (x86_64 or i686) from the release.
2. Extract the whole folder; keep `OnexExplorer.exe` together with the bundled `.dll` files, `platforms`, `styles`, and any other shipped files.
3. Run `OnexExplorer.exe`.

The experimental branch and releases flaged with **pre-release** are in development and don't guarantee that everything works as expected. 
**If you have any problems please try to compile the master branch or use regular releases!**


## End-to-end tests (E2E) ##

These tests build the app, download selected `.NOS` files, then run **CLI unpack** and assert on extracted files. They are implemented with **pytest** under `tests/`.

### Prerequisites

1. **Compile OnexExplorer** (see [BUILDING.md](/BUILDING.md)) so the binary exists, by default:
   - Linux: `build/OnexExplorer`
   - Windows (MSYS/MinGW): run **`.\packaging\windows\build.ps1`** from PowerShell, or **`bash packaging/windows/build.sh`** from an MSYS2 MINGW64 shell, so tests use **`release/OnexExplorer.exe`** (the raw `build/` exe is not enough for Qt/DLLs; Windows does not ship bash—MSYS2 provides it)
2. **Python 3** with packages:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install requests pillow pytest pytest-timeout
```

### Run tests

From the repository root, after a successful CMake build:

```bash
export QT_QPA_PLATFORM=offscreen   # headless Qt; optional on desktop with a display
python3 -m pytest tests/ -v
```

On **Windows**, use **`release/`** after **`.\packaging\windows\build.ps1`** or the MSYS2 **`build.sh`** flow (see [BUILDING.md](BUILDING.md)); do **not** set `QT_QPA_PLATFORM=offscreen` unless you also deploy `platforms\qoffscreen.dll`. Tests clear that variable on Windows so Qt uses the usual `qwindows` plugin next to the exe.

```powershell
$env:ONEX_BIN="release\OnexExplorer.exe"   # or omit if release\ exists (default search order)
python -m pytest tests/ -v
```

### Environment variables (optional)

| Variable | Meaning |
|----------|---------|
| `ONEX_BIN` | Full path to the `OnexExplorer` executable (default: `build/OnexExplorer` on Linux; on Windows, `release/OnexExplorer.exe` if present, else `build/OnexExplorer.exe`) |
| `ONEX_BUILD_DIR` | Directory containing the built binary (default: `build` under the repo) |
| `ONEX_DOWNLOAD_DIR` | Cache for downloaded `.NOS` files (default: `.cache/nostale_files`) |

## Report Bugs and suggest features ##
If you have any **problems** with OnexExplorer or want to suggest new **features** feel free to open **[issues](https://github.com/Pumbaa98/OnexExplorer/issues)**.
Please dont forget to mention the **version** you're using.
