"""Style selection, persistence and the pre-launch style chooser.

Two looks are supported:

``web``
    Modern web-application look (TkWebUI): white surfaces, rounded corners,
    blue accent, static rendering, no animation.

``win11``
    Windows 11 Fluent look (TkWin11): Mica-like workspace, Fluent controls,
    per-monitor DPI, motion and an optional integrated title bar.

The two backends must not be mixed inside one Tk interpreter, so switching
the look restarts the process.  This module keeps the preference in a small
JSON file and provides ``relaunch()`` for that purpose.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

STYLES = ("web", "win11")
DEFAULT_STYLE = "web"
ENV_VAR = "TKUI_STYLE"
CONFIG_ENV = "TKUI_CONFIG"

STYLE_INFO = {
    "web": {
        "label": "Web 应用风",
        "short": "现代 Web / SaaS",
        "library": "TkWebUI",
        "accent": "#087DFF",
        "surface": "#FFFFFF",
        "summary": "白底、圆角、克制的蓝色主色，静态渲染。适合科研、工程、内部数据处理工具。",
        "bullets": [
            "样式在启动时一次生成，运行中稳定可预期",
            "无过渡动画，切换页面几乎不增加开销",
            "圆角卡片、清晰表单、表格与图表是重点",
            "依赖少，源码易于阅读和修改",
        ],
    },
    "win11": {
        "label": "Windows 11 风",
        "short": "Fluent / WinUI 3",
        "library": "TkWin11",
        "accent": "#0067C0",
        "surface": "#FDFEFE",
        "summary": "Windows 11 Fluent 外观，Mica 风格工作区、悬停/按下/开关动画和每显示器 DPI。",
        "bullets": [
            "一体化标题栏、层级导航和设置卡片",
            "悬停、按下、开关、页面切换都有过渡",
            "每块显示器按自己的缩放比例适配",
            "可连 tk.Button / tk.Menu 等经典控件一起换肤",
        ],
    },
}

_ALIASES = {
    "web": "web",
    "webui": "web",
    "tkwebui": "web",
    "modern": "web",
    "light": "web",
    "win11": "win11",
    "win": "win11",
    "windows": "win11",
    "windows11": "win11",
    "winui": "win11",
    "fluent": "win11",
    "tkwin11": "win11",
}


class StyleError(ValueError):
    """Raised when a style name is not understood or cannot be used."""


def normalize_style(value, *, allow_auto: bool = True):
    """Return ``'web'``, ``'win11'``, ``None`` (auto) or raise StyleError."""
    if value is None or value == "":
        return None
    text = str(value).strip().lower().replace("-", "").replace("_", "")
    if allow_auto and text in ("auto", "system", "default"):
        return None
    style = _ALIASES.get(text)
    if style is None:
        raise StyleError(
            f"未知风格 {value!r}，可选：web（现代 Web 风）、win11（Windows 11 Fluent 风）、auto"
        )
    return style


def config_path() -> Path:
    override = os.environ.get(CONFIG_ENV)
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "tkui" / "config.json"
    xdg = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(xdg) / "tkui" / "config.json"


def read_config() -> dict:
    path = config_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_config(data: dict) -> Path:
    path = config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        # A read-only profile must not prevent the application from starting.
        pass
    return path


def saved_style():
    """Return the remembered style, or ``None``."""
    try:
        return normalize_style(read_config().get("style"))
    except StyleError:
        return None


def save_style(style: str, **extra):
    style = normalize_style(style, allow_auto=False)
    data = read_config()
    data["style"] = style
    data.update(extra)
    return write_config(data)


def resolve_style(explicit=None, *, use_env: bool = True, use_config: bool = True,
                  default: str = DEFAULT_STYLE) -> str:
    """Resolve the effective style.

    Priority: explicit argument → ``TKUI_STYLE`` → saved preference → default.
    ``auto`` skips to the next source.
    """
    style = normalize_style(explicit)
    if style is not None:
        return style
    if use_env:
        style = normalize_style(os.environ.get(ENV_VAR))
        if style is not None:
            return style
    if use_config:
        style = saved_style()
        if style is not None:
            return style
    return normalize_style(default, allow_auto=False) or DEFAULT_STYLE


def describe(style: str) -> dict:
    style = normalize_style(style, allow_auto=False)
    return dict(STYLE_INFO[style], key=style)


def _create_chooser_window(parent, default):
    import tkinter as tk
    from tkinter import font as tkfont

    own_root = parent is None and tk._default_root is None
    if own_root:
        root = tk.Tk()
        win = root
    elif parent is None:
        win = tk.Toplevel(tk._default_root)
        root = tk._default_root
    else:
        win = tk.Toplevel(parent)
        root = parent.winfo_toplevel()

    win.title("选择界面风格 · TkUI")
    win.resizable(False, False)
    win.configure(background="#F4F6F9")
    try:
        win.transient(root)
    except Exception:
        pass

    default_font = tkfont.nametofont("TkDefaultFont")
    family = default_font.actual("family")
    base = max(9, int(default_font.actual("size")))

    width, height = 820, 600
    win.update_idletasks()
    x = max(0, (win.winfo_screenwidth() - width) // 2)
    y = max(0, (win.winfo_screenheight() - height) // 3)
    win.geometry(f"{width}x{height}+{x}+{y}")

    result = {"style": None}

    header = tk.Frame(win, background="#F4F6F9")
    header.pack(fill="x", padx=30, pady=(26, 6))
    tk.Label(header, text="选择界面风格", font=(family, base + 11, "bold"),
             background="#F4F6F9", foreground="#15181E").pack(anchor="w")
    tk.Label(header, text="同一份界面代码与组件声明，可以换成两种外观。选择会保存为默认值，之后可随时切换。",
             font=(family, base), background="#F4F6F9", foreground="#67707C").pack(anchor="w", pady=(6, 0))

    body = tk.Frame(win, background="#F4F6F9")
    body.pack(fill="both", expand=True, padx=26, pady=(14, 18))

    cards = {}

    def choose(style):
        result["style"] = style
        win.destroy()

    for index, (style, info) in enumerate(STYLE_INFO.items()):
        card = tk.Frame(body, background="#FFFFFF", highlightthickness=1,
                        highlightbackground="#DDE2E9", bd=0)
        card.grid(row=0, column=index, sticky="nsew", padx=(0, 12) if index == 0 else (12, 0))
        body.grid_columnconfigure(index, weight=1)
        body.grid_rowconfigure(0, weight=1)
        cards[style] = card

        accent = tk.Frame(card, background=info["accent"], height=6)
        accent.pack(fill="x")

        inner = tk.Frame(card, background="#FFFFFF", padx=22, pady=18)
        inner.pack(fill="both", expand=True)
        top = tk.Frame(inner, background="#FFFFFF")
        top.pack(fill="x")
        tk.Label(top, text=info["label"], font=(family, base + 5, "bold"),
                 background="#FFFFFF", foreground="#15181E").pack(side="left")
        if style == default:
            tk.Label(top, text=" 当前 ", font=(family, max(8, base - 1)),
                     background="#E8F1FF", foreground="#0B5CAD").pack(side="right", pady=2)

        tk.Label(inner, text=f"{info['short']} · {info['library']}",
                 font=(family, base), background="#FFFFFF", foreground=info["accent"]).pack(anchor="w", pady=(6, 10))

        preview = tk.Canvas(inner, height=90, background="#FFFFFF", highlightthickness=0)
        preview.pack(fill="x", pady=(0, 12))
        preview.bind("<Configure>", lambda event, c=preview, s=style: _paint_preview(c, event.width, s))

        for line in info["bullets"]:
            row = tk.Frame(inner, background="#FFFFFF")
            row.pack(fill="x", pady=3)
            tk.Label(row, text="•", font=(family, base + 1), background="#FFFFFF",
                     foreground=info["accent"]).pack(side="left", anchor="n")
            tk.Label(row, text=line, font=(family, base), background="#FFFFFF",
                     foreground="#4A5360", justify="left", wraplength=250).pack(side="left", padx=(8, 0), anchor="w")

        button = tk.Button(inner, text=f"使用 {info['label']}",
                           font=(family, base + 1, "bold"), relief="flat", bd=0,
                           background=info["accent"], foreground="#FFFFFF",
                           activebackground=info["accent"], activeforeground="#FFFFFF",
                           cursor="hand2", padx=18, pady=9,
                           command=lambda s=style: choose(s))
        button.pack(side="bottom", fill="x", pady=(16, 0))

    footer = tk.Frame(win, background="#F4F6F9")
    footer.pack(fill="x", padx=30, pady=(0, 18))
    tk.Label(footer, text="提示：两种主题不要在同一 Tk 解释器里混用；切换风格时程序会自动重启。",
             font=(family, max(8, base - 1)), background="#F4F6F9", foreground="#7A838F").pack(side="left")
    cancel = tk.Button(footer, text="保持默认", relief="flat", bd=0, background="#F4F6F9",
                       foreground="#4A5360", activebackground="#E8EBF0", cursor="hand2",
                       padx=12, pady=6, command=lambda: choose(default))
    cancel.pack(side="right")

    try:
        win.grab_set()
    except Exception:
        pass
    win.bind("<Escape>", lambda event: choose(default))
    win.protocol("WM_DELETE_WINDOW", lambda: choose(default))
    win.focus_force()
    win.wait_window()
    if own_root:
        try:
            root.destroy()
        except Exception:
            pass
    return result["style"] or default


def _paint_preview(canvas, width, style):
    """A tiny abstract layout preview, painted without importing a theme."""
    canvas.delete("all")
    info = STYLE_INFO[style]
    width = max(width, 80)
    if style == "web":
        canvas.configure(background="#F7F9FC")
        canvas.create_rectangle(0, 0, width, 100, fill="#F7F9FC", outline="")
        canvas.create_rectangle(14, 14, width - 14, 86, fill="#FFFFFF", outline="#E3E7ED")
        canvas.create_rectangle(28, 28, 86, 38, fill="#DCE7F7", outline="")
        canvas.create_rectangle(28, 48, width * .55, 72, fill="#EEF2F7", outline="")
        canvas.create_rectangle(width * .62, 48, width - 28, 72, fill=info["accent"], outline="")
        canvas.create_rectangle(28, 78, width * .35, 82, fill="#E3E7ED", outline="")
    else:
        canvas.configure(background="#F7FAFC")
        canvas.create_rectangle(0, 0, width, 100, fill="#F7FAFC", outline="")
        canvas.create_rectangle(0, 0, 70, 100, fill="#EEF5F9", outline="")
        for i, y in enumerate((20, 38, 56, 74)):
            canvas.create_rectangle(12, y - 3, 58, y + 3,
                                    fill=info["accent"] if i == 0 else "#D4E2EC", outline="")
        canvas.create_rectangle(84, 14, width - 14, 48, fill="#FFFFFF", outline="#DDE6ED")
        canvas.create_oval(width - 44, 23, width - 22, 45, fill="#FFFFFF", outline="#BFC9D2")
        canvas.create_oval(width - 27, 27, width - 17, 37, fill=info["accent"], outline="")
        canvas.create_rectangle(84, 58, width * .56, 88, fill="#FFFFFF", outline="#DDE6ED")
        canvas.create_rectangle(width * .62, 58, width - 14, 88, fill="#FFFFFF", outline="#DDE6ED")


def choose_style(default=None, *, remember: bool = True, parent=None) -> str:
    """Show a small, dependency-free style chooser and return the choice.

    Safe to call before any themed root exists.  If ``remember`` is true the
    choice is written to the user config so later launches use it by default.
    """
    fallback = resolve_style(default)
    # ``remember=False`` must not make a stale preference win over ``default``.
    if default is not None:
        fallback = normalize_style(default, allow_auto=False) or fallback
    choice = _create_chooser_window(parent, fallback)
    if remember and choice:
        save_style(choice)
    return choice


def _style_rewrite(args, style):
    args = list(args)
    cleaned = []
    skip = False
    for item in args:
        if skip:
            skip = False
            continue
        if item in ("--style", "-s"):
            skip = True
            continue
        if item.startswith("--style="):
            continue
        if item == "--choose":
            continue
        cleaned.append(item)
    cleaned.extend(["--style", style])
    return cleaned


def relaunch(style, *, argv=None, app=None, exit_after=True, wait=False):
    """Save ``style`` and start a fresh process using the same command line.

    The two theme libraries cannot coexist in one Tk interpreter, so a full
    restart is the only safe way to switch at runtime.
    """
    style = normalize_style(style, allow_auto=False)
    save_style(style)
    args = list(sys.argv if argv is None else argv)
    script = Path(args[0]).resolve() if args else None
    rest = _style_rewrite(args[1:], style)
    if script is not None and script.name == "__main__.py" and script.parent.name == "tkui":
        command = [sys.executable, "-m", "tkui", *rest]
    elif script is not None and script.exists():
        command = [sys.executable, str(script), *rest]
    else:
        command = [sys.executable, "-m", "tkui", *rest]
    env = os.environ.copy()
    env[ENV_VAR] = style
    kwargs = {"env": env, "cwd": os.getcwd()}
    if sys.platform == "win32":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    if wait:
        subprocess.run(command, **kwargs)
    else:
        subprocess.Popen(command, **kwargs)
    if exit_after:
        if app is not None:
            try:
                app.destroy()
            except Exception:
                pass
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        finally:
            os._exit(0)
    return command
