# 缺工具链时的便携安装

原则：**装到用户目录，不改系统 PATH，不要求管理员权限。**

## C++ / C（g++ / gcc）

本机优先检查 `C:\Users\Administrator\.workbuddy\binaries\mingw64\bin\g++.exe`。

便携安装（w64devkit，约 64MB 自解压包）：

```bash
mkdir -p ~/.workbuddy/binaries/mingw64_dl
curl -L -o ~/.workbuddy/binaries/mingw64_dl/w64devkit.7z.exe \
  https://github.com/skeeto/w64devkit/releases/download/v2.10.1/w64devkit-x64-2.10.1.7z.exe
# 自解压到目标目录，-y 静默覆盖
~/.workbuddy/binaries/mingw64_dl/w64devkit.7z.exe -y -o"C:/Users/Administrator/.workbuddy/binaries/mingw64" >/dev/null
```

解压后把 `mingw64/bin` 加入进程环境（无需改系统 PATH）：

```bash
export PATH="/c/Users/Administrator/.workbuddy/binaries/mingw64/bin:$PATH"
g++ --version
```

装完执行 `python scripts/toolchain.py --refresh` 刷新缓存。

替代方案：MSYS2（`winget install MSYS2.MSYS2` 后 `pacman -S mingw-w64-ucrt-x86_64-gcc`）、TDM-GCC、或 Visual Studio Build Tools 的 `cl.exe`（需 `vcvars64.bat` 环境）。

## Java

需要 JDK 17+。本机已有（探测结果里会显示路径）。若缺失：

```bash
winget install EclipseAdoptium.Temurin.21.JDK
```

或下载 zip 版解压到 `~/.workbuddy/binaries/jdk21`，用 `CODE_RUNNER_JAVA` 和 `CODE_RUNNER_JAVAC` 环境变量指向 `bin/java.exe`、`bin/javac.exe`，免改 PATH。

## Python / Node

本机已有。优先用托管版本：
- Python：`C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe`
- Node：`C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2-6\node.exe`

## Go

```bash
winget install GoLang.Go
```

或用 `CODE_RUNNER_GO` 指向 `go.exe`。

## Rust

```bash
winget install Rustlang.Rustup
```

装完 `rustc --version` 验证，再用 `CODE_RUNNER_RUSTC` 指向。

## 环境变量覆盖表

探测时优先读取这些变量，适合装在非标准路径的情况：

| 变量 | 作用 |
|---|---|
| `CODE_RUNNER_G_PLUS_PLUS` | 指定 g++ 路径 |
| `CODE_RUNNER_GCC` | 指定 gcc 路径 |
| `CODE_RUNNER_JAVAC` / `CODE_RUNNER_JAVA` | 指定 JDK 的 javac / java |
| `CODE_RUNNER_PYTHON` / `CODE_RUNNER_NODE` | 指定解释器 |
| `CODE_RUNNER_GO` / `CODE_RUNNER_RUSTC` | 指定 Go / Rust 编译器 |

注：`g++` 的变量名把 `+` 替换为 `_PLUS_`，即 `CODE_RUNNER_G_PLUS_PLUS`。
