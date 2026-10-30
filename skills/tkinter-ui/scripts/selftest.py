"""Validate examples, scaffold generation, and (optionally) render both styles."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from _bootstrap import add_runtime, skill_dir


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true",
                        help="also build the minimal spec in both styles (needs a display)")
    args = parser.parse_args(argv)
    base = add_runtime()
    import tkui

    examples = skill_dir() / "assets" / "examples"
    specs = sorted(examples.glob("*.json"))
    if not specs:
        raise SystemExit("assets/examples 下没有 JSON 示例")
    for path in specs:
        spec = json.loads(path.read_text(encoding="utf-8"))
        issues, _ = tkui.validate(spec)
        errors = [item for item in issues if item.level == "error"]
        if errors:
            raise SystemExit(f"{path.name} 校验失败：\n" + "\n".join(map(str, errors)))
    py_examples = sorted(examples.glob("*.py"))
    for path in py_examples:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        check = subprocess.run(
            [sys.executable, str(skill_dir() / "scripts" / "check.py"), str(path)],
            capture_output=True, text=True, encoding="utf-8")
        if check.returncode:
            raise SystemExit(check.stdout + check.stderr)
    print(f"示例：{len(specs)} 个 JSON + {len(py_examples)} 个 Python 通过；运行时：{base}")

    assets = skill_dir() / "assets"
    for name in ("catalog.json", "tkui-1.schema.json"):
        path = assets / name
        if not path.is_file():
            raise SystemExit(f"缺少资源：{path}")
        json.loads(path.read_text(encoding="utf-8"))
    print("资源：catalog.json / tkui-1.schema.json 可解析")

    scripts = skill_dir() / "scripts"
    with tempfile.TemporaryDirectory() as tmp:
        for style in ("web", "win11"):
            for kind in ("blank", "form", "dashboard"):
                out = Path(tmp) / f"{style}_{kind}.py"
                proc = subprocess.run(
                    [sys.executable, str(scripts / "scaffold.py"),
                     "--style", style, "--kind", kind, "--output", str(out)],
                    capture_output=True, text=True, encoding="utf-8")
                if proc.returncode:
                    raise SystemExit(proc.stderr or proc.stdout)
                compile(out.read_text(encoding="utf-8"), str(out), "exec")
                check = subprocess.run(
                    [sys.executable, str(scripts / "check.py"), str(out)],
                    capture_output=True, text=True, encoding="utf-8")
                if check.returncode:
                    raise SystemExit(check.stdout + check.stderr)
    print("脚手架：web/win11 × blank/form/dashboard 全部生成并可编译")

    if args.render:
        minimal = examples / "minimal.json"
        for style in ("web", "win11"):
            code = (
                "import sys\n"
                f"sys.path.insert(0, {str(skill_dir() / 'scripts')!r})\n"
                "from _bootstrap import add_upstream\n"
                "add_upstream('tkwebui'); add_upstream('tkwin11')\n"
                f"sys.path.insert(0, {str(Path(base))!r})\n"
                "import tkui\n"
                f"app=tkui.App({str(minimal)!r}, style={style!r},"
                " actions={'save': lambda event: None})\n"
                "app.root.withdraw(); app.root.update_idletasks()\n"
                "print(app.info())\n"
                "app.close()\n"
            )
            proc = subprocess.run([sys.executable, "-c", code],
                                  capture_output=True, text=True, encoding="utf-8")
            if proc.returncode:
                raise SystemExit(f"{style} 渲染失败：\n{proc.stdout}\n{proc.stderr}")
            print(f"渲染 {style}：OK")
    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
