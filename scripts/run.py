#!/usr/bin/env python3
"""Universal code executor.

Compiles (when the language needs it) and runs a source file or project directory
in an isolated temp workspace, then reports structured JSON with real output.

Usage:
    run.py <path> [--lang LANG] [--stdin TEXT] [--arg X ...] [--timeout SEC]
                 [--keep] [--cwd DIR]

Exit code: 0 when the program ran and returned 0, 1 when it failed to build/run,
2 when the toolchain for that language is missing, 3 on bad input.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import toolchain  # noqa: E402

EXT_LANG = {
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".c++": "cpp", ".hpp": "cpp", ".h": "cpp",
    ".c": "c",
    ".java": "java",
    ".py": "python", ".pyw": "python",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".cs": "csharp",
    ".kt": "kotlin",
    ".sh": "bash",
    ".rb": "ruby",
    ".php": "php",
}

NEEDS_BUILD = {"cpp", "c", "java", "go", "rust", "csharp", "kotlin"}
CREATIONFLAGS = 0x00000200 if os.name == "nt" else 0  # CREATE_NEW_PROCESS_GROUP


# ----------------------------------------------------------------------------- helpers
def detect_language(path: Path) -> str:
    if path.is_dir():
        files = [p for p in path.rglob("*") if p.is_file()]
        counts: dict[str, int] = {}
        for f in files:
            lang = EXT_LANG.get(f.suffix.lower())
            if lang:
                counts[lang] = counts.get(lang, 0) + 1
        if not counts:
            raise SystemExit(f"no recognizable source files under {path}")
        return max(counts, key=counts.get)
    lang = EXT_LANG.get(path.suffix.lower())
    if not lang:
        raise SystemExit(f"cannot infer language from extension '{path.suffix}'")
    return lang


def run_cmd(cmd: list[str], cwd: Path, timeout: int, stdin_text: str = "", env: dict | None = None):
    started = time.time()
    full_env = {**os.environ, **(env or {})}
    full_env.setdefault("PYTHONIOENCODING", "utf-8")
    full_env.setdefault("PYTHONUTF8", "1")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            input=(stdin_text or "").encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=full_env,
            creationflags=CREATIONFLAGS,
        )
        out = proc.stdout.decode("utf-8", "replace")
        err = proc.stderr.decode("utf-8", "replace")
        code = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or b"").decode("utf-8", "replace")
        err = (exc.stderr or b"").decode("utf-8", "replace")
        code = -1
        timed_out = True
    return {
        "cmd": " ".join(cmd),
        "code": code,
        "stdout": out,
        "stderr": err,
        "timed_out": timed_out,
        "duration_ms": int((time.time() - started) * 1000),
    }


def java_entry(path: Path) -> tuple[str | None, str | None]:
    """Return (package, public type name) declared in a single .java file."""
    text = path.read_text("utf-8", "replace")
    pkg = None
    m = re.search(r"^\s*package\s+([\w.]+)\s*;", text, re.MULTILINE)
    if m:
        pkg = m.group(1)
    cls = None
    m = re.search(
        r"\bpublic\s+(?:final\s+|abstract\s+|sealed\s+|static\s+)*"
        r"(?:class|interface|enum|record|@interface)\s+(\w+)",
        text,
    )
    if m:
        cls = m.group(1)
    else:
        m = re.search(r"\b(?:class|interface|enum|record)\s+(\w+)", text)
        if m:
            cls = m.group(1)
    return pkg, cls


# ----------------------------------------------------------------------------- per-language
def build_and_run(lang: str, src: Path, work: Path, args, timeout: int, stdin_text: str):
    """Return (result|None, error|None)."""
    tools = toolchain.probe()
    result: dict = {"language": lang, "compile": None, "run": None}

    if lang in ("python", "javascript", "bash", "ruby", "php", "typescript"):
        interp = {
            "python": "python", "javascript": "node", "bash": "bash",
            "ruby": "ruby", "php": "php", "typescript": "node",
        }[lang]
        exe = tools.get(interp)
        if not exe:
            return None, f"interpreter '{interp}' not found"
        target = work / src.name
        result["run"] = run_cmd([exe, str(target), *args], work, timeout, stdin_text)
        return result, None

    if lang in ("cpp", "c"):
        compiler = tools.get("g++" if lang == "cpp" else "gcc")
        if not compiler:
            return None, "g++ not found"
        sources = sorted(p for p in work.rglob("*") if p.suffix.lower() in
                         ({".cpp", ".cc", ".cxx", ".c"} if lang == "cpp" else {".c"}))
        binary = work / ("prog.exe" if os.name == "nt" else "prog")
        if lang == "cpp":
            cmd = [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra",
                   "-o", str(binary), *[str(s) for s in sources]]
        else:
            cmd = [compiler, "-std=c17", "-O2", "-Wall", "-o", str(binary),
                   *[str(s) for s in sources], "-lm"]
        result["compile"] = run_cmd(cmd, work, max(timeout, 60))
        if result["compile"]["code"] != 0:
            return result, None
        result["run"] = run_cmd([str(binary), *args], work, timeout, stdin_text)
        return result, None

    if lang == "java":
        javac, java = tools.get("javac"), tools.get("java")
        if not javac or not java:
            return None, "javac/java not found"
        entry_class = None
        if src.is_file():
            copy_path = work / src.name
            pkg, cls = java_entry(copy_path)
            entry_class = f"{pkg}.{cls}" if pkg and cls else cls
            if cls:
                dest_dir = work / Path(pkg.replace(".", "/")) if pkg else work
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / f"{cls}.java"
                if dest != copy_path:
                    copy_path.replace(dest)  # 必须移动而非复制，否则同一类被编译两次
        else:
            for f in work.rglob("*.java"):
                pkg, cls = java_entry(f)
                if pkg and f.parent == work:
                    dest_dir = work / Path(pkg.replace(".", "/"))
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(f), str(dest_dir / f.name))
                if cls and entry_class is None:
                    entry_class = f"{pkg}.{cls}" if pkg else cls
            entry_class = entry_class or "Main"

        java_files = sorted(str(p) for p in work.rglob("*.java"))
        classes = work / "classes"
        classes.mkdir(exist_ok=True)
        result["compile"] = run_cmd(
            [javac, "-encoding", "UTF-8", "-d", str(classes), *java_files],
            work, max(timeout, 60),
        )
        if result["compile"]["code"] != 0:
            return result, None
        result["run"] = run_cmd(
            [java, "-Dfile.encoding=UTF-8", "-Dstdout.encoding=UTF-8",
             "-Dstderr.encoding=UTF-8", "-cp", str(classes), entry_class, *args],
            work, timeout, stdin_text,
        )
        return result, None

    if lang == "go":
        go = tools.get("go")
        if not go:
            return None, "go not found"
        env = {"GOCACHE": str(work / ".gocache"), "GOPATH": str(work / ".gopath"),
               "GO111MODULE": "off", "GOFLAGS": "-mod=mod"}
        (work / ".gocache").mkdir(exist_ok=True)
        (work / ".gopath").mkdir(exist_ok=True)
        if src.is_file():
            target = work / src.name
            result["run"] = run_cmd([go, "run", str(target), *args], work, max(timeout, 120), stdin_text, env)
        else:
            result["compile"] = run_cmd([go, "build", "-o", str(work / "prog.exe"), "."],
                                        work, max(timeout, 180), "", env)
            if result["compile"]["code"] != 0:
                return result, None
            result["run"] = run_cmd([str(work / "prog.exe"), *args], work, timeout, stdin_text, env)
        return result, None

    if lang == "rust":
        rustc = tools.get("rustc")
        if not rustc:
            return None, "rustc not found"
        binary = work / ("prog.exe" if os.name == "nt" else "prog")
        result["compile"] = run_cmd(
            [rustc, "-O", "-o", str(binary), str(work / src.name)], work, max(timeout, 120)
        )
        if result["compile"]["code"] != 0:
            return result, None
        result["run"] = run_cmd([str(binary), *args], work, timeout, stdin_text)
        return result, None

    return None, f"no runner implemented for '{lang}'"


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Compile and run a program, return JSON.")
    ap.add_argument("path")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--stdin", default="")
    ap.add_argument("--arg", action="append", default=[], dest="args")
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("--keep", action="store_true", help="keep temp workspace and print its path")
    ap.add_argument("--cwd", default=None, help="extra files (e.g. input.txt) to copy into the workspace")
    a = ap.parse_args()

    src = Path(a.path).resolve()
    if not src.exists():
        print(json.dumps({"ok": False, "error": f"path not found: {src}"}, ensure_ascii=False))
        return 3

    lang = a.lang or detect_language(src)
    work = Path(tempfile.mkdtemp(prefix="coderunner_"))

    try:
        if src.is_file():
            shutil.copy2(src, work / src.name)
        else:
            shutil.copytree(src, work / "src")
            work = work / "src"
        if a.cwd:
            extra = Path(a.cwd)
            if extra.is_dir():
                for f in extra.iterdir():
                    if f.is_file():
                        shutil.copy2(f, work / f.name)

        result, error = build_and_run(lang, src, work, a.args, a.timeout, a.stdin)

        if error:
            payload = {"ok": False, "language": lang, "error": error,
                       "hint": "run scripts/toolchain.py to see what is available; install the missing toolchain or pick another language"}
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 2

        run = result["run"]
        ok = bool(run) and run["code"] == 0 and not run["timed_out"]
        payload = {
            "ok": ok,
            "language": lang,
            "workspace": str(work),
            "compile": result["compile"],
            "run": run,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if ok else 1
    finally:
        if not a.keep:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
