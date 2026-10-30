"""Render a declarative TkUI component tree with either backend."""
from __future__ import annotations

import copy
import traceback
from tkinter import ttk

from .actions import Event
from .catalog import COMPONENTS, ICONS, canonical_type
from .spec import SpecError, Issue

SEMANTIC = {
    "primary": "#087DFF",
    "success": "#159576",
    "warning": "#B77717",
    "danger": "#D54B58",
    "info": "#197FA8",
    "neutral": "#657080",
}

_DEFAULT_LAYOUT = {
    "label": {"fill": "none", "anchor": "w"},
    "heading": {"fill": "x"},
    "badge": {"fill": "none", "anchor": "w"},
    "button": {"fill": "none"},
    "switch": {"fill": "none", "anchor": "w"},
    "checkbox": {"fill": "none", "anchor": "w"},
    "radio_group": {"fill": "x"},
    "keychord": {"fill": "none"},
    "color": {"fill": "x"},
    "font": {"fill": "x"},
    "stat": {"fill": "x"},
    "alert": {"fill": "x"},
    "card": {"fill": "x"},
    "section": {"fill": "x"},
    "accordion": {"fill": "x"},
    "settings_row": {"fill": "x"},
    "settings_card": {"fill": "x"},
    "expander": {"fill": "x"},
    "column": {"fill": "x"},
    "row": {"fill": "x"},
    "grid": {"fill": "x"},
    "separator": {"fill": "x"},
    "scroll": {"fill": "both", "expand": True},
    "tabs": {"fill": "both", "expand": True},
    "list": {"fill": "both", "expand": True},
    "table": {"fill": "both", "expand": True},
    "tree": {"fill": "both", "expand": True},
    "spreadsheet": {"fill": "both", "expand": True},
    "chart": {"fill": "both", "expand": True},
    "image": {"fill": "both", "expand": True},
    "entry": {"fill": "x"},
    "text": {"fill": "x"},
    "combo": {"fill": "x"},
    "dropdown": {"fill": "x"},
    "spinbox": {"fill": "none", "anchor": "w"},
    "slider": {"fill": "x"},
    "progress": {"fill": "x"},
    "meter": {"fill": "none"},
    "date": {"fill": "x"},
    "segmented": {"fill": "none"},
    "page": {"fill": "both", "expand": True},
    "spacer": {"fill": "none"},
}


def _as_padding(value, default=0):
    if value is None:
        return default
    if isinstance(value, (list, tuple)):
        try:
            return tuple(int(v) for v in value)
        except (TypeError, ValueError):
            return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _pack_pad(value):
    if isinstance(value, (list, tuple)):
        return sum(int(v) for v in value)
    return int(value)


class Renderer:
    def __init__(self, app, parent):
        self.app = app
        self.backend = app.backend
        self.api = app.backend.api
        self.style = app.style
        self.root = parent._root()
        self.parent = parent
        self._seq = 0
        self._ready = False
        try:
            self.workspace_bg = ttk.Style(self.root).lookup("Workspace.TFrame", "background")
        except Exception:
            self.workspace_bg = None
        self._icache = {}

    # ------------------------------------------------------------- primitives
    def _id_for(self, node):
        self._seq += 1
        return str(node.get("id") or f"{canonical_type(node.get('type', 'node'))}_{self._seq}")

    def register(self, widget, node, *, getter=None, setter=None, native=None, var=None):
        node_id = self._id_for(node)
        if node_id in self.app.widgets:
            raise SpecError([Issue(node_id, f"组件 id {node_id!r} 重复")])
        self.app.widgets[node_id] = widget
        self.app._nodes[node_id] = node
        self.app._getters[node_id] = getter
        self.app._setters[node_id] = setter
        self.app._native[node_id] = native or widget
        if var is not None:
            self.app._vars_by_id[node_id] = var
        widget._tkui_id = node_id
        tooltip = node.get("tooltip")
        if tooltip:
            try:
                self.api.Tooltip(widget, str(tooltip))
            except Exception:
                pass
        if node.get("enabled") is False:
            try:
                widget.state(["disabled"])
            except Exception:
                try:
                    widget.configure(state="disabled")
                except Exception:
                    pass
        return node_id

    def icon(self, name, size=16, color=None, background=None):
        if not name:
            return None
        key = (name, size, color, background)
        if key not in self._icache:
            self._icache[key] = self.backend.icon(self.root, name, size, color, background)
        return self._icache[key]

    def style_bg(self, surface):
        if surface == "workspace" and self.style == "win11" and self.workspace_bg:
            return self.workspace_bg
        return self.api.PALETTE.get("bg")

    def surface_style(self, surface):
        if surface == "workspace" and self.style == "win11":
            return "Workspace.TFrame"
        if surface == "sidebar":
            return "Sidebar.TFrame"
        return "TFrame"

    # ---------------------------------------------------------------- actions
    def _action_for(self, node, event):
        on = node.get("on") or {}
        if isinstance(on, dict) and event in on:
            return on[event]
        if event in ("change", "select", "activate") and "command" in node:
            return node.get("command")
        if event == "click" and "command" in node:
            return node.get("command")
        return None

    def emit(self, node, widget, event, value=None):
        action = self._action_for(node, event)
        if action is None:
            return None
        node_id = getattr(widget, "_tkui_id", None)
        return self.app._run_action(action, Event(event, widget, self.app, value, node_id))

    def _wrap_event(self, node, widget, event, value_getter=None):
        def callback(*_):
            value = value_getter() if value_getter else None
            try:
                return self.emit(node, widget, event, value)
            except Exception:
                self.app._report_exception()
        return callback

    # -------------------------------------------------------------- variables
    def _variable(self, node, kind="str", default=None, *, watch=True):
        import tkinter as tk

        name = node.get("variable") or node.get("id")
        if not name:
            name = f"{canonical_type(node.get('type', 'value'))}_{id(node)}"
        if name in self.app.vars:
            var = self.app.vars[name]
        else:
            cls = {
                "str": tk.StringVar,
                "bool": tk.BooleanVar,
                "float": tk.DoubleVar,
                "int": tk.IntVar,
            }.get(kind, tk.StringVar)
            if default is None:
                default = False if kind == "bool" else (0 if kind in ("int", "float") else "")
            try:
                var = cls(master=self.root, value=default)
            except Exception:
                var = cls(master=self.root)
                var.set(default)
            self.app.vars[str(name)] = var
        if watch:
            self.app._watch(str(name), node, None)
        return str(name), var

    def _watch_widget(self, name, node, widget):
        self.app._watch(name, node, widget)

    # ----------------------------------------------------------------- layout
    def _layout_for(self, node, mode):
        name = canonical_type(node.get("type", "label"))
        layout = dict(_DEFAULT_LAYOUT.get(name, {}))
        layout.update(COMPONENTS.get(name, {}).get("default_layout") or {})
        layout.update(node.get("layout") or {})
        if name == "spacer" and node.get("expand"):
            layout["expand"] = True
            layout["fill"] = "both"
        if "fill" not in layout:
            layout["fill"] = "y" if mode == "row" else None
        return layout

    def place(self, parent, widget, node, mode, index, gap, *, grid_columns=2):
        layout = self._layout_for(node, mode)
        expand = bool(layout.get("expand", False))
        fill = layout.get("fill")
        if mode == "grid":
            columns = max(1, int(grid_columns or 1))
            row = int(layout.get("row", index // columns))
            column = int(layout.get("column", index % columns))
            stretch = expand or fill in ("both", "x", "y")
            sticky = layout.get("sticky") or ("nsew" if stretch else "")
            padx = _as_padding(layout.get("padx"), max(0, gap // 2))
            pady = _as_padding(layout.get("pady"), max(0, gap // 2))
            widget.grid(row=row, column=column,
                        rowspan=int(layout.get("rowspan", 1)),
                        columnspan=int(layout.get("columnspan", 1)),
                        sticky=sticky, padx=padx, pady=pady,
                        ipadx=int(layout.get("ipadx", 0) or 0),
                        ipady=int(layout.get("ipady", 0) or 0))
            try:
                parent.columnconfigure(
                    column, weight=int(layout.get("weightx", 1 if stretch else 0)))
                parent.rowconfigure(
                    row, weight=int(layout.get("weighty", 1 if expand else 0)))
            except Exception:
                pass
            return
        side = layout.get("side") or ("left" if mode == "row" else "top")
        padx = layout.get("padx")
        pady = layout.get("pady")
        if padx is None:
            padx = max(0, gap // 2) if mode == "row" else 0
        if pady is None:
            pady = max(0, gap // 2) if mode == "column" else 0
        widget.pack(side=side, fill=fill or "", expand=expand,
                    padx=_pack_pad(padx), pady=_pack_pad(pady),
                    ipadx=int(layout.get("ipadx", 0) or 0),
                    ipady=int(layout.get("ipady", 0) or 0),
                    anchor=layout.get("anchor") or "center")
        if "width" in layout or "height" in layout:
            try:
                widget.configure(width=int(layout.get("width", 0) or 0),
                                 height=int(layout.get("height", 0) or 0))
            except Exception:
                pass

    def build_children(self, parent, node, *, mode="column", gap=8, surface="panel"):
        children = node.get("children") or []
        grid_columns = int(node.get("columns", 2) or 2)
        for index, child in enumerate(children):
            widget = self.build(parent, child, surface=surface)
            self.place(parent, widget, child, mode, index, gap, grid_columns=grid_columns)

    def build_into(self, parent, node, *, mode="column", gap=10, surface="panel"):
        if isinstance(node, str):
            node = {"type": "label", "text": node}
        widget = self.build(parent, node, surface=surface)
        self.place(parent, widget, node, mode, 0, gap)
        return widget

    # ---------------------------------------------------------------- dispatch
    def build(self, parent, node, *, surface="panel"):
        if isinstance(node, str):
            node = {"type": "label", "text": node}
        if not isinstance(node, dict):
            raise SpecError([Issue("$", "组件节点必须是对象或字符串")])
        name = canonical_type(node.get("type", ""))
        renderer = _RENDERERS.get(name)
        if renderer is None:
            raise SpecError([Issue("$.type", f"未知组件 {node.get('type')!r}")])
        widget = renderer(self, parent, node, surface)
        if widget is None:
            raise SpecError([Issue("$.type", f"{name} 没有产生控件")])
        return widget

    # ------------------------------------------------------------------ pages
    def render_page(self, host, node):
        if isinstance(node, str):
            node = {"type": "page", "title": node, "children": []}
        node = copy.deepcopy(node)
        node.setdefault("type", "page")
        title = node.get("title", "")
        subtitle = node.get("subtitle", "")
        scroll = node.get("scroll", True)

        if scroll and self.style == "win11" and self.backend.has("FluentPage"):
            frame = self.api.FluentPage(host)
            body = frame.body
            if node.get("padding") is not None:
                body.configure(padding=_as_padding(node.get("padding")))
            child_surface = "workspace"
        elif scroll:
            frame = self.api.ScrollArea(host)
            body = frame.body
            body.configure(padding=_as_padding(node.get("padding"), 24))
            try:
                frame.canvas.configure(background=self.api.PALETTE.get("bg"))
            except Exception:
                pass
            child_surface = "panel"
        else:
            frame = ttk.Frame(host, padding=_as_padding(node.get("padding"), 24))
            body = frame
            child_surface = "panel"

        gap = int(node.get("gap", 14) or 14)
        header_style = self.surface_style(child_surface)
        if title or subtitle:
            header = ttk.Frame(body, style=header_style)
            header.pack(fill="x", pady=(0, gap))
            if title:
                ttk.Label(header, text=str(title), style="TkUI.Title.TLabel").pack(anchor="w")
            if subtitle:
                ttk.Label(header, text=str(subtitle), style="TkUI.Subtitle.TLabel",
                          wraplength=900, justify="left").pack(anchor="w", pady=(5, 0))
        self.build_children(body, node, mode="column", gap=gap, surface=child_surface)
        self.register(frame, node)
        return frame


def _render_column(ctx, parent, node, surface):
    direction = "row" if canonical_type(node.get("type")) == "row" else "column"
    gap = int(node.get("gap", 8) or 8)
    padding = _as_padding(node.get("padding"), 0)
    own_surface = node.get("surface") or surface
    frame = ttk.Frame(parent, padding=padding, style=ctx.surface_style(own_surface))
    child_surface = own_surface
    align = node.get("align", "center")
    if direction == "row" and align in ("start", "center", "end"):
        for child in node.get("children") or []:
            if isinstance(child, dict) and "layout" not in child:
                child["layout"] = {"side": {"start": "left", "center": "left", "end": "right"}[align]}
    ctx.build_children(frame, node, mode=direction, gap=gap, surface=child_surface)
    ctx.register(frame, node)
    return frame


def _render_grid(ctx, parent, node, surface):
    gap = int(node.get("gap", 8) or 8)
    own_surface = node.get("surface") or surface
    frame = ttk.Frame(parent, padding=_as_padding(node.get("padding"), 0),
                      style=ctx.surface_style(own_surface))
    ctx.build_children(frame, node, mode="grid", gap=gap, surface=own_surface)
    ctx.register(frame, node)
    return frame


def _render_spacer(ctx, parent, node, surface):
    size = int(node.get("size", 8) or 8)
    frame = ttk.Frame(parent, width=size, height=size)
    ctx.register(frame, node)
    return frame


def _render_separator(ctx, parent, node, surface):
    widget = ttk.Separator(parent, orient=node.get("orient", "horizontal"))
    ctx.register(widget, node)
    return widget


def _render_label(ctx, parent, node, surface):
    style = {
        "body": "TLabel",
        "muted": "Muted.TLabel",
        "strong": "Strong.TLabel",
        "title": "TkUI.Title.TLabel",
        "subtitle": "TkUI.Subtitle.TLabel",
        "caption": "Muted.TLabel",
    }.get(node.get("style", "body"), "TLabel")
    text = str(node.get("text", ""))
    options = {
        "text": text,
        "style": style,
        "justify": node.get("justify", "left"),
        "anchor": node.get("anchor", "w"),
    }
    wrap = int(node.get("wrap", 0) or 0)
    if wrap:
        options["wraplength"] = wrap
    icon = ctx.icon(node.get("icon"), 16) if node.get("icon") else None
    if icon is not None:
        options["image"] = icon
        options["compound"] = "left"
    widget = ttk.Label(parent, **options)
    if surface == "workspace" and ctx.style == "win11" and ctx.workspace_bg:
        try:
            widget.configure(background=ctx.workspace_bg)
        except Exception:
            pass
    ctx.register(widget, node)
    return widget


def _render_heading(ctx, parent, node, surface):
    frame = ttk.Frame(parent, style=ctx.surface_style(surface))
    level = int(node.get("level", 2) or 2)
    style = "TkUI.Title.TLabel" if level == 1 else "TkUI.H2.TLabel"
    label = ttk.Label(frame, text=str(node.get("title", "")), style=style,
                      anchor=node.get("align", "w"))
    label.pack(anchor=node.get("align", "w"))
    subtitle = node.get("subtitle")
    if subtitle:
        sub = ttk.Label(frame, text=str(subtitle), style="TkUI.Subtitle.TLabel",
                        anchor=node.get("align", "w"), justify="left")
        sub.pack(anchor=node.get("align", "w"), pady=(4, 0))
        if surface == "workspace" and ctx.workspace_bg:
            try:
                sub.configure(background=ctx.workspace_bg)
            except Exception:
                pass
    if surface == "workspace" and ctx.workspace_bg:
        try:
            label.configure(background=ctx.workspace_bg)
        except Exception:
            pass
    ctx.register(frame, node)
    return frame


def _render_card(ctx, parent, node, surface):
    kwargs = {"padding": int(node.get("padding", 16) or 16),
              "selected": bool(node.get("selected", False))}
    card = ctx.api.Card(parent, **kwargs)
    ctx.build_children(card, node, mode="column", gap=8, surface="panel")
    command = node.get("command")
    if command is not None:
        callback = ctx._wrap_event(node, card, "click")
        _bind_card_click(card, callback)
        try:
            card.configure(cursor="hand2")
        except Exception:
            pass
    ctx.register(card, node)
    return card


def _bind_card_click(widget, callback):
    def is_interactive(child):
        try:
            cls = child.winfo_class()
        except Exception:
            cls = ""
        return cls in ("TButton", "TCheckbutton", "TRadiobutton", "TEntry",
                       "TCombobox", "TScale", "TScrollbar", "Treeview", "Text",
                       "Listbox", "Spinbox")

    try:
        widget.bind("<Button-1>", callback, add="+")
    except Exception:
        pass
    for child in widget.winfo_children():
        if is_interactive(child):
            continue
        try:
            child.bind("<Button-1>", callback, add="+")
        except Exception:
            pass
        if child.winfo_children():
            _bind_card_click(child, callback)


def _render_section(ctx, parent, node, surface):
    title = str(node.get("title", "") or "")
    if title:
        card = ctx.api.SectionCard(parent, text=title,
                                   padding=int(node.get("padding", 14) or 14),
                                   selected=bool(node.get("selected", False)))
    else:
        card = ctx.api.Card(parent, padding=int(node.get("padding", 14) or 14),
                            selected=bool(node.get("selected", False)))
    ctx.build_children(card, node, mode="column", gap=10, surface="panel")
    ctx.register(card, node)
    return card


def _render_accordion(ctx, parent, node, surface):
    group = ctx.api.Accordion(parent, str(node.get("title", "")),
                              opened=bool(node.get("opened", False)))
    ctx.build_children(group.body, node, mode="column", gap=8, surface="panel")
    ctx.register(group, node)
    return group


def _render_scroll(ctx, parent, node, surface):
    area = ctx.api.ScrollArea(parent)
    height = int(node.get("height", 0) or 0)
    if height:
        try:
            area.canvas.configure(height=height)
        except Exception:
            pass
    area.body.configure(padding=_as_padding(node.get("padding"), 0))
    ctx.build_children(area.body, node, mode="column", gap=int(node.get("gap", 10) or 10),
                       surface="panel")
    ctx.register(area, node)
    return area


def _render_tabs(ctx, parent, node, surface):
    notebook = ttk.Notebook(parent)
    for child in node.get("children") or []:
        if isinstance(child, str):
            child = {"type": "tab", "title": child, "children": []}
        title = str(child.get("title", ""))
        tab = ttk.Frame(notebook, padding=_as_padding(
            child.get("padding", node.get("padding", 12)), 12))
        notebook.add(tab, text=title)
        ctx.build_children(tab, child, mode="column", gap=8, surface="panel")
        ctx.register(tab, child)
    ctx.register(notebook, node)
    return notebook


def _render_settings_row(ctx, parent, node, surface):
    row = ctx.api.SettingRow(parent, str(node.get("title", "")),
                             str(node.get("description", "")),
                             help_text=node.get("help"))
    ctx.build_children(row.action, node, mode="row", gap=6, surface="panel")
    ctx.register(row, node)
    return row


def _render_settings_card(ctx, parent, node, surface):
    title = str(node.get("title", ""))
    description = str(node.get("description", ""))
    if ctx.style == "win11" and ctx.backend.has("SettingsCard"):
        card = ctx.api.SettingsCard(parent, title, description,
                                    symbol=node.get("icon") or "settings")
        actions = card.actions
    else:
        card = ctx.api.Card(parent, padding=0)
        row = ctx.api.SettingRow(card, title, description, help_text=node.get("help"))
        row.pack(fill="x")
        actions = row.action
    ctx.build_children(actions, node, mode="row", gap=6, surface="panel")
    if node.get("command") is not None:
        callback = ctx._wrap_event(node, card, "click")
        _bind_card_click(card, callback)
    ctx.register(card, node)
    return card


def _render_expander(ctx, parent, node, surface):
    title = str(node.get("title", ""))
    if ctx.style == "win11" and ctx.backend.has("ExpanderCard"):
        card = ctx.api.ExpanderCard(parent, title,
                                    str(node.get("description", "")),
                                    symbol=node.get("icon") or "settings",
                                    opened=bool(node.get("opened", False)))
        body = card.body
    else:
        card = ctx.api.Accordion(parent, title, opened=bool(node.get("opened", False)))
        body = card.body
        description = node.get("description")
        if description:
            ttk.Label(body, text=str(description), style="Muted.TLabel").pack(anchor="w", pady=(0, 6))
    ctx.build_children(body, node, mode="column", gap=8, surface="panel")
    ctx.register(card, node)
    return card


def _render_page(ctx, parent, node, surface):
    return ctx.render_page(parent, node)


# ------------------------------------------------------------------- inputs
def _variant_style(ctx, variant):
    if variant in ("secondary", None, ""):
        return "TButton"
    if variant == "link":
        return "TkUI.Link.TButton"
    return {
        "primary": "Primary.TButton",
        "quiet": "Quiet.TButton",
        "danger": "Danger.TButton",
        "success": "Success.TButton",
        "toggle": "Toggle.TButton",
        "tool": "Toolbutton",
    }.get(variant, "TButton")


def _render_button(ctx, parent, node, surface):
    variant = node.get("variant", "secondary")
    text = str(node.get("text", "") or "")
    icon = ctx.icon(node.get("icon"), 16) if node.get("icon") else None
    options = {"text": text, "style": _variant_style(ctx, variant)}
    if icon is not None:
        options["image"] = icon
        options["compound"] = "left" if text else "none"
    if node.get("width") is not None:
        options["width"] = int(node["width"])
    # Pass the widget lazily through a closure-free proxy: emit resolves the id
    # from the widget when the button is actually pressed.
    def command():
        try:
            ctx.emit(node, widget, "click", None)
        except Exception:
            ctx.app._report_exception()

    factory = ctx.api.FluentButton if (
        ctx.style == "win11" and ctx.backend.has("FluentButton")) else ttk.Button
    try:
        widget = factory(parent, command=command, **options)
    except Exception:
        widget = ttk.Button(parent, command=command, **options)
    ctx.register(widget, node)
    return widget


def _render_entry(ctx, parent, node, surface):
    import tkinter as tk

    kind = node.get("kind", "text")
    value = node.get("value", "")
    name, var = ctx._variable(node, "str", str(value))
    needs_validation = bool(node.get("label") or node.get("required")
                            or node.get("min") is not None or node.get("max") is not None
                            or kind not in ("text", "password"))
    if needs_validation:
        kwargs = {}
        if node.get("width") is not None:
            kwargs["width"] = int(node["width"])
        if kind == "password":
            kwargs["show"] = "*"
        widget = ctx.api.ValidatedEntry(
            parent,
            variable=var,
            kind="text" if kind == "password" else kind,
            required=bool(node.get("required", False)),
            minimum=node.get("min"),
            maximum=node.get("max"),
            label=str(node.get("label", "")),
            **kwargs,
        )
        if node.get("placeholder"):
            try:
                ctx.api.set_placeholder(widget.entry, str(node["placeholder"]))
            except Exception:
                pass
        ctx._watch_widget(name, node, widget)
    else:
        kwargs = {"textvariable": var}
        if node.get("width") is not None:
            kwargs["width"] = int(node["width"])
        widget = ttk.Entry(parent, **kwargs)
        if node.get("placeholder"):
            try:
                ctx.api.set_placeholder(widget, str(node["placeholder"]))
            except Exception:
                pass
        ctx._watch_widget(name, node, widget)
    ctx.register(widget, node, var=name,
                 getter=lambda: var.get(), setter=lambda value: var.set(value))
    return widget


def _render_text(ctx, parent, node, surface):
    value = str(node.get("value", "") or "")
    widget = ctx.api.RoundedText(parent, height=int(node.get("height", 5) or 5),
                                 wrap=node.get("wrap", "word"))
    if value:
        widget.insert("1.0", value)
    if node.get("readonly"):
        widget.configure(state="disabled")
    widget.bind("<KeyRelease>", ctx._wrap_event(node, widget, "change", widget.get), add="+")
    ctx.register(widget, node,
                 getter=lambda: widget.get("1.0", "end-1c"),
                 setter=lambda value: (widget.delete("1.0", "end"),
                                       widget.insert("1.0", "" if value is None else str(value))))
    return widget


def _render_combo(ctx, parent, node, surface):
    values = [str(item) for item in node.get("values") or []]
    name, var = ctx._variable(node, "str", str(node.get("value", "") or ""))
    options = {
        "values": values,
        "textvariable": var,
        "state": "readonly" if node.get("readonly", True) else "normal",
    }
    if node.get("width") is not None:
        options["width"] = int(node["width"])
    widget = ctx.api.ThemedCombobox(parent, **options)
    if node.get("placeholder"):
        try:
            ctx.api.set_placeholder(widget, str(node["placeholder"]))
        except Exception:
            pass
    ctx._watch_widget(name, node, widget)
    ctx.register(widget, node, var=name,
                 getter=lambda: var.get(), setter=lambda value: var.set(value))
    return widget


def _render_dropdown(ctx, parent, node, surface):
    values = [str(item) for item in node.get("values") or []]
    name, var = ctx._variable(node, "str", str(node.get("value", "") or ""))
    widget = ctx.api.Dropdown(parent, values, variable=var)
    if node.get("placeholder"):
        try:
            ctx.api.set_placeholder(widget, str(node["placeholder"]))
        except Exception:
            pass
    ctx._watch_widget(name, node, widget)
    ctx.register(widget, node, var=name,
                 getter=lambda: var.get(), setter=lambda value: var.set(value))
    return widget


def _render_spinbox(ctx, parent, node, surface):
    name, var = ctx._variable(node, "float", float(node.get("value", 0) or 0))
    widget = ttk.Spinbox(parent,
                         from_=float(node.get("min", 0) or 0),
                         to=float(node.get("max", 100) or 100),
                         increment=float(node.get("step", 1) or 1),
                         textvariable=var,
                         width=int(node.get("width", 8) or 8))
    ctx._watch_widget(name, node, widget)
    ctx.register(widget, node, var=name,
                 getter=lambda: var.get(), setter=lambda value: var.set(value))
    return widget


def _render_checkbox(ctx, parent, node, surface):
    name, var = ctx._variable(node, "bool", bool(node.get("value", False)))
    widget = ttk.Checkbutton(parent, text=str(node.get("text", "") or ""), variable=var)
    ctx._watch_widget(name, node, widget)
    ctx.register(widget, node, var=name,
                 getter=lambda: bool(var.get()), setter=lambda value: var.set(bool(value)))
    return widget


def _normalize_options(node):
    options = []
    for item in node.get("options") or []:
        if isinstance(item, dict):
            value = item.get("value", item.get("key", item.get("label", "")))
            label = item.get("label", value)
        else:
            value = label = item
        options.append((str(value), str(label)))
    return options


def _render_radio_group(ctx, parent, node, surface):
    options = _normalize_options(node)
    default = node.get("value")
    if default is None and options:
        default = options[0][0]
    name, var = ctx._variable(node, "str", str(default) if default is not None else "")
    widget = ttk.Frame(parent)
    orientation = node.get("orientation", "horizontal")
    for value, label in options:
        button = ttk.Radiobutton(widget, text=label, value=value, variable=var)
        button.pack(side="left" if orientation == "horizontal" else "top",
                    padx=(0, 14) if orientation == "horizontal" else 0,
                    pady=(0, 4) if orientation == "vertical" else 0, anchor="w")
    ctx._watch_widget(name, node, widget)
    ctx.register(widget, node, var=name,
                 getter=lambda: var.get(), setter=lambda value: var.set(value))
    return widget


def _render_switch(ctx, parent, node, surface):
    name, var = ctx._variable(node, "bool", bool(node.get("value", False)))
    widget = ctx.api.SquareSwitch(parent, text=str(node.get("label", "") or ""), variable=var)
    ctx._watch_widget(name, node, widget)
    ctx.register(widget, node, var=name,
                 getter=lambda: bool(var.get()), setter=lambda value: var.set(bool(value)))
    return widget


def _render_segmented(ctx, parent, node, surface):
    options = _normalize_options(node)
    default = node.get("value")
    if default is None and options:
        default = options[0][0]
    name, var = ctx._variable(node, "str", str(default) if default is not None else "",
                              watch=False)
    widget = ctx.api.SegmentedControl(parent, options, var)
    ctx.register(widget, node, var=name,
                 getter=lambda: var.get(), setter=lambda value: var.set(value))

    def changed(*_):
        try:
            ctx.emit(node, widget, "change", var.get())
        except Exception:
            ctx.app._report_exception()

    widget.command = changed
    return widget


def _render_slider(ctx, parent, node, surface):
    name, var = ctx._variable(node, "float", float(node.get("value", 0) or 0), watch=False)
    widget = ctx.api.ValueSlider(
        parent, variable=var,
        from_=float(node.get("min", 0) or 0),
        to=float(node.get("max", 100) or 100),
        step=float(node.get("step", 1) or 1),
        unit=str(node.get("unit", "") or ""),
    )
    widget.command = lambda value: ctx.emit(node, widget, "change", value)
    ctx.register(widget, node, var=name,
                 getter=lambda: float(var.get()), setter=lambda value: widget.set(value))
    return widget


def _render_progress(ctx, parent, node, surface):
    widget = ctx.api.TextProgress(
        parent,
        value=float(node.get("value", 0) or 0),
        maximum=float(node.get("max", 100) or 100),
        text=str(node.get("text", "") or ""),
        mode=node.get("mode", "determinate"),
        kind=node.get("kind", "primary"),
        orient=node.get("orient", "horizontal"),
        length=int(node.get("length", 240) or 240),
        thickness=int(node.get("thickness", 28) or 28),
    )
    ctx.register(widget, node,
                 getter=lambda: widget.get(),
                 setter=lambda value: widget.set(float(value)))
    return widget


def _render_meter(ctx, parent, node, surface):
    widget = ctx.api.Meter(
        parent,
        value=float(node.get("value", 0) or 0),
        minimum=float(node.get("min", 0) or 0),
        maximum=float(node.get("max", 100) or 100),
        meter_type=node.get("shape", "full"),
        unit=str(node.get("unit", "%") or ""),
        subtext=str(node.get("subtext", "") or ""),
        interactive=bool(node.get("interactive", False)),
        size=int(node.get("size", 190) or 190),
    )
    widget.command = lambda value: ctx.emit(node, widget, "change", value)
    ctx.register(widget, node,
                 getter=lambda: widget.get(),
                 setter=lambda value: widget.set(float(value)))
    return widget


def _render_badge(ctx, parent, node, surface):
    widget = ctx.api.Badge(parent, text=str(node.get("text", "") or ""),
                           kind=node.get("kind", "info"))
    ctx.register(widget, node)
    return widget


def _render_date(ctx, parent, node, surface):
    widget = ctx.api.DateEntry(parent,
                               value=node.get("value"),
                               minimum=node.get("min"),
                               maximum=node.get("max"))
    widget.command = lambda *_ : ctx.emit(node, widget, "change", widget.variable.get())
    widget.bind("<FocusOut>", lambda event: ctx.emit(node, widget, "change",
                                                     widget.variable.get()), add="+")
    ctx.register(widget, node,
                 getter=lambda: widget.variable.get(),
                 setter=lambda value: widget.set_date(value))
    return widget


def _render_keychord(ctx, parent, node, surface):
    value = str(node.get("value", "") or "")
    if ctx.style == "win11" and ctx.backend.has("KeyChord"):
        widget = ctx.api.KeyChord(parent, value=value)
        ctx.register(widget, node, getter=lambda: widget.value,
                     setter=lambda new: (setattr(widget, "value", str(new)), widget.draw()))
        return widget
    name, var = ctx._variable(node, "str", value)
    widget = ttk.Entry(parent, textvariable=var, state="readonly")
    ctx.register(widget, node, var=name,
                 getter=lambda: var.get(), setter=lambda new: var.set(new))
    return widget


def _render_color(ctx, parent, node, surface):
    widget = ctx.api.ColorPicker(parent, color=node.get("value", "#087DFF"))
    widget.command = lambda color: ctx.emit(node, widget, "change", color)
    ctx.register(widget, node,
                 getter=lambda: widget.get_color(),
                 setter=lambda value: widget.set_color(value))
    return widget


def _render_font(ctx, parent, node, surface):
    widget = ctx.api.FontPicker(parent, font=node.get("value", "TkDefaultFont"))
    ctx.register(widget, node,
                 getter=lambda: widget.get_font(),
                 setter=lambda value: None)
    return widget


def _render_stat(ctx, parent, node, surface):
    card = ctx.api.Card(parent, padding=16)
    icon = ctx.icon(node.get("icon"), 22, color=SEMANTIC.get(node.get("kind"), SEMANTIC["info"])) \
        if node.get("icon") else None
    if icon is not None:
        ttk.Label(card, image=icon).grid(row=0, column=0, rowspan=2, sticky="n",
                                         padx=(0, 12))
    label = ttk.Label(card, text=str(node.get("label", "")), style="TkUI.StatSmall.TLabel")
    label.grid(row=0, column=1, sticky="w")
    value_text = str(node.get("value", ""))
    if node.get("suffix"):
        value_text += " " + str(node["suffix"])
    value = ttk.Label(card, text=value_text, style="TkUI.Stat.TLabel")
    value.grid(row=1, column=1, sticky="w", pady=(2, 0))
    if node.get("delta"):
        badge = ctx.api.Badge(card, text=str(node["delta"]), kind=node.get("kind", "info"))
        badge.grid(row=0, column=2, rowspan=2, sticky="e", padx=(14, 0))
    card.columnconfigure(1, weight=1)
    ctx.register(card, node)
    return card


def _render_alert(ctx, parent, node, surface):
    kind = node.get("kind", "info")
    color = SEMANTIC.get(kind, SEMANTIC["info"])
    card = ctx.api.Card(parent, padding=14, border_color=color)
    row = ttk.Frame(card)
    row.pack(fill="x")
    icon = ctx.icon("info", 18, color=color)
    if icon is not None:
        ttk.Label(row, image=icon).pack(side="left", anchor="n", padx=(0, 10))
    text = ttk.Frame(row)
    text.pack(side="left", fill="x", expand=True)
    if node.get("title"):
        ttk.Label(text, text=str(node["title"]), style="Strong.TLabel").pack(anchor="w")
    ttk.Label(text, text=str(node.get("message", "")), style="Muted.TLabel",
              wraplength=760, justify="left").pack(anchor="w", pady=(2, 0))
    ctx.register(card, node)
    return card


def _render_image(ctx, parent, node, surface):
    widget = ctx.api.ImageViewer(parent, height=int(node.get("height", 300) or 300))
    path = node.get("path")
    if path:
        try:
            widget.load(path)
        except Exception:
            pass
    ctx.register(widget, node)
    return widget


# --------------------------------------------------------------------- data
def _normalize_columns(columns):
    result = []
    for index, item in enumerate(columns or []):
        if isinstance(item, dict):
            key = str(item.get("key", item.get("text", index)))
            text = str(item.get("text", key))
            width = int(item.get("width", 140) or 140)
        else:
            key = text = str(item)
            width = 140
        result.append({"key": key, "text": text, "width": width})
    return result


def _row_dict(values, columns):
    if isinstance(values, dict):
        return {column["key"]: values.get(column["key"], values.get(column["text"], ""))
                for column in columns}
    return {column["key"]: value for column, value in zip(columns, values)}


def _render_table(ctx, parent, node, surface):
    columns = _normalize_columns(node.get("columns"))
    keys = [column["key"] for column in columns]
    rows = []
    for row in node.get("rows") or []:
        if isinstance(row, dict):
            rows.append([row.get(key, "") for key in keys])
        else:
            rows.append(list(row))
    widget = ctx.api.DataTable(parent, columns=columns, rows=rows,
                               page_size=int(node.get("page_size", 10) or 10),
                               height=int(node.get("height", 8) or 8))
    if node.get("command") or (node.get("on") or {}).get("activate"):
        def activate(event=None):
            selection = widget.tree.selection()
            if not selection:
                return
            values = list(widget.tree.item(selection[0], "values"))
            ctx.emit(node, widget, "activate", {key: value for key, value in zip(keys, values)})
        widget.tree.bind("<Double-1>", activate, add="+")
    if (node.get("on") or {}).get("select"):
        def selected(event=None):
            selection = widget.tree.selection()
            if not selection:
                return
            values = list(widget.tree.item(selection[0], "values"))
            ctx.emit(node, widget, "select", {key: value for key, value in zip(keys, values)})
        widget.tree.bind("<<TreeviewSelect>>", selected, add="+")
    ctx.register(widget, node, getter=lambda: widget.get_rows(),
                 setter=lambda values: widget.set_rows(values))
    return widget


def _render_list(ctx, parent, node, surface):
    widget = ctx.api.RoundedListbox(parent, selectmode=node.get("selectmode", "browse"),
                                    height=int(node.get("height", 8) or 8))
    for item in node.get("items") or []:
        widget.insert("end", str(item))
    value = node.get("value")
    if isinstance(value, int) and 0 <= value < len(node.get("items") or []):
        widget.selection_set(value)
        widget.see(value)
    elif isinstance(value, str):
        items = [str(item) for item in node.get("items") or []]
        if value in items:
            widget.selection_set(items.index(value))
    widget.bind("<<ListboxSelect>>",
                lambda event: ctx.emit(node, widget, "change", widget.curselection()), add="+")
    if (node.get("on") or {}).get("select"):
        widget.bind("<<ListboxSelect>>",
                    lambda event: ctx.emit(node, widget, "select", widget.curselection()), add="+")

    def getter():
        selection = widget.curselection()
        if widget.cget("selectmode") == "multiple" or widget.cget("selectmode") == "extended":
            return list(selection)
        return selection[0] if selection else -1

    def setter(value):
        widget.selection_clear(0, "end")
        if isinstance(value, (list, tuple)):
            for index in value:
                widget.selection_set(index)
        elif isinstance(value, int):
            widget.selection_set(value)
        elif isinstance(value, str):
            items = list(widget.get(0, "end"))
            if value in items:
                widget.selection_set(items.index(value))

    ctx.register(widget, node, getter=getter, setter=setter)
    return widget


def _render_tree(ctx, parent, node, surface):
    columns = _normalize_columns(node.get("columns"))
    keys = [column["key"] for column in columns]
    wrapper = ttk.Frame(parent)
    wrapper.columnconfigure(0, weight=1)
    wrapper.rowconfigure(0, weight=1)
    tree = ctx.api.SortableTreeview(wrapper, columns=keys, show="headings",
                                    height=int(node.get("height", 8) or 8))
    tree.grid(row=0, column=0, sticky="nsew")
    for column in columns:
        tree.heading(column["key"], text=column["text"])
        tree.column(column["key"], width=column["width"], minwidth=60,
                    stretch=column["key"] == keys[-1] if keys else True)
    vbar = ctx.api.AutoScrollbar(wrapper, command=tree.yview)
    vbar.grid(row=0, column=1, sticky="ns")
    hbar = ctx.api.AutoScrollbar(wrapper, orient="horizontal", command=tree.xview)
    hbar.grid(row=1, column=0, sticky="ew")
    tree.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
    try:
        ctx.api.configure_table(tree)
    except Exception:
        pass

    def row_values(row):
        if isinstance(row, dict):
            return tuple(row.get(key, "") for key in keys)
        return tuple(row)

    for row in node.get("rows") or []:
        tree.insert("", "end", values=row_values(row))

    def row_from_item(item):
        return {key: value for key, value in zip(keys, tree.item(item, "values"))}

    if node.get("command") or (node.get("on") or {}).get("activate"):
        tree.bind("<Double-1>", lambda event: ctx.emit(
            node, wrapper, "activate",
            row_from_item(tree.focus()) if tree.focus() else None), add="+")
    if (node.get("on") or {}).get("select"):
        tree.bind("<<TreeviewSelect>>", lambda event: ctx.emit(
            node, wrapper, "select",
            row_from_item(tree.focus()) if tree.focus() else None), add="+")

    def getter():
        return [row_from_item(item) for item in tree.get_children("")]

    def setter(rows):
        tree.delete(*tree.get_children(""))
        for row in rows or []:
            tree.insert("", "end", values=row_values(row))

    ctx.register(wrapper, node, native=tree, getter=getter, setter=setter)
    return wrapper


def _render_spreadsheet(ctx, parent, node, surface):
    widget = ctx.api.Spreadsheet(
        parent,
        data=node.get("data") or [],
        rows=int(node.get("rows", 30) or 30),
        columns=int(node.get("columns", 8) or 8),
        column_width=int(node.get("column_width", 122) or 122),
        row_height=int(node.get("row_height", 30) or 30),
    )
    widget.bind("<<SheetChanged>>",
                lambda event: ctx.emit(node, widget, "change", widget.get_data()), add="+")
    ctx.register(widget, node,
                 getter=lambda: widget.get_data(),
                 setter=lambda data: widget.set_data(data))
    return widget


def _render_chart(ctx, parent, node, surface):
    kind = node.get("kind", "line")
    height = int(node.get("height", 240) or 240)
    common = {"height": height}
    if kind in ("donut", "pie"):
        factory = ctx.api.PieChart if kind == "pie" else ctx.api.DonutChart
        widget = factory(parent, data=node.get("data") or [], **common)
    else:
        factory = {
            "line": ctx.api.LineChart,
            "column": ctx.api.ColumnChart,
            "scatter": ctx.api.ScatterChart,
        }.get(kind, ctx.api.LineChart)
        options = dict(common)
        if node.get("labels") is not None:
            options["labels"] = list(node["labels"])
        if node.get("series") is not None:
            series = copy.deepcopy(node["series"])
            if kind == "scatter":
                for item in series:
                    if "values" in item and "points" not in item:
                        item["points"] = list(enumerate(item.pop("values")))
            options["series"] = series
        elif node.get("values") is not None:
            if kind == "scatter":
                options["series"] = [{"name": "数据",
                                      "points": list(enumerate(node["values"]))}]
            else:
                options["values"] = list(node["values"])
        widget = factory(parent, **options)

    def clicked(point):
        action = ((node.get("on") or {}).get("select")
                  or (node.get("on") or {}).get("click")
                  or node.get("command"))
        if action is None:
            return
        try:
            ctx.app._run_action(action, Event("select", widget, ctx.app, point,
                                              getattr(widget, "_tkui_id", None)))
        except Exception:
            ctx.app._report_exception()

    widget.on_click = clicked
    if kind in ("donut", "pie"):
        def setter(data):
            widget.set_data(data)
    else:
        def setter(data):
            if isinstance(data, dict):
                widget.set_data(**data)
            else:
                widget.set_data(data)
    ctx.register(widget, node, getter=lambda: widget.get_data(), setter=setter)
    return widget


_RENDERERS = {
    "column": _render_column,
    "row": _render_column,
    "grid": _render_grid,
    "spacer": _render_spacer,
    "separator": _render_separator,
    "label": _render_label,
    "heading": _render_heading,
    "card": _render_card,
    "section": _render_section,
    "accordion": _render_accordion,
    "scroll": _render_scroll,
    "tabs": _render_tabs,
    "settings_row": _render_settings_row,
    "settings_card": _render_settings_card,
    "expander": _render_expander,
    "page": _render_page,
    "button": _render_button,
    "entry": _render_entry,
    "text": _render_text,
    "combo": _render_combo,
    "dropdown": _render_dropdown,
    "spinbox": _render_spinbox,
    "checkbox": _render_checkbox,
    "radio_group": _render_radio_group,
    "switch": _render_switch,
    "segmented": _render_segmented,
    "slider": _render_slider,
    "progress": _render_progress,
    "meter": _render_meter,
    "badge": _render_badge,
    "date": _render_date,
    "keychord": _render_keychord,
    "color": _render_color,
    "font": _render_font,
    "stat": _render_stat,
    "alert": _render_alert,
    "image": _render_image,
    "table": _render_table,
    "list": _render_list,
    "tree": _render_tree,
    "spreadsheet": _render_spreadsheet,
    "chart": _render_chart,
}


def renderer_names():
    return tuple(_RENDERERS)
