# 各语言写法约定

目标是"一次编译通过、一次运行正确"。以下为易踩点清单。

## C++ (C++17, g++)

- 编译参数固定：`-std=c++17 -O2 -Wall -Wextra`。有警告就修，`-Wall` 报的警告常是真 bug。
- 必带 `#include` 自足：`<iostream> <vector> <string> <algorithm> <map> <unordered_map> <set> <queue> <stack> <cmath> <climits> <iomanip> <numeric>`。
- 多组输入：

```cpp
int n;
while (cin >> n) { /* 处理 */ }
```

- 读整行前若已用过 `>>`，先 `cin.ignore()`，否则 `getline` 拿到空串。
- 输出小数：`cout << fixed << setprecision(2)`，别用 `printf` 与 `cout` 混排（同步关掉会乱序）。
- 大数组别放栈上（`int a[1000000]` 会爆栈），用 `vector` 或 `static`。
- 别 `using namespace std;` 之后又定义 `count`/`data`/`rank` 这类同名变量，会和 `std` 冲突。

## Java (JDK 17+)

- **public 类名必须等于文件名**。文件名 `Main.java` → `public class Main`。不一致直接编译失败。
- 平台默认编码在 Windows 上不是 UTF-8，源码含中文时：`javac -encoding UTF-8`，运行加 `-Dfile.encoding=UTF-8`（执行器已内置）。
- 输入用 `Scanner`，注意 `nextInt()` 后接 `nextLine()` 会读到空行：

```java
int n = sc.nextInt();
sc.nextLine();              // 吃掉行尾
String s = sc.nextLine();
```

- 大规模输入用 `BufferedReader` + `StringTokenizer`，`Scanner` 在 1e5 行以上会慢到超时。
- `String` 拼接在循环里改用 `StringBuilder`。
- 递归深度过大会 `StackOverflowError`，改成显式栈或循环。
- 输出用 `System.out.println`，大量输出包一层 `PrintWriter`/`BufferedWriter`。

## Python

- `sys.stdin.read().split()` 一次读全部，比逐行 `input()` 快得多。
- 递归默认上限 1000，深递归先 `sys.setrecursionlimit(10**6)`。
- 输出用 `print`，格式 `f"{x:.2f}"`。

## JavaScript / TypeScript

- Node 无 `prompt`，读 stdin 用：

```js
const data = require('fs').readFileSync(0, 'utf8').trim().split(/\s+/);
```

- `.ts` 需要先转译，无 `tsc` 时降级为 `.js` 实现。

## Go

- 单文件必须是 `package main` + `func main()`。
- 输入：`fmt.Scan` 或 `bufio.Scanner`（大数据量用后者）。
- 执行器已设置 `GOCACHE`/`GOPATH` 到临时目录，不会碰用户全局缓存。

## Rust

- `rustc -O` 直接编译单文件；多文件/依赖 crate 需要 Cargo，临时任务尽量单文件。
- 输入：`std::io::stdin().read_to_string(&mut s)`。

## C

- `gcc -std=c17 -O2 -lm`；用 `scanf` 时注意格式符与变量类型匹配（`%d` 配 `int`，`%lf` 配 `double`）。

## 通用

- 程序必须**自己终止**：不要 `while(true)` 等输入却没有 EOF 保护，执行器 15s 会判超时。
- 时间/内存敏感任务，先估算复杂度再写，别写完才发现 1e9 不可行。
