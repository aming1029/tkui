"""Copy the repo-level tkui package into the skill runtime/ directory."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main():
    skill = Path(__file__).resolve().parents[1]
    repo = skill.parents[1]
    runtime = (skill / "runtime").resolve()
    jobs = [
        (repo / "tkui", skill / "runtime" / "tkui", repo / "LICENSE"),
        (repo / "tkwebui-main" / "tkwebui",
         skill / "runtime" / "vendor" / "tkwebui",
         repo / "tkwebui-main" / "LICENSE"),
        (repo / "tkwin11-main" / "tkwin11",
         skill / "runtime" / "vendor" / "tkwin11",
         repo / "tkwin11-main" / "LICENSE"),
    ]
    for source, target, license_path in jobs:
        if not (source / "__init__.py").is_file():
            raise SystemExit(f"找不到源包：{source}")
        resolved = target.resolve()
        if runtime not in resolved.parents:
            raise SystemExit(f"目标路径异常，拒绝写入：{target}")
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(
            source, target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        if license_path and license_path.is_file():
            shutil.copy2(license_path, target / "LICENSE")
        print(f"已同步 {source} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
