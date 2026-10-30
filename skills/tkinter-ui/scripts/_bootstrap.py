"""Locate the bundled TkUI runtime and upstream libraries."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _add_path(path):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)
    current = os.environ.get("PYTHONPATH", "")
    parts = [item for item in current.split(os.pathsep) if item]
    if text not in parts:
        os.environ["PYTHONPATH"] = os.pathsep.join([text, *parts])


def skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def runtime_candidates():
    env = os.environ.get("TKUI_HOME")
    if env:
        path = Path(env).expanduser()
        yield path
        yield path.parent
    yield skill_dir() / "runtime"
    yield skill_dir().parents[1]          # repo root next to tkui/
    yield Path.cwd()


def add_runtime():
    """Insert the first directory containing a ``tkui`` package."""
    tried = []
    for base in runtime_candidates():
        try:
            base = Path(base).resolve()
        except OSError:
            continue
        package = base / "tkui"
        if (package / "__init__.py").is_file():
            _add_path(base)
            return base
        tried.append(str(base))
    raise SystemExit(
        "找不到 tkui 运行时。把 tkui 包放进 skill 的 runtime/，"
        "或设置 TKUI_HOME 指向包含 tkui/ 的目录。\n已尝试：\n  "
        + "\n  ".join(tried)
    )


def add_upstream(name):
    """Best-effort sys.path setup for a sibling upstream checkout."""
    env = os.environ.get("TKUI_TKWEBUI_PATH" if name == "tkwebui" else "TKUI_TKWIN11_PATH")
    candidates = []
    if env:
        candidates.append(Path(env).expanduser())
    for base in (Path.cwd(), skill_dir(), skill_dir().parents[1]):
        candidates.append(base / f"{name}-main")
        candidates.append(base / name)
    for candidate in candidates:
        package = candidate / name
        if (package / "__init__.py").is_file():
            _add_path(candidate.resolve())
            return candidate
    return None
