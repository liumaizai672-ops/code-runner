# 报错 → 改法 对照表

自愈循环时按这张表直接改，不要原样重跑。

## C++ / g++

| 报错 | 原因 | 改法 |
|---|---|---|
| `'sort' was not declared in this scope` | 缺头文件 | 加 `#include <algorithm>` |
| `'vector' has not been declared` / `'vector' is not a member of 'std'` | 只写了 `vector` 或漏 include | 加 `#include <vector>`，写 `std::vector` |
| `expected ';' before ...` | 上一行结尾漏分号 | 查上一行 |
| `undefined reference to 'main'` | 入口写成 `Main`/`mian`，或文件不在编译列表 | 确认 `int main()`，多文件时把全部 `.cpp` 交给编译器 |
| `undefined reference to 'std::__cxx11::...'` | 用 gcc 编 C++ | 换 `g++` |
| `'to_string' was not declared` | 编译器标准过低 | 加 `-std=c++17` |
| `Segmentation fault` （运行时） | 数组越界 / 空指针 / 递归过深 | 打印边界、把大数组移出栈、加深递归改迭代 |
| `terminate called after throwing std::bad_alloc` | 申请内存过大 | 改数据结构，或分块处理 |
| `redefinition of 'xxx'` | 全局重名 | 改名或加 `static` |
| 中文乱码 | 源文件编码/控制台代码页 | 源文件存 UTF-8，执行器按 UTF-8 解码；必要时 `SetConsoleOutputCP(65001)` |

## Java

| 报错 | 原因 | 改法 |
|---|---|---|
| `class X is public, should be declared in a file named X.java` | 类名与文件名不一致 | 文件改名为 `<类名>.java`，或把类改成非 public |
| `cannot find symbol: Scanner` | 缺 import | `import java.util.*;` |
| `incompatible types: possible lossy conversion from double to int` | 类型转换 | 显式 `(int)` 强转 |
| `variable x might not have been initialized` | 局部变量未赋初值 | 声明时给默认值 |
| `java.lang.NullPointerException` | 对象未 new / 数组元素为 null | 定位行号，初始化 |
| `java.util.NoSuchElementException` | Scanner 读到 EOF 还在读 | 加 `hasNext()` / `hasNextInt()` 判断 |
| `StringIndexOutOfBoundsException` | 下标越界 | 检查 `< s.length()` |
| `StackOverflowError` | 递归过深 | 改迭代或显式栈；必要时 `-Xss16m` |
| `ArrayIndexOutOfBoundsException` | 下标越界 | 打印 `length` 与实际下标 |
| `error: unmappable character (0xXX) for encoding GBK` | 源文件 UTF-8 而 javac 用 GBK | 加 `-encoding UTF-8`（执行器已内置） |

## Python

| 报错 | 改法 |
|---|---|
| `IndentationError` / `TabError` | 统一 4 空格，别混 tab |
| `RecursionError` | `sys.setrecursionlimit(10**6)`，或改迭代 |
| `KeyError` | 用 `dict.get(k, default)` |
| `NameError` | 变量拼错或作用域错 |
| `TypeError: can only concatenate str` | 显式 `str()` 转换 |
| 输出多了 `None` | `print(func())` 与 `func` 里已 print 冲突，去掉其一 |

## Node / JavaScript

| 报错 | 改法 |
|---|---|
| `ReferenceError: require is not defined` | 在 ESM 环境用 `import`，或文件改 `.cjs` |
| `SyntaxError: Unexpected token` | 检查是否用了 TS 语法 |
| `TypeError: Cannot read properties of undefined` | 加可选链 `?.` 或判空 |

## Go

| 报错 | 改法 |
|---|---|
| `package command-line-arguments is not a main package` | 加 `package main` |
| `undefined: fmt` | 加 `import "fmt"`，且 import 了必须用 |
| `declared but not used` | 删除未用变量或用 `_` |

## Rust

| 报错 | 改法 |
|---|---|
| `cannot find function ... in this scope` | 补 `use` 或 `std::` 前缀 |
| `borrow of moved value` | 改 `.clone()` 或传引用 `&` |
| `mismatched types` | 显式转换 `as` 或 `.into()` |

## 超时 / 无输出

| 现象 | 原因 | 改法 |
|---|---|---|
| `timed_out: true` | 死循环 / 等不到 EOF | 加 EOF 判断，或提高 `--timeout` |
| stdout 为空但 code=0 | 输出走了 stderr，或缓冲未 flush | 加 `flush`（C: `fflush(stdout)`；Python: `print(..., flush=True)`） |
| 退出码 139 / 3221225477 | 段错误 / 访问冲突 | 见 C++ 段错误一行 |
