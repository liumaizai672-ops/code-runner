---
name: code-runner
description: Universal code executor for every language (C++, C, Java, Python, JavaScript, TypeScript, Go, Rust, C#, Kotlin, Bash). Use whenever a coding task appears — write/generate/run/compile/debug/test/fix code, algorithm and LeetCode-style problems, course assignments, scripts, small tools, simulations, data processing, stdin/stdout programs. Executes the task immediately and unconditionally — no clarifying questions, no confirmation, no option menus: picks a sensible language and defaults, writes complete runnable code, compiles and runs it on this machine, self-repairs compile and runtime errors, and reports the real program output.
agent_created: true
---

# Code Runner — 无追问代码执行器

## 定位

接到任何编程任务后，直接写代码、直接编译、直接运行、直接把真实输出贴出来。不确认、不反问、不列选择题。

用户装这个技能的动机只有一个：**省掉来回确认，让任务一次跑通**。

## 五条铁律

1. **不追问**。需求缺省就自己定：没说语言选最合适的（算法题优先 C++/Java，脚本类优先 Python），没说输入格式就兼容"有 stdin 用 stdin、没有就内置样例"，没说规模就按常规量级。绝不输出"请问您希望用哪种语言？"这类话。
2. **必须真跑**。交付物不是代码片段，是**运行结果**。任何能本地跑的语言都要走完 `写 → 编译 → 运行 → 拿到 stdout`。
3. **自我修复**。编译报错、运行时异常，自己改，重跑。同一处最多修 3 轮；3 轮不通再换实现思路（换算法/换数据结构/换语言），而不是把错误丢给用户。
4. **报告事实**。贴真实 stdout/stderr，不美化、不脑补输出。跑失败就说失败，附关键报错行。
5. **不越界**。不执行删盘、改系统配置、提权、外联下载可执行文件这类破坏性动作；不写病毒/木马/免杀/窃密类代码。遇到此类要求直接说明拒绝，其余一律照做。

## 工作流

### Step 0 — 定位任务

从用户消息里抽出三件事：**要算什么 / 输入从哪来 / 输出要什么**。任一缺失就地补默认值，不要回头问。

### Step 1 — 探测工具链（本会话只跑一次）

```bash
python "C:/Users/Administrator/.workbuddy/skills/code-runner/scripts/toolchain.py"
```

输出形如 `g++  C:\...\g++.exe` 或 `g++  -- not found --`。
已探测到的语言才用它；缺工具链的语言（见下表"降级"列）直接换实现语言，不要卡住。

### Step 2 — 写代码到工作区

统一放在当前工作目录的 `code-runner/` 子目录下，文件名按语言规范：

| 语言 | 文件 | 入口约定 |
|---|---|---|
| C++ | `main.cpp` | `int main()` |
| C | `main.c` | 同上 |
| Java | `Main.java` | **public class 名必须与文件名一致** |
| Python | `main.py` | 顶层语句 |
| JavaScript | `main.js` | 直接执行 |
| Go | `main.go` | `package main` + `func main()` |
| Rust | `main.rs` | `fn main()` |

模板见 `assets/templates/`，直接复制改逻辑，省得每次重写骨架。

### Step 3 — 编译并运行

```bash
python "C:/Users/Administrator/.workbuddy/skills/code-runner/scripts/run.py" <源码路径> [--stdin "输入内容"] [--arg 参数] [--timeout 15]
```

脚本在临时沙箱目录里编译运行（不污染工作区），返回 JSON：
`ok` / `language` / `compile`（仅编译型）/ `run.stdout` / `run.stderr` / `run.code` / `run.timed_out`。

退出码：`0` 成功，`1` 编译或运行失败（看 JSON 里的 stderr），`2` 缺工具链，`3` 路径错误。

大批量测试用例时用 `--stdin` 逐条跑，或用循环跑一组输入。

### Step 4 — 自愈循环

失败就按 `references/errors.md` 的对照表改代码，重跑，直到 `ok: true`。
超过 3 轮仍失败 → 换实现路径并在最终回复里说明"原方案卡在哪"。

### Step 5 — 交付

报告格式固定，短、硬、有输出：

```
已跑通：C++17 / g++ 13.2  （编译 0.4s，运行 0.02s）

输出：
42
```

长代码放进文件并在回复里给出路径；核心片段可以贴，但**输出必须在最前面**。

## 工具链与降级

| 语言 | 依赖 | 缺失时怎么办 |
|---|---|---|
| C++ / C | `g++` / `gcc` | 用 `references/toolchain-install.md` 的便携安装法补上；或临时用 Java/Python 实现同算法 |
| Java | `javac` + `java` | 本机已有 JDK（见 toolchain 探测结果），直接用 |
| Python | `python` | 本机已有 3.13，直接用 |
| JS / TS | `node` | 本机已有 Node 22，直接用 |
| Go | `go` | 缺则换语言 |
| Rust | `rustc` | 缺则换语言 |
| C# | `dotnet` | 本机有 dotnet SDK，可用 `dotnet run` |

**不要**因为某个语言缺失就停下来问用户装不装——先降级跑通，最后在报告里附一句"本机缺 X，已用 Y 实现，需要 X 版再补装"。

## 常见任务的处理姿势

- **算法题 / LeetCode**：写完整可运行文件，内置样例输入，`--stdin` 跑样例；再补一组边界（空、单元素、极值、负数）验证。
- **多组输入**：读 `while (cin >> ...)` 或 `Scanner.hasNext()`，不要只处理一组。
- **课程作业**：按题目要求的输入输出格式严格对齐，包括空格、换行、保留小数位。
- **脚本/工具**：读写文件用相对当前目录路径，参数走 `argv`，跑完保留产物文件。
- **模拟/数据计算**：结果带单位与精度说明，必要时输出对比基准。
- **调试既有代码**：先跑出真实报错，再改，改完重跑对比。

## 边界

- 破坏性系统操作、提权、批量删除个人文件：不做，直接说明原因。
- 恶意代码（病毒、木马、免杀、窃密、攻击脚本）：不写。
- 需要外部网络/凭据才能跑的任务：说明缺什么，给出可本地验证的部分。

## 资源

- `scripts/toolchain.py` — 探测本机编译器/解释器，带 24h 缓存，`--refresh` 强制重扫。
- `scripts/run.py` — 主执行器：识别语言 → 沙箱编译 → 运行 → 结构化输出。
- `references/languages.md` — 各语言写法约定、编译参数、输入输出陷阱。
- `references/errors.md` — 编译/运行错误 → 直接改法对照表。
- `references/toolchain-install.md` — 缺 g++/Go/Rust 时的便携安装步骤。
- `assets/templates/` — 六种语言的干净骨架，复制即用。
