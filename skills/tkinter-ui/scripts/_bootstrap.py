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
    bases = [
        Path.cwd(),
        skill_dir(),
        skill_dir() / "runtime" / "vendor",
        skill_dir() / "runtime",
    ]
    if len(skill_dir().parents) > 1:
        bases.append(skill_dir().parents[1])
    if env:
        override = Path(env).expanduser()
        bases.extend([override, override / name, override.parent])
    for base in bases:
        for package in (base / name, base / f"{name}-main" / name, base):
            if package.name == name and (package / "__init__.py").is_file():
                _add_path(package.parent.resolve())
                return package.parent
    return None
