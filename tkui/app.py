"""Application shell around the declarative renderer."""
from __future__ import annotations

import copy
import os
import sys
import traceback
import warnings
from tkinter import ttk

from . import theme as theme_mod
from .actions import ActionError, Event, check_action_names, run_action
from .backends import BackendError, load as load_backend
from .renderer import Renderer
from .spec import Issue, SpecError, check, nav_items, page_node


class SpecWarning(UserWarning):
    pass


def _root_theme(root):
    try:
        return str(ttk.Style(root).theme_use())
    except Exception:
        return None


class App:
    """Host a declarative UI spec.

    ``App("app.json")`` or ``App(spec_dict)`` creates a window.  Pass
    ``master=frame`` to embed the UI in an existing Tk container.
    """

    def __init__(self, spec, *, style=None, actions=None, master=None,
                 theme=None, strict=True, warn=True, on_close=None):
        if isinstance(spec, (str, bytes, os.PathLike)):
            from .spec import load as load_spec
            spec = load_spec(spec)
        if not isinstance(spec, dict):
            raise SpecError([Issue("$", "spec 必须是 JSON 对象或 JSON 文件路径")])
        self.spec = copy.deepcopy(spec)
        if "body" not in self.spec and "pages" not in self.spec and self.spec.get("type"):
            self.spec = {"version": 1, "body": self.spec}
        self._issues, self._required_actions = check(self.spec, strict=strict)
        if warn:
            messages = [str(item) for item in self._issues if item.level == "warning"]
            if messages:
                warnings.warn(SpecWarning("TkUI 规格提示：\n  " + "\n  ".join(messages)),
                              stacklevel=2)
        self.actions = dict(actions or {})
        check_action_names(self, self._required_actions)

        self.widgets = {}
        self.vars = {}
        self._nodes = {}
        self._getters = {}
        self._setters = {}
        self._native = {}
        self._vars_by_id = {}
        self._var_nodes = {}
        self._var_traces = {}
        self._muted = False
        self._ready = False
        self._closed = False
        self._pages = {}
        self._page_frames = {}
        self.current_page = None
        self.on_close = on_close
        self._embedded = master is not None
        self.master = master

        spec_style = self.spec.get("style")
        self.style = theme_mod.resolve_style(style if style is not None else spec_style)
        self.backend = load_backend(self.style)
        merged_theme = dict(self.spec.get("theme") or {})
        merged_theme.update(theme or {})
        self.theme = merged_theme

        import tkinter as tk

        if master is None:
            if merged_theme.get("dpi", True):
                self.backend.prepare()
            self.window = tk.Tk()
            self.root = self.window
            configured = getattr(self.root, "_tkui_style", None)
            if configured is not None and configured != self.style:
                raise BackendError(
                    f"当前 Tk 根窗口已套用 {configured} 主题，不能改为 {self.style}。"
                    " 请新开进程，或调用 App.restart_in_style()。"
                )
            existing = configured or _root_theme(self.root)
            if existing in ("switch-lite", "win11-fluent"):
                expected = "switch-lite" if self.style == "web" else "win11-fluent"
                if existing != expected:
                    raise BackendError(
                        f"当前 Tk 根窗口已套用 {existing} 主题，不能改为 {self.style}。"
                        " 请新开进程，或调用 App.restart_in_style()。"
                    )
            if not getattr(self.root, "_tkui_style", None):
                self.backend.apply(self.root, merged_theme)
            else:
                self.backend.apply(self.root, merged_theme)
            self.root._tkui_app = self
            self.surface = self.root
            self.renderer = Renderer(self, self.root)
            self._configure_window()
            self._build()
            if self.on_close is not None:
                self.root.protocol("WM_DELETE_WINDOW", self.close)
        else:
            self.window = master.winfo_toplevel()
            self.root = self.window
            existing = getattr(self.root, "_tkui_style", None)
            if existing is not None and existing != self.style:
                raise BackendError(
                    f"宿主窗口使用 {existing} 风格，不能嵌入 {self.style} 风格。"
                )
            if existing is None and _root_theme(self.root) in ("switch-lite", "win11-fluent"):
                existing = _root_theme(self.root)
            if existing is None:
                self.backend.apply(self.root, merged_theme)
            elif existing in ("switch-lite", "win11-fluent"):
                expected = "switch-lite" if self.style == "web" else "win11-fluent"
                if existing != expected:
                    raise BackendError(
                        f"宿主窗口使用 {existing}，不能嵌入 {self.style} 风格。"
                    )
            self.surface = master
            self.renderer = Renderer(self, master)
            self._build()
        self._ready = True

    # ------------------------------------------------------------- window setup
    def _configure_window(self):
        window = self.spec.get("window") or {}
        title = window.get("title") or self.spec.get("title") or "TkUI"
        self.root.title(str(title))
        size = window.get("size") or [980, 700]
        try:
            width, height = int(size[0]), int(size[1])
        except (TypeError, ValueError, IndexError):
            width, height = 980, 700
        if window.get("centered", True):
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = max(0, (screen_w - width) // 2)
            y = max(0, (screen_h - height) // 3)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        else:
            self.root.geometry(f"{width}x{height}")
        minimum = window.get("min_size")
        if minimum:
            try:
                self.root.minsize(int(minimum[0]), int(minimum[1]))
            except (TypeError, ValueError, IndexError):
                pass
        resizable = window.get("resizable", True)
        if isinstance(resizable, (list, tuple)):
            self.root.resizable(bool(resizable[0]), bool(resizable[1]))
        else:
            self.root.resizable(bool(resizable), bool(resizable))

    # ------------------------------------------------------------------- build
    def _build(self):
        if self.spec.get("pages"):
            self._pages = {key: page_node(key, value)
                           for key, value in self.spec["pages"].items()}
            nav = dict(self.spec.get("nav") or {})
            self._nav_spec = nav
            mode = nav.get("mode", "sidebar")
            self._sidebar = None
            self._nav_var = None
            self._nav_control = None

            self.shell = ttk.Frame(self.surface)
            self._maybe_build_custom_chrome()

            if mode == "sidebar":
                items = nav_items(self.spec)
                self._nav_items = items
                width = int(nav.get("width", 230) or 230)
                sidebar_items = [(item["key"], item["label"], item.get("icon") or "controls")
                                 for item in items]
                self._sidebar = self.backend.api.Sidebar(
                    self.shell, sidebar_items, self._on_nav, width=width)
                self._sidebar.pack(side="left", fill="y")
                self.page_host = ttk.Frame(self.shell)
                self.page_host.pack(side="left", fill="both", expand=True)
            elif mode == "segmented":
                header = ttk.Frame(self.shell, padding=(20, 14, 20, 0))
                header.pack(fill="x")
                items = nav_items(self.spec)
                self._nav_items = items
                self._nav_var = __import__("tkinter").StringVar(self.root)
                options = [(item["key"], item["label"]) for item in items]
                self._nav_control = self.backend.api.SegmentedControl(
                    header, options, self._nav_var, command=self._on_nav)
                self._nav_control.pack(anchor="w")
                self.page_host = ttk.Frame(self.shell)
                self.page_host.pack(fill="both", expand=True)
            else:
                self._nav_items = nav_items(self.spec)
                self.page_host = ttk.Frame(self.shell)
                self.page_host.pack(fill="both", expand=True)

            self.shell.pack(fill="both", expand=True)
            selected = nav.get("selected") or (self._nav_items[0]["key"] if self._nav_items else None)
            if selected:
                self.navigate(selected)
        else:
            self._nav_items = []
            self.shell = ttk.Frame(self.surface)
            self.shell.pack(fill="both", expand=True)
            body = self.spec["body"]
            widget = self.renderer.build(self.shell, body)
            widget.pack(fill="both", expand=True)

    def _maybe_build_custom_chrome(self):
        window = self.spec.get("window") or {}
        if window.get("chrome") != "custom":
            return
        if self.style != "win11" or not self.backend.has("FluentTitleBar"):
            warnings.warn(SpecWarning("自定义一体化标题栏只在 win11 风格下生效，已使用系统标题栏。"),
                          stacklevel=2)
            return
        # The sidebar is created by the caller into ``shell``; build a temporary
        # placeholder here and connect the real sidebar afterwards.
        try:
            nav = self._nav_spec if hasattr(self, "_nav_spec") else {}
            width = int(nav.get("width", 230) or 230) if nav.get("mode", "sidebar") == "sidebar" else 0
            title = (window.get("title") or self.spec.get("title") or "TkUI")
            self._titlebar = self.backend.api.FluentTitleBar(
                self.root, title=str(title), sidebar_width=width,
                on_close=self.close)
            self._titlebar.pack(side="top", fill="x")
        except Exception:
            self._report_exception()

    def _on_nav(self, key):
        self.navigate(key)

    def navigate(self, key):
        if key not in self._pages:
            raise KeyError(f"页面不存在：{key!r}")
        if self.current_page == key and key in self._page_frames:
            return
        if self.current_page and self.current_page in self._page_frames:
            try:
                self._page_frames[self.current_page].pack_forget()
            except Exception:
                pass
        if key not in self._page_frames:
            frame = self.renderer.render_page(self.page_host, self._pages[key])
            self._page_frames[key] = frame
        frame = self._page_frames[key]
        frame.pack(fill="both", expand=True)
        if self.current_page and self.current_page in self._page_frames:
            try:
                self._page_frames[self.current_page].pack_forget()
            except Exception:
                pass
        # Re-pack the new page after the old one was hidden.
        frame.pack(fill="both", expand=True)
        self.current_page = key
        if self._sidebar is not None:
            try:
                self._sidebar.select(key, notify=False)
            except Exception:
                pass
        if self._nav_var is not None and self._nav_var.get() != key:
            self._nav_var.set(key)
        try:
            self.root.event_generate("<<TkUIPageChanged>>", data=key)
        except Exception:
            pass
        return frame

    @property
    def page(self):
        return self.current_page

    # ---------------------------------------------------------------- variables
    def _watch(self, name, node, widget):
        entries = self._var_nodes.setdefault(name, [])
        for index, (existing, _) in enumerate(entries):
            if existing is node:
                entries[index] = (node, widget)
                break
        else:
            entries.append((node, widget))
        if name not in self._var_traces:
            var = self.vars.get(name)
            if var is not None:
                self._var_traces[name] = var.trace_add(
                    "write", lambda *_, key=name: self._var_changed(key))

    def _var_changed(self, name):
        if not self._ready or self._muted:
            return
        var = self.vars.get(name)
        if var is None:
            return
        try:
            value = var.get()
        except Exception:
            value = None
        for node, widget in list(self._var_nodes.get(name, [])):
            if widget is None:
                continue
            on = node.get("on") or {}
            action = on.get("change") if isinstance(on, dict) else None
            if action is None:
                action = node.get("command")
            if action is None:
                continue
            try:
                self._run_action(action, Event("change", widget, self, value,
                                               getattr(widget, "_tkui_id", None)))
            except Exception:
                self._report_exception()

    def var(self, name):
        if name not in self.vars:
            raise KeyError(f"变量不存在：{name!r}")
        return self.vars[name]

    # -------------------------------------------------------------------- values
    def widget(self, node_id):
        return self.widgets[node_id]

    def native(self, node_id):
        return self._native.get(node_id, self.widgets[node_id])

    def get(self, node_id, default=...):
        if node_id not in self.widgets:
            if default is not ...:
                return default
            raise KeyError(f"组件不存在：{node_id!r}")
        getter = self._getters.get(node_id)
        if getter is not None:
            return getter()
        var_name = self._vars_by_id.get(node_id)
        if var_name and var_name in self.vars:
            return self.vars[var_name].get()
        widget = self.widgets[node_id]
        for method in ("get_data", "get"):
            if hasattr(widget, method):
                return getattr(widget, method)()
        return None

    def set(self, node_id, value, *, silent=False):
        if node_id not in self.widgets:
            raise KeyError(f"组件不存在：{node_id!r}")
        previous = self._muted
        self._muted = silent or previous
        try:
            setter = self._setters.get(node_id)
            if setter is not None:
                setter(value)
                return
            var_name = self._vars_by_id.get(node_id)
            if var_name and var_name in self.vars:
                self.vars[var_name].set(value)
                return
            widget = self.widgets[node_id]
            if hasattr(widget, "set_data"):
                widget.set_data(value)
            elif hasattr(widget, "set"):
                widget.set(value)
            else:
                raise AttributeError(f"组件 {node_id!r} 不支持 set()")
        finally:
            self._muted = previous

    def focus(self, node_id):
        widget = self.native(node_id)
        try:
            widget.focus_set()
        except Exception:
            pass
        return widget

    # ------------------------------------------------------------------ actions
    def add_action(self, name, function):
        self.actions[name] = function
        return function

    def _run_action(self, action, event):
        return run_action(self, action, event)

    def _report_exception(self):
        exc_type, exc, tb = sys.exc_info()
        if exc is None:
            return
        traceback.print_exception(exc_type, exc, tb)
        try:
            self.root.report_callback_exception(exc_type, exc, tb)
        except Exception:
            pass

    # --------------------------------------------------------------- feedback
    def notify(self, message, *, title="", kind="info", duration=3000, position="bottom-right"):
        try:
            return self.backend.api.notify(self.root, str(message), title=title, kind=kind,
                                           duration=duration, position=position)
        except Exception:
            print(f"[{kind}] {message}")
            return None

    def dialog(self, message, *, title="提示", kind="info"):
        dialogs = self.backend.api.Dialogs
        if kind in ("danger", "error"):
            return dialogs.error(self.root, str(message), title=title)
        if kind in ("warning", "warn"):
            return dialogs.warning(self.root, str(message), title=title)
        return dialogs.info(self.root, str(message), title=title)

    def ask_string(self, prompt, *, title="输入", initial=""):
        return self.backend.api.Dialogs.ask_string(
            self.root, str(prompt), title=title, initial=str(initial))

    # ------------------------------------------------------------------ window
    def run(self):
        if self._embedded:
            raise RuntimeError("嵌入模式没有自己的 mainloop，请运行宿主窗口")
        self.root.mainloop()
        return self

    def close(self):
        if self._closed:
            return
        self._closed = True
        if self.on_close is not None:
            try:
                self.on_close(self)
            except Exception:
                self._report_exception()
        try:
            # TkWin11's controller <Destroy> handlers may run after Tk has
            # already removed their Tcl commands (notably on Python 3.15/Tk 9).
            # They are harmless teardown noise; keep the console clean.
            import tkinter as tk
            def quiet(exc_type, exc, tb):
                if isinstance(exc, tk.TclError) and "delete Tcl command" in str(exc):
                    return
                traceback.print_exception(exc_type, exc, tb)
            try:
                self.root.report_callback_exception = quiet
            except Exception:
                pass
            if self._embedded:
                self.shell.destroy()
            else:
                self.root.destroy()
        except Exception:
            pass

    destroy = close

    def restart_in_style(self, style):
        """Save the preference and relaunch this program with another look."""
        return theme_mod.relaunch(style, app=self)

    def info(self):
        return {
            "style": self.style,
            "style_label": theme_mod.STYLE_INFO[self.style]["label"],
            "backend": self.backend.package,
            "version": self.backend.version,
            "path": str(self.backend.module_path),
            "page": self.current_page,
            "components": len(self.widgets),
        }
