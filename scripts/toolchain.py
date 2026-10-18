#!/usr/bin/env python3
"""Locate compilers / interpreters on this machine.

Resolution order per tool:
  1. explicit env override (CODE_RUNNER_<TOOL>)
  2. PATH (shutil.which)
  3. known absolute candidate paths
  4. bounded recursive search under common install roots
Results are cached in the OS temp dir for 24h; delete the cache file to force a rescan.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from pathlib import Path

CACHE_TTL = 24 * 3600
CACHE_FILE = Path(tempfile.gettempdir()) / "code_runner_toolchain.json"

EXE = ".exe" if os.name == "nt" else ""

MINGW_ROOT = Path.home() / ".workbuddy" / "binaries" / "mingw64"

# Absolute candidates, tried in order. Cheap and deterministic — preferred over scanning.
CANDIDATES: dict[str, list[str]] = {
    "g++": [
        str(MINGW_ROOT / "bin" / f"g++{EXE}"),
        r"C:\mingw64\bin\g++.exe",
        r"C:\MinGW\bin\g++.exe",
        r"C:\msys64\ucrt64\bin\g++.exe",
        r"C:\msys64\mingw64\bin\g++.exe",
        r"C:\TDM-GCC-64\bin\g++.exe",
        r"C:\Program Files\LLVM\bin\g++.exe",
    ],
    "gcc": [
        str(MINGW_ROOT / "bin" / f"gcc{EXE}"),
        r"C:\mingw64\bin\gcc.exe",
        r"C:\MinGW\bin\gcc.exe",
        r"C:\msys64\ucrt64\bin\gcc.exe",
    ],
    "javac": [
        r"D:\fb rt\tools\jdk17.0.20_12\bin\javac.exe",
        r"D:\kko\_build\jdk\jdk-17.0.20.1+1\bin\javac.exe",
        r"D:\minec\jdk21\jdk-21.0.12.1+1\bin\javac.exe",
        r"C:\Program Files\Java\jdk-21\bin\javac.exe",
    ],
    "java": [
        r"D:\fb rt\tools\jdk17.0.20_12\bin\java.exe",
        r"D:\kko\_build\jdk\jdk-17.0.20.1+1\bin\java.exe",
        r"D:\minec\jdk21\jdk-21.0.12.1+1\bin\java.exe",
        r"C:\Program Files\Java\jdk-21\bin\java.exe",
    ],
    "python": [
        r"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe",
        r"C:\Program Files\PyManager\python.exe",
    ],
    "node": [
        r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2-6\node.exe",
        r"D:\1111\node.exe",
    ],
    "go": [r"C:\Program Files\Go\bin\go.exe", r"C:\Go\bin\go.exe"],
    "rustc": [str(Path.home() / ".cargo" / "bin" / "rustc.exe")],
    "dotnet": [r"C:\Program Files\dotnet\dotnet.exe"],
}

# Bounded fallback scans: only when candidates miss. (root, filename, max_depth)
SCAN_ROOTS: list[tuple[str, str, int]] = [
    (r"C:\Program Files\Eclipse Adoptium", "javac.exe", 4),
    (r"C:\Program Files\Microsoft", "javac.exe", 4),
    (r"D:\fb rt\tools", "javac.exe", 4),
    (r"D:\kko\_build", "javac.exe", 4),
    (r"D:\minec", "javac.exe", 4),
    (r"C:\msys64", "g++.exe", 3),
    (r"C:\Program Files\LLVM", "g++.exe", 3),
]


def _usable(path: str) -> str | None:
    p = Path(path)
    return str(p) if p.is_file() else None


def _scan(root: str, name: str, depth: int) -> str | None:
    base = Path(root)
    if not base.is_dir():
        return None
    level = [base]
    for _ in range(depth):
        nxt = []
        for d in level:
            try:
                for child in d.iterdir():
                    if child.is_file() and child.name.lower() == name.lower():
                        return str(child)
                    if child.is_dir():
                        nxt.append(child)
            except (PermissionError, OSError):
                continue
        level = nxt
        if not level:
            break
    return None


def find(tool: str) -> str | None:
    override = os.environ.get("CODE_RUNNER_" + tool.upper().replace("+", "_PLUS_"))
    if override and _usable(override):
        return _usable(override)

    onpath = shutil.which(tool)
    if onpath:
        return onpath

    for cand in CANDIDATES.get(tool, []):
        got = _usable(cand)
        if got:
            return got

    fname = tool + EXE
    for root, name, depth in SCAN_ROOTS:
        if name.lower() == fname.lower():
            got = _scan(root, name, depth)
            if got:
                return got
    return None


def probe(use_cache: bool = True) -> dict[str, str | None]:
    if use_cache and CACHE_FILE.is_file():
        try:
            data = json.loads(CACHE_FILE.read_text("utf-8"))
            if time.time() - data.get("_ts", 0) < CACHE_TTL:
                return {k: v for k, v in data.items() if not k.startswith("_")}
        except (ValueError, OSError):
            pass

    result = {tool: find(tool) for tool in CANDIDATES}
    try:
        CACHE_FILE.write_text(
            json.dumps({**result, "_ts": time.time()}, indent=2), "utf-8"
        )
    except OSError:
        pass
    return result


def clear_cache() -> None:
    CACHE_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    import sys

    if "--refresh" in sys.argv:
        clear_cache()
    for name, path in probe(use_cache="--refresh" not in sys.argv).items():
        print(f"{name:8} {path or '-- not found --'}")
