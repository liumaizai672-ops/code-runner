#!/usr/bin/env bash
# code-runner 一键安装（macOS / Linux）
# 用法：
#   curl -fsSL https://raw.githubusercontent.com/liumaizai672-ops/code-runner/main/install.sh | bash
set -euo pipefail

SLUG="liumaizai672-ops/code-runner"
BRANCH="main"
DEST="${CODE_RUNNER_DIR:-$HOME/.workbuddy/skills/code-runner}"

printf '\n  code-runner · AI 代码执行器\n'
printf '  ------------------------------------\n\n'

printf '  [1/3] 获取技能文件\n'
if command -v git >/dev/null 2>&1; then
  if [ -d "$DEST/.git" ]; then
    echo "        已有安装，原地更新"
    git -C "$DEST" fetch --depth 1 origin "$BRANCH" >/dev/null 2>&1
    git -C "$DEST" reset --hard "origin/$BRANCH" >/dev/null 2>&1
  else
    rm -rf "$DEST"
    mkdir -p "$(dirname "$DEST")"
    git clone --depth 1 --branch "$BRANCH" "https://github.com/${SLUG}.git" "$DEST" >/dev/null 2>&1
  fi
else
  echo "        未找到 git，改用 zip 下载"
  tmp="$(mktemp -d)"
  curl -fsSL "https://codeload.github.com/${SLUG}/zip/refs/heads/${BRANCH}" -o "$tmp/cr.zip"
  unzip -q "$tmp/cr.zip" -d "$tmp"
  rm -rf "$DEST"
  mkdir -p "$(dirname "$DEST")"
  mv "$tmp"/*/ "$DEST"
  rm -rf "$tmp"
fi

printf '  [2/3] 校验文件完整性\n'
[ -f "$DEST/SKILL.md" ] || { echo "安装不完整：缺少 SKILL.md" >&2; exit 1; }
[ -f "$DEST/scripts/run.py" ] || { echo "安装不完整：缺少 scripts/run.py" >&2; exit 1; }
echo "        SKILL.md / run.py / toolchain.py 就位"

printf '  [3/3] 探测本机编译器\n'
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -n "$PY" ]; then
  "$PY" "$DEST/scripts/toolchain.py" --refresh || true
else
  echo "        未找到 Python，跳过探测"
fi

printf '\n  安装完成。\n\n'
printf '  新开对话后直接说：\n'
printf '    "用 C++ 写个冒泡排序并运行"\n'
printf '    "Java 实现快排，跑一组样例"\n\n'
printf '  技能目录：%s\n\n' "$DEST"
