"""Static checks for upstream code, or spec checks for JSON."""
from __future__ import annotations

import argparse
import ast
import json
import py_compile
import sys
import tempfile
from pathlib import Path

from _bootstrap import add_runtime


def check_python(path: Path):
    issues = []
    try:
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError) as exc:
        return [{"level": "error", "line": 0, "message": f"无法解析：{exc}"}]
    try:
        with tempfile.TemporaryDirectory() as tmp:
            py_compile.compile(str(path), cfile=str(Path(tmp) / "x.pyc"), doraise=True)
    except py_compile.PyCompileError as exc:
        issues.append({"level": "error", "line": 0, "message": str(exc)})

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in ("tkwebui", "tkwin11"):
                    imported.add(root)
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            if root in ("tkwebui", "tkwin11"):
                imported.add(root)
    if len(imported) > 1:
        issues.append({"level": "error", "line": 0,
                       "message": "同一个 Tk 解释器不能同时导入 tkwebui 与 tkwin11"})

    def calls(name):
        result = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                label = func.id if isinstance(func, ast.Name) else (
                    func.attr if isinstance(func, ast.Attribute) else None)
                if label == name:
                    result.append(node.lineno)
        return sorted(result)

    tk_lines = calls("Tk")
    dpi_lines = calls("enable_dpi_awareness")
    apply_lines = calls("apply_theme")
    install_lines = calls("install")
    if tk_lines and dpi_lines and min(dpi_lines) > min(tk_lines):
        issues.append({"level": "warning", "line": min(dpi_lines),
                       "message": "enable_dpi_awareness 应在 Tk() 之前调用"})
    if tk_lines and install_lines and min(install_lines) > min(tk_lines):
        issues.append({"level": "error", "line": min(install_lines),
                       "message": "tkwin11.install() 必须在第一个 Tk() 之前调用"})
    if tk_lines and apply_lines and min(apply_lines) < min(tk_lines):
        issues.append({"level": "warning", "line": min(apply_lines),
                       "message": "apply_theme(root) 应在 Tk() 之后调用"})

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "Combobox" and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "ttk":
                    issues.append({
                        "level": "warning", "line": node.lineno,
                        "message": "ttk.Combobox 的下拉浮层不受主题控制；需要统一外观时用 ThemedCombobox",
                    })
    if "tkwin11" in imported:
        if tk_lines and not install_lines:
            issues.append({
                "level": "warning", "line": min(tk_lines),
                "message": "新程序可只用 apply_theme；旧程序要连经典 tk 控件一起换肤，需在 Tk() 前 install()",
            })
    return issues


def check_spec(path: Path):
    add_runtime()
    from tkui.spec import SpecError, load, validate

    try:
        spec = load(path)
    except SpecError as exc:
        return [{"level": item.level, "line": 0,
                 "message": f"{item.path}: {item.message}"} for item in exc.issues]
    issues, _ = validate(spec)
    return [{"level": item.level, "line": 0,
             "message": f"{item.path}: {item.message}"} for item in issues]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check TkUI/TkWebUI/TkWin11 code or spec")
    parser.add_argument("target")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    path = Path(args.target)
    if not path.exists():
        print(f"找不到文件：{path}", file=sys.stderr)
        return 2
    issues = check_spec(path) if path.suffix.lower() == ".json" else check_python(path)
    errors = [item for item in issues if item["level"] == "error"]
    if args.json:
        print(json.dumps({"ok": not errors, "target": str(path), "issues": issues},
                         ensure_ascii=False, indent=2))
    else:
        if not issues:
            print(f"{path}: 未发现问题")
        for item in issues:
            line = f":{item['line']}" if item.get("line") else ""
            mark = "错误" if item["level"] == "error" else "提示"
            print(f"{path}{line}: {mark}: {item['message']}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
