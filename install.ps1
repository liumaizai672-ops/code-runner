<#
  code-runner installer (Windows PowerShell 5.1+ / 7+)

  Usage:
    irm https://raw.githubusercontent.com/liumaizai672-ops/code-runner/main/install.ps1 | iex

  Optional environment variables:
    CODE_RUNNER_SKIP_TOOLCHAIN=1   do not auto-install the C++ toolchain (w64devkit)
    CODE_RUNNER_DIR=...            custom install directory

  NOTE: this file is intentionally ASCII-only. Windows PowerShell 5.1 decodes a
  BOM-less script as ANSI, which corrupts non-ASCII characters and can break
  parsing. Keep it ASCII so the one-liner works on every Windows machine.
#>

$ErrorActionPreference = "Stop"

$RepoSlug = "liumaizai672-ops/code-runner"
$Branch   = "main"
if ($env:CODE_RUNNER_DIR) {
    $Dest = $env:CODE_RUNNER_DIR
} else {
    $Dest = Join-Path $env:USERPROFILE ".workbuddy\skills\code-runner"
}

function Write-Step($n, $msg) {
    Write-Host "  [$n/3] $msg" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  code-runner - AI code executor" -ForegroundColor Cyan
Write-Host "  ------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# ---------------------------------------------------------------- 1. get files
Write-Step 1 "Fetching skill files"

$git = Get-Command git -CommandType Application -ErrorAction SilentlyContinue
$gj  = $null
if ($git) { $gj = $git.Source }

if ($gj) {
    if (Test-Path (Join-Path $Dest ".git")) {
        Write-Host "        Existing install found, updating in place"
        & $gj -C $Dest fetch --depth 1 origin $Branch 2>&1 | Out-Null
        & $gj -C $Dest reset --hard "origin/$Branch" 2>&1 | Out-Null
    } else {
        if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
        New-Item -ItemType Directory -Force -Path (Split-Path $Dest -Parent) | Out-Null
        & $gj clone --depth 1 --branch $Branch "https://github.com/$RepoSlug.git" $Dest 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "git clone failed. Check your network, or grab the zip manually: https://github.com/$RepoSlug"
        }
    }
} else {
    Write-Host "        git not found, falling back to zip download"
    $zip = Join-Path $env:TEMP ("code-runner-" + [guid]::NewGuid().ToString("N").Substring(0, 8) + ".zip")
    $tmp = Join-Path $env:TEMP "code-runner-extract"
    Invoke-WebRequest -Uri "https://codeload.github.com/$RepoSlug/zip/refs/heads/$Branch" -OutFile $zip -UseBasicParsing
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
    Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
    $inner = Get-ChildItem -Path $tmp -Directory | Select-Object -First 1
    if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
    New-Item -ItemType Directory -Force -Path (Split-Path $Dest -Parent) | Out-Null
    Move-Item -Path $inner.FullName -Destination $Dest
    Remove-Item -Recurse -Force $tmp
    Remove-Item -Force $zip
}

# ---------------------------------------------------------------- 2. verify
Write-Step 2 "Verifying files"

$skill  = Join-Path $Dest "SKILL.md"
$runner = Join-Path $Dest "scripts\run.py"
$probe  = Join-Path $Dest "scripts\toolchain.py"
if (-not (Test-Path $skill))  { throw "Incomplete install: SKILL.md is missing" }
if (-not (Test-Path $runner)) { throw "Incomplete install: scripts\run.py is missing" }
Write-Host "        SKILL.md / run.py / toolchain.py OK"

# ---------------------------------------------------------------- 3. toolchains
Write-Step 3 "Detecting local toolchains"

$py = $null
$candidates = @(
    (Join-Path $env:USERPROFILE ".workbuddy\binaries\python\versions\3.13.12\python.exe"),
    "C:\Program Files\PyManager\python.exe"
)
foreach ($c in $candidates) {
    if (-not $py -and (Test-Path $c)) { $py = $c }
}
if (-not $py) {
    $p = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if ($p) { $py = $p.Source }
}

if ($py) {
    & $py $probe --refresh
} else {
    Write-Host "        Python not found, skipping probe (the skill detects on first run)" -ForegroundColor DarkGray
}

# optional: bootstrap a C++ compiler
if ($env:CODE_RUNNER_SKIP_TOOLCHAIN -ne "1") {
    $gpp = Join-Path $env:USERPROFILE ".workbuddy\binaries\mingw64\bin\g++.exe"
    if (-not (Test-Path $gpp)) {
        Write-Host ""
        Write-Host "        No C++ compiler found, fetching portable w64devkit (~64MB)..." -ForegroundColor DarkGray
        try {
            $dl    = Join-Path $env:TEMP "w64devkit.7z.exe"
            $base  = Join-Path $env:USERPROFILE ".workbuddy\binaries\mingw64"
            $stage = Join-Path $env:TEMP "w64stage"
            Invoke-WebRequest -Uri "https://github.com/skeeto/w64devkit/releases/download/v2.10.1/w64devkit-x64-2.10.1.7z.exe" -OutFile $dl -UseBasicParsing
            New-Item -ItemType Directory -Force -Path $base | Out-Null
            if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
            & $dl -y "-o$stage" | Out-Null
            $inner = Get-ChildItem -Path $stage -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($inner) {
                Copy-Item -Path (Join-Path $inner.FullName "*") -Destination $base -Recurse -Force
            } else {
                Copy-Item -Path (Join-Path $stage "*") -Destination $base -Recurse -Force
            }
            Remove-Item -Recurse -Force $stage -ErrorAction SilentlyContinue
            Remove-Item -Force $dl -ErrorAction SilentlyContinue
            if ($py) { & $py $probe --refresh }
            Write-Host "        C++ toolchain ready: $base\bin\g++.exe" -ForegroundColor Green
        } catch {
            Write-Host "        Toolchain auto-install failed: $($_.Exception.Message)" -ForegroundColor DarkYellow
            Write-Host "        See references/toolchain-install.md for manual steps" -ForegroundColor DarkYellow
        }
    }
}

# ---------------------------------------------------------------- done
Write-Host ""
Write-Host "  Installed successfully." -ForegroundColor Green
Write-Host ""
Write-Host "  Open a NEW WorkBuddy conversation and just say:"
Write-Host '    "write a bubble sort in C++ and run it"'
Write-Host '    "implement quicksort in Java and run a sample"'
Write-Host ""
Write-Host "  Skill directory: $Dest" -ForegroundColor DarkGray
Write-Host ""
