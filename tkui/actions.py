"""Action model used by commands and events in declarative specs."""
from __future__ import annotations

import inspect
from dataclasses import dataclass


@dataclass
class Event:
    """Payload passed to Python callbacks and built-in actions."""

    name: str
    source: object = None
    app: object = None
    value: object = None
    id: str = None

    @property
    def widget(self):
        return self.source

    def __repr__(self):
        return f"Event({self.name!r}, id={self.id!r}, value={self.value!r})"


class ActionError(RuntimeError):
    pass


_BUILTINS = {"notify", "navigate", "set", "toggle", "dialog", "quit", "chain",
             "style", "log"}


def check_action_names(app, names):
    """Raise a helpful error when a spec references unknown Python actions."""
    missing = sorted(name for name in names if name not in app.actions)
    if missing:
        available = ", ".join(sorted(app.actions)) or "（未提供）"
        raise ActionError(
            "规格引用了未注册的动作："
            + ", ".join(repr(name) for name in missing)
            + f"。可用的动作：{available}。"
            " 也可以用内置动作对象，例如 {\"action\": \"notify\", \"message\": \"已保存\"}。"
        )


def call_user(app, fn, event):
    """Call a user callback with an Event when it accepts an argument."""
    if not callable(fn):
        raise ActionError(f"动作 {fn!r} 不是可调用对象")
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        return fn(event)
    positional = [
        parameter for parameter in signature.parameters.values()
        if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    ]
    varargs = any(parameter.kind == parameter.VAR_POSITIONAL
                  for parameter in signature.parameters.values())
    if positional or varargs:
        return fn(event)
    return fn()


def run_action(app, action, event):
    """Execute a spec action (name, built-in object, or list)."""
    if action is None:
        return None
    if isinstance(action, str):
        fn = app.actions.get(action)
        if fn is None:
            raise ActionError(f"未注册的动作：{action!r}")
        return call_user(app, fn, event)
    if isinstance(action, (list, tuple)):
        result = None
        for item in action:
            result = run_action(app, item, event)
        return result
    if isinstance(action, dict):
        return _run_dict(app, action, event)
    raise ActionError(f"无法执行的动作：{action!r}")


def _run_dict(app, action, event):
    data = dict(action)
    name = data.get("action")

    def resolve(value):
        if value in ("$value", "$event"):
            return event.value
        return value

    # Shorthand forms: {"notify": "..."} / {"navigate": "settings"}.
    if name is None:
        for candidate in _BUILTINS:
            if candidate in data:
                name = candidate
                break

    if name == "chain":
        chain = data.get("chain", [])
        result = None
        for item in chain:
            result = run_action(app, item, event)
        return result

    if name == "notify":
        message = data.get("message") or data.get("notify") or data.get("text") or ""
        app.notify(str(message), title=data.get("title", ""), kind=data.get("kind", "info"))
        return None

    if name == "navigate":
        page = data.get("navigate") or data.get("page") or data.get("target")
        if not page:
            raise ActionError("navigate 动作需要 page")
        return app.navigate(str(page))

    if name == "set":
        target = data.get("target")
        if not target:
            raise ActionError("set 动作需要 target（组件 id）")
        value = data.get("value")
        if value == "$event":
            value = event.value
        app.set(target, value)
        return None

    if name == "toggle":
        target = data.get("target")
        if not target:
            raise ActionError("toggle 动作需要 target（组件 id）")
        app.set(target, not bool(app.get(target)))
        return None

    if name == "dialog":
        message = data.get("message", "")
        title = data.get("title", "提示")
        kind = data.get("kind", "info")
        return app.dialog(message, title=title, kind=kind)

    if name == "style":
        style = resolve(data.get("style") or data.get("target"))
        if not style:
            raise ActionError("style 动作需要 style（web / win11）")
        return app.restart_in_style(str(style))

    if name == "log":
        print(data.get("message", ""))
        return None

    if name == "quit":
        return app.close()

    raise ActionError(f"未知内置动作：{action!r}")
