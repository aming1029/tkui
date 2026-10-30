"""Copy the repo-level tkui package into the skill runtime/ directory."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main():
    skill = Path(__file__).resolve().parents[1]
    source = skill.parents[1] / "tkui"
    target = skill / "runtime" / "tkui"
    if not (source / "__init__.py").is_file():
        raise SystemExit(f"找不到源运行时：{source}")
    if (target.resolve().parent) != (skill / "runtime").resolve():
        raise SystemExit(f"目标路径异常，拒绝写入：{target}")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(
        source, target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    print(f"已同步 {source} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
