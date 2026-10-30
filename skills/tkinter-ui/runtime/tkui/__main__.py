"""Command line interface: catalog, schema, prompt, check, run, demo, choose."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


def _print(text=""):
    print(text)


def _load_actions(path):
    if not path:
        return {}
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("tkui_user_actions", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载动作文件：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    actions = {}
    for name in dir(module):
        if name.startswith("_"):
            continue
        value = getattr(module, name)
        if callable(value) and getattr(value, "__module__", None) == module.__name__:
            actions[name] = value
    return actions


def _style_arg(value):
    from .theme import normalize_style
    if value == "ask":
        return "ask"
    return normalize_style(value, allow_auto=False)


def cmd_catalog(args):
    from . import catalog, to_markdown
    if args.markdown:
        text = to_markdown()
    else:
        text = json.dumps(catalog(), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        _print(f"已写入 {args.output}")
    else:
        _print(text)


def cmd_schema(args):
    from .spec import json_schema
    text = json.dumps(json_schema(), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        _print(f"已写入 {args.output}")
    else:
        _print(text)


def cmd_prompt(args):
    from .ai import prompt
    text = prompt()
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        _print(f"已写入 {args.output}")
    else:
        _print(text)


def cmd_check(args):
    from .spec import SpecError, load
    try:
        spec = load(args.spec)
        from .spec import validate
        issues, actions = validate(spec, strict=not args.no_strict)
    except SpecError as exc:
        if args.json:
            _print(json.dumps({"ok": False, "issues": [
                {"path": item.path, "message": item.message, "level": item.level}
                for item in exc.issues]}, ensure_ascii=False, indent=2))
        else:
            _print(str(exc))
        return 1
    errors = [item for item in issues if item.level == "error"]
    if args.json:
        _print(json.dumps({
            "ok": not errors,
            "issues": [{"path": item.path, "message": item.message, "level": item.level}
                       for item in issues],
            "actions": sorted(actions),
        }, ensure_ascii=False, indent=2))
    else:
        if issues:
            _print(f"{len(issues)} 条提示：")
            for item in issues:
                _print("  " + str(item))
        if errors:
            _print(f"校验失败：{len(errors)} 个错误")
        else:
            _print("规格有效。" + (f" Python 动作：{', '.join(sorted(actions)) or '无'}" if actions else ""))
    return 1 if errors else 0


def cmd_run(args):
    import tkui
    from .actions import ActionError
    from .backends import BackendError
    from .spec import SpecError

    style = None
    if args.style:
        style = _style_arg(args.style)
        if style == "ask":
            style = tkui.choose_style()
    try:
        actions = _load_actions(args.actions)
        app = tkui.App(args.spec, style=style, actions=actions)
        app.run()
    except (SpecError, BackendError, ActionError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


def cmd_demo(args):
    from .demo import run_demo
    style = None
    if args.style:
        style = _style_arg(args.style)
    return run_demo(style=style, page=args.page, choose=getattr(args, "choose", False))


def cmd_choose(args):
    import tkui
    style = tkui.choose_style(default=args.default, remember=not args.no_remember)
    if args.run:
        app = tkui.App(args.run, style=style)
        app.run()
        return 0
    if args.json:
        _print(json.dumps({"style": style, "info": tkui.describe(style)},
                          ensure_ascii=False, indent=2))
    else:
        _print(style)
    return 0


def cmd_styles(args):
    import tkui
    if args.json:
        _print(json.dumps({key: tkui.describe(key) for key in tkui.STYLES},
                          ensure_ascii=False, indent=2))
        return 0
    for key in tkui.STYLES:
        info = tkui.STYLE_INFO[key]
        _print(f"{key:5} {info['label']:16} {info['short']:18} {info['library']}")
        _print(f"      {info['summary']}")
    return 0


def cmd_info(args):
    import tkui
    import subprocess
    result = {"default": tkui.resolve_style(), "loaded": {}, "errors": {}}
    for style in tkui.STYLES:
        code = (
            "import json;"
            "from tkui.backends import backend_info;"
            f"print(json.dumps(backend_info({style!r}), ensure_ascii=False))"
        )
        proc = subprocess.run([sys.executable, "-c", code],
                              capture_output=True, text=True, encoding="utf-8")
        if proc.returncode == 0:
            try:
                result["loaded"][style] = json.loads(proc.stdout)
            except ValueError:
                result["errors"][style] = proc.stdout.strip() or proc.stderr.strip()
        else:
            result["errors"][style] = proc.stderr.strip() or proc.stdout.strip()
    _print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not result["errors"] else 1


def build_parser():
    from . import __version__
    parser = argparse.ArgumentParser(
        prog="python -m tkui",
        description="TkUI：一套声明式界面，两种外观（Web / Windows 11 Fluent）。",
    )
    parser.add_argument("--version", action="version", version=f"tkui {__version__}")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("catalog", help="输出组件目录（JSON 或 Markdown）")
    p.add_argument("--markdown", action="store_true")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_catalog)

    p = sub.add_parser("schema", help="输出 JSON Schema")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_schema)

    p = sub.add_parser("prompt", help="输出给 AI 的提示词")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_prompt)

    p = sub.add_parser("check", help="校验规格文件")
    p.add_argument("spec")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-strict", action="store_true", help="忽略未知字段提示")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("run", help="运行规格文件")
    p.add_argument("spec")
    p.add_argument("--style", "-s", help="web / win11 / auto / ask")
    p.add_argument("--actions", help="可选的 Python 动作文件")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("demo", help="运行组件画廊")
    p.add_argument("--style", "-s", help="web / win11 / auto / ask")
    p.add_argument("--page", help="初始页面 key")
    p.add_argument("--choose", action="store_true", help="启动前弹出风格选择")
    p.set_defaults(func=cmd_demo)

    p = sub.add_parser("choose", help="弹出风格选择对话框")
    p.add_argument("--default")
    p.add_argument("--no-remember", action="store_true")
    p.add_argument("--run", help="选择后运行指定规格")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_choose)

    p = sub.add_parser("styles", help="列出两种风格")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_styles)

    p = sub.add_parser("info", help="显示后端位置和版本")
    p.set_defaults(func=cmd_info)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
