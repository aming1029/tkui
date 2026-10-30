"""Locate and load exactly one theme backend.

Both upstream projects expose nearly the same public names, but they must not
be imported into the same Tk interpreter.  This module therefore imports the
chosen library lazily and refuses to mix the two.
"""
from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from .theme import STYLES, normalize_style

_PACKAGES = {
    "web": ("tkwebui", "TKUI_TKWEBUI_PATH",
            ("tkwebui-main/tkwebui", "tkwebui-main", "tkwebui", "vendor/tkwebui")),
    "win11": ("tkwin11", "TKUI_TKWIN11_PATH",
              ("tkwin11-main/tkwin11", "tkwin11-main", "tkwin11", "vendor/tkwin11")),
}

_LOADED = {}
_LOADED_MODULES = set()


class BackendError(RuntimeError):
    """The requested theme library could not be found or loaded."""


@dataclass(frozen=True)
class Backend:
    style: str
    api: object
    package: str
    module_path: Path
    version: str

    @property
    def palette(self):
        return dict(self.api.PALETTE)

    def has(self, name) -> bool:
        return hasattr(self.api, name)

    def prepare(self):
        """Things that must happen before the first Tk() is created."""
        fn = getattr(self.api, "enable_dpi_awareness", None)
        if callable(fn):
            try:
                fn()
            except Exception:
                pass

    def apply(self, root, theme=None):
        """Apply the theme to an existing root and install tkui helper styles."""
        theme = dict(theme or {})
        if self.has("apply_theme"):
            allowed = _theme_kwargs(self.api.apply_theme)
            options = {key: value for key, value in theme.items()
                       if key in allowed and value is not None}
            self.api.apply_theme(root, **options)
        if self.style == "win11" and self.has("configure_fluent"):
            try:
                self.api.configure_fluent(root)
            except Exception:
                pass
        root._tkui_style = self.style
        root._tkui_backend = self
        _enhance_styles(root, self)

    def icon(self, master, name, size=16, color=None, background=None):
        if not name:
            return None
        root = master._root()
        try:
            return self.api.icon(root, name, size, color, background)
        except Exception:
            return None


def _theme_kwargs(function):
    import inspect

    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return {"font_family", "font_size", "accent", "accent_hover", "root"}
    names = set()
    for parameter in signature.parameters.values():
        names.add(parameter.name)
    return names


def _candidate_package_dirs(package, env_name, local_names):
    here = Path(__file__).resolve().parent.parent
    candidates = []

    override = os.environ.get(env_name)
    if override:
        path = Path(override).expanduser()
        candidates.extend([path, path / package])

    for base in (here, Path.cwd(), Path.cwd().parent):
        for name in local_names:
            candidates.append(base / name)
        candidates.append(base / package)

    # Optional installed copy, checked last so a local checkout wins.
    candidates.append(None)

    seen = set()
    for candidate in candidates:
        if candidate is None:
            yield None
            continue
        try:
            key = str(candidate.resolve())
        except OSError:
            key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if (candidate / "__init__.py").is_file():
            yield candidate


def _import_package(package, env_name, local_names):
    errors = []
    for candidate in _candidate_package_dirs(package, env_name, local_names):
        if candidate is None:
            try:
                module = importlib.import_module(package)
            except Exception as exc:  # noqa: BLE001 - reported below
                errors.append(f"installed {package}: {exc}")
                continue
        else:
            parent = str(candidate.parent)
            if parent not in sys.path:
                sys.path.insert(0, parent)
            try:
                module = importlib.import_module(package)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{candidate}: {exc}")
                continue
        return module, Path(getattr(module, "__file__", "")).resolve()
    detail = "\n  ".join(errors) if errors else "未找到包目录"
    raise BackendError(
        f"找不到 {package}。请把 {local_names[0]} 放在项目目录旁，"
        f"或设置环境变量 {env_name} 指向仓库根目录。\n  {detail}"
    )


def load(style) -> Backend:
    """Import and cache the backend for ``style``."""
    style = normalize_style(style, allow_auto=False)
    if style not in STYLES:
        raise BackendError(f"未知风格：{style!r}")
    if style in _LOADED:
        return _LOADED[style]
    other = [item for item in _LOADED_MODULES if item != _PACKAGES[style][0]]
    if other:
        raise BackendError(
            f"同一个 Tk 解释器里不能混用 {other[0]} 与 {_PACKAGES[style][0]}。"
            "切换风格请调用 tkui.relaunch()/App.restart_in_style() 重启程序。"
        )
    package, env_name, local_names = _PACKAGES[style]
    module, module_path = _import_package(package, env_name, local_names)
    _LOADED_MODULES.add(package)
    backend = Backend(
        style=style,
        api=module,
        package=package,
        module_path=module_path,
        version=str(getattr(module, "__version__", "?")),
    )
    _LOADED[style] = backend
    return backend


def loaded_styles():
    return tuple(_LOADED)


def _enhance_styles(root, backend):
    """Add style-neutral typography used by the renderer."""
    from tkinter import font as tkfont, ttk

    api = backend.api
    palette = api.PALETTE
    style = ttk.Style(root)
    default = tkfont.nametofont("TkDefaultFont", root=root)
    family = default.actual("family")
    size = default.actual("size")
    if size < 0:  # negative means pixels in Tk
        size = 10
    fg = palette.get("fg", "#16181D")
    muted = palette.get("muted", "#697180")
    bg = palette.get("bg", "#FFFFFF")
    accent = palette.get("accent", "#087DFF")
    accent_hover = palette.get("accent_hover", accent)
    workspace = style.lookup("Workspace.TFrame", "background") or bg
    page_bg = workspace if backend.style == "win11" else bg

    style.configure("TkUI.Title.TLabel", font=(family, size + 9, "bold"),
                    background=page_bg, foreground=fg)
    style.configure("TkUI.Subtitle.TLabel", font=(family, size + 1),
                    background=page_bg, foreground=muted)
    style.configure("TkUI.H2.TLabel", font=(family, size + 4, "bold"),
                    background=page_bg, foreground=fg)
    style.configure("TkUI.Stat.TLabel", font=(family, size + 13, "bold"),
                    background=bg, foreground=fg)
    style.configure("TkUI.StatSmall.TLabel", font=(family, size),
                    background=bg, foreground=muted)
    style.configure("TkUI.Mono.TLabel", font=("Consolas", size),
                    background=bg, foreground=fg)
    style.configure("TkUI.Key.TLabel", font=(family, max(8, size - 1)),
                    background=palette.get("hover", "#F1F1F4"), foreground=fg,
                    padding=(7, 3))
    try:
        quiet_layout = style.layout("Quiet.TButton")
        if quiet_layout:
            style.layout("TkUI.Link.TButton", quiet_layout)
        style.configure("TkUI.Link.TButton", font=(family, size), anchor="w",
                        padding=3, foreground=accent,
                        background=palette.get("bg", bg))
        style.map("TkUI.Link.TButton",
                  foreground=[("active", accent_hover), ("!disabled", accent)],
                  background=[("active", palette.get("bg", bg))])
    except Exception:
        pass


def backend_info(style) -> dict:
    backend = load(style)
    return {
        "style": backend.style,
        "package": backend.package,
        "version": backend.version,
        "path": str(backend.module_path),
        "palette": backend.palette,
        "features": {
            "fluent": backend.has("configure_fluent"),
            "custom_chrome": backend.has("FluentTitleBar"),
            "classic_patch": backend.has("install"),
        },
    }
