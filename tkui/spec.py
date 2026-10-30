"""Validation, normalization and JSON Schema generation for TkUI specs."""
from __future__ import annotations

import copy
import difflib
import json
from dataclasses import dataclass, field
from pathlib import Path

from .catalog import (ALIASES, COMMON_PROPS, COMPONENTS, ICONS, LAYOUT_FIELDS,
                      SPEC_VERSION, canonical_type)

TOP_KEYS = {"version", "title", "description", "style", "window", "theme",
            "nav", "pages", "body", "meta"}
WINDOW_KEYS = {"title", "size", "min_size", "resizable", "centered", "chrome",
               "padding", "icon"}
THEME_KEYS = {"accent", "accent_hover", "font_family", "font_size", "dpi"}
NAV_KEYS = {"mode", "items", "selected", "width", "title", "subtitle"}
NAV_ITEM_KEYS = {"key", "label", "icon"}
NODE_KEYS = {"type", "id", "layout", "children", "variable", "tooltip", "enabled", "on"}


@dataclass
class Issue:
    path: str
    message: str
    level: str = "error"

    def __str__(self):
        mark = "错误" if self.level == "error" else "提示"
        return f"{self.path}: {mark}: {self.message}"


class SpecError(ValueError):
    def __init__(self, issues):
        self.issues = list(issues)
        errors = [item for item in self.issues if item.level == "error"]
        shown = errors or self.issues
        text = "TkUI 规格有 {} 个问题：\n".format(len(shown))
        text += "\n".join(f"  - {item}" for item in shown[:40])
        if len(shown) > 40:
            text += f"\n  ... 还有 {len(shown) - 40} 个"
        super().__init__(text)


class Validator:
    def __init__(self, *, strict: bool = True):
        self.strict = strict
        self.issues = []
        self.ids = {}
        self.variables = {}
        self.actions = set()
        self.warnings = []

    # ------------------------------------------------------------------ util
    def error(self, path, message):
        self.issues.append(Issue(path, message, "error"))

    def warn(self, path, message):
        self.issues.append(Issue(path, message, "warning"))

    def unknown(self, path, name, allowed, what="字段"):
        if not self.strict:
            return
        suggestion = difflib.get_close_matches(str(name), list(allowed), n=1)
        hint = f"，是否想写 {suggestion[0]!r}？" if suggestion else ""
        self.warn(path, f"未知{what} {name!r}{hint}")

    # --------------------------------------------------------------- top level
    def validate(self, spec):
        if not isinstance(spec, dict):
            self.error("$", "规格必须是 JSON 对象")
            return self
        for key in spec:
            if key not in TOP_KEYS:
                self.unknown(f"$.{key}", key, TOP_KEYS)
        version = spec.get("version", SPEC_VERSION)
        if version != SPEC_VERSION:
            self.error("$.version", f"只支持版本 {SPEC_VERSION}，收到 {version!r}")
        for key in ("title", "description", "style"):
            if key in spec and not isinstance(spec[key], str):
                self.error(f"$.{key}", "必须是字符串")
        if "style" in spec:
            self._enum("$.style", spec["style"], ["web", "win11", "auto"])
        self._window(spec.get("window", {}))
        self._theme(spec.get("theme", {}))
        pages = spec.get("pages")
        nav = spec.get("nav")
        if pages is not None:
            self._pages(pages)
            if "body" in spec:
                self.warn("$.body", "已提供 pages，body 会被忽略")
        else:
            if "body" not in spec:
                self.error("$", "必须提供 body（单页）或 pages（多页）")
            else:
                self._node(spec["body"], "$.body", "body")
        if nav is not None:
            self._nav(nav, pages)
        elif pages:
            self._nav({"items": [{"key": key, "label": key} for key in pages]}, pages)
        return self

    def _window(self, window):
        if window is None:
            return
        if not isinstance(window, dict):
            self.error("$.window", "必须是对象")
            return
        for key in window:
            if key not in WINDOW_KEYS:
                self.unknown(f"$.window.{key}", key, WINDOW_KEYS)
        if "title" in window and not isinstance(window["title"], str):
            self.error("$.window.title", "必须是字符串")
        for key in ("size", "min_size"):
            value = window.get(key)
            if value is not None and (not isinstance(value, (list, tuple)) or len(value) != 2
                                      or not all(isinstance(v, int) for v in value)):
                self.error(f"$.window.{key}", "必须是 [宽, 高] 两个整数")
        if "resizable" in window:
            value = window["resizable"]
            if not isinstance(value, (bool, list, tuple)):
                self.error("$.window.resizable", "必须是布尔值或 [宽, 高]")
        if "chrome" in window:
            self._enum("$.window.chrome", window["chrome"], ["native", "custom"])
        if "centered" in window and not isinstance(window["centered"], bool):
            self.error("$.window.centered", "必须是布尔值")

    def _theme(self, theme):
        if theme is None:
            return
        if not isinstance(theme, dict):
            self.error("$.theme", "必须是对象")
            return
        for key in theme:
            if key not in THEME_KEYS:
                self.unknown(f"$.theme.{key}", key, THEME_KEYS)
        for key in ("accent", "accent_hover"):
            value = theme.get(key)
            if value is not None:
                if not isinstance(value, str):
                    self.error(f"$.theme.{key}", "必须是 #RRGGBB 字符串")
                elif not (len(value) == 7 and value.startswith("#")):
                    self.warn(f"$.theme.{key}", "颜色通常写成 #RRGGBB")
        for key in ("font_size",):
            if key in theme and not isinstance(theme[key], int):
                self.error(f"$.theme.{key}", "必须是整数")

    def _pages(self, pages):
        if not isinstance(pages, dict) or not pages:
            self.error("$.pages", "必须是非空对象：页面 key → 页面")
            return
        for key, page in pages.items():
            path = f"$.pages.{key}"
            if not isinstance(key, str) or not key:
                self.error(path, "页面 key 必须是非空字符串")
                continue
            if not isinstance(page, dict):
                self.error(path, "页面必须是对象（建议 {type: page, title: ..., children: [...]}）")
                continue
            page = copy.deepcopy(page)
            if "type" not in page:
                page["type"] = "page"
            if page.get("type") != "page":
                self.error(path + ".type", "pages 下的节点类型必须是 page")
            self._node(page, path, "page")

    def _nav(self, nav, pages):
        if nav is None:
            return
        if not isinstance(nav, dict):
            self.error("$.nav", "必须是对象")
            return
        for key in nav:
            if key not in NAV_KEYS:
                self.unknown(f"$.nav.{key}", key, NAV_KEYS)
        mode = nav.get("mode", "sidebar" if pages else "none")
        self._enum("$.nav.mode", mode, ["sidebar", "segmented", "none"])
        items = nav.get("items")
        if items is None:
            return
        if not isinstance(items, list):
            self.error("$.nav.items", "必须是列表")
            return
        keys = []
        for index, item in enumerate(items):
            path = f"$.nav.items[{index}]"
            if isinstance(item, str):
                keys.append(item)
                continue
            if not isinstance(item, dict):
                self.error(path, "必须是字符串或 {key,label,icon}")
                continue
            for key in item:
                if key not in NAV_ITEM_KEYS:
                    self.unknown(path + "." + key, key, NAV_ITEM_KEYS)
            key = item.get("key")
            if not isinstance(key, str) or not key:
                self.error(path + ".key", "必须是非空字符串")
                continue
            keys.append(key)
            if not isinstance(item.get("label", key), str):
                self.error(path + ".label", "必须是字符串")
            if item.get("icon") is not None:
                self._enum(path + ".icon", item["icon"], ICONS)
            if pages is not None and key not in pages:
                self.warn(path, f"页面 {key!r} 不存在")
        if len(set(keys)) != len(keys):
            self.error("$.nav.items", "导航 key 必须唯一")
        selected = nav.get("selected")
        if selected is not None and selected not in keys:
            self.error("$.nav.selected", f"{selected!r} 不在 nav.items 中")
        if "width" in nav and not isinstance(nav["width"], int):
            self.error("$.nav.width", "必须是整数")

    # ------------------------------------------------------------------- nodes
    def _node(self, node, path, parent_type="body"):
        if isinstance(node, str):
            return
        if not isinstance(node, dict):
            self.error(path, "节点必须是对象或字符串（字符串按 label 处理）")
            return
        raw_type = node.get("type")
        if not isinstance(raw_type, str) or not raw_type:
            self.error(path + ".type", "缺少组件类型")
            return
        name = canonical_type(raw_type)
        component = COMPONENTS.get(name)
        if component is None:
            suggestion = difflib.get_close_matches(name, COMPONENTS, n=1)
            hint = f"，是否想写 {suggestion[0]!r}？" if suggestion else ""
            self.error(path + ".type", f"未知组件 {raw_type!r}{hint}")
            return
        if parent_type != "tabs" and name == "tab":
            self.error(path + ".type", "tab 只能作为 tabs 的直接子项")
        if parent_type == "tabs" and name != "tab":
            self.error(path + ".type", "tabs 的子项必须是 tab")

        node_id = node.get("id")
        if node_id is not None:
            if not isinstance(node_id, str) or not node_id:
                self.error(path + ".id", "必须是非空字符串")
            elif node_id in self.ids:
                self.error(path + ".id", f"id {node_id!r} 已在 {self.ids[node_id]} 使用")
            else:
                self.ids[node_id] = path

        variable = node.get("variable")
        if variable is not None and not isinstance(variable, str):
            self.error(path + ".variable", "必须是字符串")

        on = node.get("on")
        if on is not None:
            if not isinstance(on, dict):
                self.error(path + ".on", "必须是 {事件: 动作} 对象")
            else:
                allowed_events = set(component["events"])
                for event, action in on.items():
                    if event not in allowed_events:
                        self.error(path + f".on.{event}",
                                   f"{name} 不支持事件 {event!r}，可用：{', '.join(sorted(allowed_events)) or '无'}")
                    self._action(action, path + f".on.{event}")
        if "command" in node:
            self._action(node["command"], path + ".command")

        layout = node.get("layout")
        if layout is not None:
            self._layout(layout, path + ".layout")

        known = NODE_KEYS | set(component["props"])
        if "command" in component["props"]:
            known.add("command")
        for key in node:
            if key not in known:
                self.unknown(path + "." + key, key, known)

        for prop_name, meta in component["props"].items():
            required = meta.get("required")
            if required and prop_name not in node:
                self.error(path, f"{name} 缺少必填属性 {prop_name!r}")
            if prop_name in node:
                self._value(node[prop_name], path + "." + prop_name, meta, prop_name)

        if "enabled" in node and not isinstance(node["enabled"], bool):
            self.error(path + ".enabled", "必须是布尔值")

        children = node.get("children")
        if children is not None:
            if not component["container"]:
                self.error(path + ".children", f"{name} 不是容器，不能有 children")
            elif not isinstance(children, list):
                self.error(path + ".children", "必须是列表")
            else:
                if name == "tabs" and not children:
                    self.error(path + ".children", "tabs 至少需要一个 tab")
                for index, child in enumerate(children):
                    self._node(child, f"{path}.children[{index}]", name)

        if name == "chart":
            if not any(key in node for key in ("values", "series", "data")):
                self.error(path, "chart 需要 values、series 或 data 之一")
            kind = node.get("kind", "line")
            if kind in ("donut", "pie") and "data" not in node:
                self.error(path, f"{kind} 图需要 data")
            if kind in ("line", "column", "scatter") and not any(
                    key in node for key in ("values", "series")):
                self.error(path, f"{kind} 图需要 values 或 series")
        if name == "table" and not node.get("columns"):
            self.error(path, "table 需要 columns")
        if name == "stat" and ("label" not in node or "value" not in node):
            self.error(path, "stat 需要 label 和 value")

    def _layout(self, layout, path):
        if not isinstance(layout, dict):
            self.error(path, "必须是对象")
            return
        for key, value in layout.items():
            meta = LAYOUT_FIELDS.get(key)
            if meta is None:
                self.unknown(path + "." + key, key, LAYOUT_FIELDS)
                continue
            kind = meta["kind"]
            if kind == "enum":
                self._enum(path + "." + key, value, meta["values"])
            elif kind == "bool":
                if not isinstance(value, bool):
                    self.error(path + "." + key, "必须是布尔值")
            elif kind == "int":
                if key in ("padx", "pady") and isinstance(value, (list, tuple)):
                    if len(value) != 2 or not all(isinstance(v, int) for v in value):
                        self.error(path + "." + key, "必须是整数或 [左, 右] / [上, 下]")
                elif not isinstance(value, int) or isinstance(value, bool):
                    self.error(path + "." + key, "必须是整数")
            elif kind == "str" and not isinstance(value, str):
                self.error(path + "." + key, "必须是字符串")
        if "fill" in layout and layout["fill"] == "none":
            layout["fill"] = None

    def _action(self, action, path):
        if isinstance(action, str):
            if not action.strip():
                self.error(path, "动作名不能为空")
            else:
                self.actions.add(action)
            return
        if isinstance(action, list):
            for index, item in enumerate(action):
                self._action(item, f"{path}[{index}]")
            return
        if isinstance(action, dict):
            builtins = {"action", "notify", "navigate", "set", "toggle", "dialog",
                        "quit", "chain", "style", "log", "title", "message", "kind",
                        "target", "value", "page", "text"}
            for key in action:
                if key not in builtins:
                    self.unknown(path + "." + key, key, builtins, "动作字段")
            if "chain" in action:
                chain = action["chain"]
                if not isinstance(chain, list):
                    self.error(path + ".chain", "必须是动作列表")
                else:
                    self._action(chain, path + ".chain")
            if action.get("action") not in (None, "notify", "navigate", "set", "toggle",
                                            "dialog", "quit", "style", "log", "chain"):
                self.error(path + ".action", f"未知内置动作 {action.get('action')!r}")
            return
        self.error(path, "动作必须是字符串、对象或列表")

    def _value(self, value, path, meta, name):
        kind = meta["kind"]
        if kind == "str":
            if not isinstance(value, (str, int, float)) or isinstance(value, bool):
                self.error(path, "必须是字符串")
        elif kind == "int":
            if not isinstance(value, int) or isinstance(value, bool):
                self.error(path, "必须是整数")
        elif kind == "float":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                self.error(path, "必须是数值")
        elif kind == "bool":
            if not isinstance(value, bool):
                self.error(path, "必须是布尔值")
        elif kind == "list":
            if not isinstance(value, (list, tuple)):
                self.error(path, "必须是列表")
        elif kind == "dict":
            if not isinstance(value, dict):
                self.error(path, "必须是对象")
        elif kind == "enum":
            if value not in meta.get("values", []):
                self.error(path, f"取值必须是 {', '.join(map(str, meta.get('values', [])))} 之一，收到 {value!r}")
        elif kind == "action":
            self._action(value, path)

    def _enum(self, path, value, values):
        if value not in values:
            self.error(path, f"取值必须是 {', '.join(map(str, values))} 之一，收到 {value!r}")


def validate(spec, *, strict: bool = True):
    """Validate and return ``(issues, actions)`` without raising."""
    validator = Validator(strict=strict).validate(spec)
    return validator.issues, validator.actions


def check(spec, *, strict: bool = True):
    """Validate and raise SpecError if there are errors."""
    issues, actions = validate(spec, strict=strict)
    errors = [item for item in issues if item.level == "error"]
    if errors:
        raise SpecError(issues)
    return issues, actions


def load(path):
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise SpecError([Issue("$", f"无法读取 {path}: {exc}")]) from exc
    try:
        spec = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SpecError([Issue(f"$ (line {exc.lineno}, column {exc.colno})",
                               f"JSON 解析失败：{exc.msg}")]) from exc
    check(spec)
    return spec


def page_node(key, value):
    """Normalize a page entry into a full page node."""
    if not isinstance(value, dict):
        raise SpecError([Issue(f"$.pages.{key}", "页面必须是对象")])
    node = copy.deepcopy(value)
    node.setdefault("type", "page")
    node.setdefault("title", str(key))
    return node


def nav_items(spec):
    pages = spec.get("pages") or {}
    nav = spec.get("nav") or {}
    items = nav.get("items")
    if items is None:
        items = [{"key": key, "label": page_node(key, page).get("title", key)}
                 for key, page in pages.items()]
    result = []
    for item in items:
        if isinstance(item, str):
            item = {"key": item, "label": item}
        key = item.get("key")
        result.append({"key": key, "label": item.get("label", key), "icon": item.get("icon")})
    return result


def _json_type(meta):
    kind = meta["kind"]
    if kind == "str":
        return {"type": ["string", "number"]}
    if kind == "int":
        return {"type": "integer"}
    if kind == "float":
        return {"type": "number"}
    if kind == "bool":
        return {"type": "boolean"}
    if kind == "list":
        return {"type": "array"}
    if kind == "dict":
        return {"type": "object"}
    if kind == "enum":
        return {"enum": list(meta.get("values", []))}
    if kind == "action":
        return {"oneOf": [{"type": "string"}, {"type": "object"}, {"type": "array"}]}
    return {}


def json_schema():
    """Build a JSON Schema (draft 2020-12) from the catalog."""
    layout_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {},
    }
    for name, meta in LAYOUT_FIELDS.items():
        if meta["kind"] == "enum":
            schema = {"enum": meta["values"]}
        elif meta["kind"] == "bool":
            schema = {"type": "boolean"}
        elif meta["kind"] == "int" and name in ("padx", "pady"):
            schema = {"oneOf": [{"type": "integer"},
                                {"type": "array", "items": {"type": "integer"},
                                 "minItems": 2, "maxItems": 2}]}
        elif meta["kind"] == "int":
            schema = {"type": "integer"}
        else:
            schema = {"type": "string"}
        schema["description"] = meta["desc"]
        layout_schema["properties"][name] = schema

    on_schema = {
        "type": "object",
        "additionalProperties": {"$ref": "#/$defs/action"},
    }
    action_schema = {
        "oneOf": [
            {"type": "string"},
            {"type": "object"},
            {"type": "array", "items": {"$ref": "#/$defs/action"}},
        ]
    }

    variants = []
    for name, item in COMPONENTS.items():
        props = {
            "type": {"const": name},
            "id": {"type": "string"},
            "variable": {"type": "string"},
            "tooltip": {"type": "string"},
            "enabled": {"type": "boolean"},
            "layout": {"$ref": "#/$defs/layout"},
            "on": on_schema,
        }
        required = ["type"]
        for prop_name, meta in item["props"].items():
            schema = _json_type(meta)
            if "default" in meta:
                schema["default"] = meta["default"]
            schema["description"] = meta["desc"]
            props[prop_name] = schema
            if meta.get("required"):
                required.append(prop_name)
        if item["container"]:
            props["children"] = {"type": "array", "items": {"$ref": "#/$defs/node"}}
        variants.append({
            "type": "object",
            "required": required,
            "properties": props,
            "additionalProperties": False,
            "description": item["summary"],
        })

    node_schema = {"oneOf": variants}
    page_schema = {
        "type": "object",
        "required": ["type"],
        "properties": {
            "type": {"const": "page"},
            "title": {"type": "string"},
            "subtitle": {"type": "string"},
            "scroll": {"type": "boolean"},
            "padding": {"type": "integer"},
            "gap": {"type": "integer"},
            "children": {"type": "array", "items": {"$ref": "#/$defs/node"}},
        },
        "additionalProperties": True,
    }
    pages_schema = {"type": "object", "additionalProperties": page_schema,
                    "minProperties": 1}
    nav_item_schema = {
        "oneOf": [
            {"type": "string"},
            {
                "type": "object",
                "required": ["key"],
                "properties": {
                    "key": {"type": "string"},
                    "label": {"type": "string"},
                    "icon": {"enum": list(ICONS)},
                },
                "additionalProperties": False,
            },
        ]
    }
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://tkui.local/schema/tkui-1.json",
        "title": "TkUI declarative UI spec",
        "description": "One style-neutral spec, rendered as Web or Windows 11 Fluent.",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "version": {"const": SPEC_VERSION},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "style": {"enum": list(["web", "win11", "auto"])},
            "window": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "size": {"type": "array", "items": {"type": "integer"},
                             "minItems": 2, "maxItems": 2},
                    "min_size": {"type": "array", "items": {"type": "integer"},
                                 "minItems": 2, "maxItems": 2},
                    "resizable": {"oneOf": [{"type": "boolean"},
                                            {"type": "array", "items": {"type": "boolean"},
                                             "minItems": 2, "maxItems": 2}]},
                    "centered": {"type": "boolean"},
                    "chrome": {"enum": ["native", "custom"]},
                    "padding": {"type": "integer"},
                    "icon": {"type": "string"},
                },
            },
            "theme": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "accent": {"type": "string"},
                    "accent_hover": {"type": "string"},
                    "font_family": {"type": "string"},
                    "font_size": {"type": "integer"},
                    "dpi": {"type": "boolean"},
                },
            },
            "nav": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "mode": {"enum": ["sidebar", "segmented", "none"]},
                    "items": {"type": "array", "items": nav_item_schema},
                    "selected": {"type": "string"},
                    "width": {"type": "integer"},
                    "title": {"type": "string"},
                    "subtitle": {"type": "string"},
                },
            },
            "pages": pages_schema,
            "body": {"$ref": "#/$defs/node"},
            "meta": {"type": "object"},
        },
        "oneOf": [
            {"required": ["body"]},
            {"required": ["pages"]},
        ],
        "$defs": {
            "node": node_schema,
            "page": page_schema,
            "layout": layout_schema,
            "action": action_schema,
        },
    }
    return schema
