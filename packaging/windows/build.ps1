#Requires -Version 5.1
<#
.SYNOPSIS
  Run packaging/windows/build.sh inside MSYS2 (Windows has no built-in bash; this script finds MSYS2).

.PARAMETER Msystem
  MSYS2 environment: mingw64 (default) or mingw32 — must match the toolchain you installed (x86_64 vs i686).
#>
param(
    [ValidateSet("mingw64", "mingw32")]
    [string]$Msystem = "mingw64"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$candidates = @(
    $env:MSYS2_ROOT
    "C:\msys64"
    "C:\msys32"
)

$msys2Root = $null
foreach ($c in $candidates) {
    if ([string]::IsNullOrWhiteSpace($c)) { continue }
    $cmd = Join-Path $c "msys2_shell.cmd"
    if (Test-Path -LiteralPath $cmd) {
        $msys2Root = $c
        break
    }
}

if (-not $msys2Root) {
    Write-Error @"
Could not find msys2_shell.cmd. Install MSYS2 from https://www.msys2.org/ (default install: C:\msys64), or set MSYS2_ROOT to your install directory.

Then open 'MSYS2 MINGW64', install the packages from BUILDING.md, and either run this script again from PowerShell or run: bash packaging/windows/build.sh
"@
    exit 1
}

$shellCmd = Join-Path $msys2Root "msys2_shell.cmd"
$bashLine = "bash packaging/windows/build.sh"
$argList = @(
    "-$Msystem",
    "-defterm",
    "-no-start",
    "-where", $repoRoot,
    "-lc", $bashLine
)

$proc = Start-Process -FilePath $shellCmd -ArgumentList $argList -NoNewWindow -Wait -PassThru
exit $proc.ExitCode
