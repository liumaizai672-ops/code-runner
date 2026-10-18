<#
  code-runner 一键安装（PowerShell 5.1+ / 7+）

  用法：
    irm https://raw.githubusercontent.com/liumaizai672-ops/code-runner/main/install.ps1 | iex

  可选环境变量：
    CODE_RUNNER_SKIP_TOOLCHAIN=1   不自动下载 C++ 编译器（w64devkit）
    CODE_RUNNER_DIR=...            自定义安装目录
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
Write-Host "  code-runner · AI 代码执行器" -ForegroundColor Cyan
Write-Host "  ------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# ---------------------------------------------------------------- 1. 取代码
Write-Step 1 "获取技能文件"

$git = Get-Command git -CommandType Application -ErrorAction SilentlyContinue
$gj  = $null
if ($git) { $gj = $git.Source }

if ($gj) {
    if (Test-Path (Join-Path $Dest ".git")) {
        Write-Host "        已有安装，原地更新"
        & $gj -C $Dest fetch --depth 1 origin $Branch 2>&1 | Out-Null
        & $gj -C $Dest reset --hard "origin/$Branch" 2>&1 | Out-Null
    } else {
        if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
        New-Item -ItemType Directory -Force -Path (Split-Path $Dest -Parent) | Out-Null
        & $gj clone --depth 1 --branch $Branch "https://github.com/$RepoSlug.git" $Dest 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "git clone 失败，请检查网络或改用 zip 安装： https://github.com/$RepoSlug"
        }
    }
} else {
    Write-Host "        未找到 git，改用 zip 下载"
    $zip = Join-Path $env:TEMP "code-runner-$([guid]::NewGuid().ToString('N').Substring(0,8)).zip"
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

# ---------------------------------------------------------------- 2. 校验
Write-Step 2 "校验文件完整性"

$skill = Join-Path $Dest "SKILL.md"
$runner = Join-Path $Dest "scripts\run.py"
if (-not (Test-Path $skill))  { throw "安装不完整：缺少 SKILL.md" }
if (-not (Test-Path $runner)) { throw "安装不完整：缺少 scripts\run.py" }
Write-Host "        SKILL.md / run.py / toolchain.py 就位"

# ---------------------------------------------------------------- 3. 工具链
Write-Step 3 "探测本机编译器"

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
    & $py (Join-Path $Dest "scripts\toolchain.py") --refresh
} else {
    Write-Host "        未找到 Python，跳过探测（首次运行时技能会自己探测）" -ForegroundColor DarkGray
}

# 可选：自动补 C++ 编译器
if ($env:CODE_RUNNER_SKIP_TOOLCHAIN -ne "1") {
    $gpp = Join-Path $env:USERPROFILE ".workbuddy\binaries\mingw64\bin\g++.exe"
    if (-not (Test-Path $gpp)) {
        Write-Host ""
        Write-Host "        未检测到 C++ 编译器，正在准备便携版 w64devkit（约 64MB）..." -ForegroundColor DarkGray
        try {
            $dl   = Join-Path $env:TEMP "w64devkit.7z.exe"
            $base = Join-Path $env:USERPROFILE ".workbuddy\binaries\mingw64"
            Invoke-WebRequest -Uri "https://github.com/skeeto/w64devkit/releases/download/v2.10.1/w64devkit-x64-2.10.1.7z.exe" -OutFile $dl -UseBasicParsing
            New-Item -ItemType Directory -Force -Path $base | Out-Null
            $stage = Join-Path $env:TEMP "w64stage"
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
            if ($py) { & $py (Join-Path $Dest "scripts\toolchain.py") --refresh }
            Write-Host "        C++ 编译器就绪：$base\bin\g++.exe" -ForegroundColor Green
        } catch {
            Write-Host "        编译器自动安装失败：$($_.Exception.Message)" -ForegroundColor DarkYellow
            Write-Host "        手动安装说明见 references/toolchain-install.md" -ForegroundColor DarkYellow
        }
    }
}

# ---------------------------------------------------------------- 完成
Write-Host ""
Write-Host "  安装完成。" -ForegroundColor Green
Write-Host ""
Write-Host "  回到 WorkBuddy 新开一个对话，直接说："
Write-Host '    "用 C++ 写个冒泡排序并运行"'
Write-Host '    "Java 实现快排，跑一组样例"'
Write-Host ""
Write-Host "  技能目录：$Dest" -ForegroundColor DarkGray
Write-Host ""
