# code-runner

> 让 AI **写完代码就直接编译运行**，不再反问「请问用哪种语言？」「需要我继续吗？」。

一个 WorkBuddy / Claude Skills 技能包。装上之后，任何编程任务都是：**写代码 → 编译 → 运行 → 贴出真实输出**，中途不打断你。

```
你：写个 C++ 求最长上升子序列，用 10 9 2 5 3 7 101 18 试一下

AI：已跑通：C++17 / g++ 16.2.0（编译 2.2s，运行 0.3s）

    LIS 长度: 4
    其中一个解: 2 3 7 18
```

---

## 一键安装

**Windows（PowerShell，推荐）**

```powershell
irm https://raw.githubusercontent.com/liumaizai672-ops/code-runner/main/install.ps1 | iex
```

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/liumaizai672-ops/code-runner/main/install.sh | bash
```

**或者直接 clone（最透明，没有中间脚本）**

```bash
git clone https://github.com/liumaizai672-ops/code-runner.git ~/.workbuddy/skills/code-runner
```

装完**新开一个对话**即可生效。

### 安装脚本做了什么

1. 把仓库放到 `~/.workbuddy/skills/code-runner/`（已是 git 检出则原地更新）
2. 校验 `SKILL.md`、`scripts/run.py` 是否齐全
3. 探测本机编译器，列出哪些语言可用
4. 没装 git 时自动降级成 zip 下载

> C++ 编译器缺失时，安装脚本会自动下载便携版 w64devkit（约 64MB）到
> `~/.workbuddy/binaries/mingw64/`，**不改系统 PATH、不需要管理员权限**。
> 不想装可先设 `CODE_RUNNER_SKIP_TOOLCHAIN=1`。

---

## 它凭什么"无条件执行"

五条铁律写在 `SKILL.md` 里，每次触发都会遵守：

| # | 铁律 | 具体表现 |
|---|---|---|
| 1 | **不追问** | 缺省信息自己定：没说语言就选最合适的，没说输入就内置样例 |
| 2 | **必须真跑** | 交付物是运行结果，不是代码片段 |
| 3 | **自我修复** | 编译/运行报错自己改，同一处最多修 3 轮，再不通就换实现思路 |
| 4 | **报告事实** | 贴真实 stdout/stderr，不美化、不脑补 |
| 5 | **不越界** | 不删盘、不提权、不写病毒木马；其余一律照做 |

第 5 条是硬边界。想让它连安装编译器都静默处理可以，但破坏性系统操作和恶意代码不在此列。

---

## 支持的语言

| 语言 | 编译/运行 | 本机实测 |
|---|---|---|
| C++ | `g++ -std=c++17 -O2 -Wall -Wextra` | ✅ GCC 16.2.0 |
| C | `gcc -std=c17 -O2 -lm` | ✅ |
| Java | `javac -encoding UTF-8` + `java` | ✅ JDK 17 |
| Python | 托管解释器 | ✅ 3.13 |
| JavaScript | Node | ✅ 22 |
| Go | `go run`（缓存隔离到临时目录） | 需本机有 go |
| Rust | `rustc -O` | 需本机有 rustc |
| C# | `dotnet` | 需本机有 .NET SDK |

缺工具链不会卡住任务：会说清楚"本机缺 X，已用 Y 实现"，而不是停下来问你装不装。

---

## 用法示例

```
"用 Java 写快排，跑一组乱序数据"
"这段 C++ 报错了：<贴报错>，修一下并重跑"
"读 input.txt 统计词频，输出前 10"
"实现 Dijkstra，用 5 个节点测试并打印路径"
"帮我把这个 Python 脚本改成 C++，性能要快"
```

---

## 工作原理

```
code-runner/
├── SKILL.md                    # 执行协议：铁律 + 五步工作流 + 降级表
├── scripts/
│   ├── toolchain.py            # 探测编译器，24h 缓存，CODE_RUNNER_<TOOL> 可覆盖
│   └── run.py                  # 沙箱编译运行器，输出结构化 JSON
├── references/
│   ├── languages.md            # 各语言写法陷阱（Scanner 吃空行、cin.ignore…）
│   ├── errors.md               # 40+ 条「报错 → 直接改法」对照表
│   └── toolchain-install.md    # 缺编译器的便携安装法
└── assets/templates/           # 6 种语言的干净骨架，复制即用
```

`run.py` 在临时目录里编译运行，**不污染你的工作区**，结束后自动清理。

```jsonc
{
  "ok": true,
  "language": "cpp",
  "compile": { "code": 0, "duration_ms": 2252 },
  "run": {
    "code": 0,
    "stdout": "1 2 3 \ncpp-ok\n",
    "stderr": "",
    "timed_out": false,
    "duration_ms": 295
  }
}
```

退出码：`0` 成功 / `1` 编译或运行失败 / `2` 缺工具链 / `3` 路径错误。
默认 15 秒超时，死循环会被回收，不会挂住会话。

---

## 卸载

```bash
rm -rf ~/.workbuddy/skills/code-runner
```

可选一并删掉自动装的编译器：`~/.workbuddy/binaries/mingw64/`。

---

## License

MIT，见 [LICENSE](LICENSE)。
