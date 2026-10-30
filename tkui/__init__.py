"""TkUI — one AI-friendly component layer over TkWebUI and TkWin11.

The same declarative spec renders as a modern web application (``web``) or a
Windows 11 Fluent application (``win11``).  Users can pick the look before the
first window appears, and an app can restart itself into the other look.

Typical use::

    import tkui

    app = tkui.App("app.json", actions={"save": on_save})
    app.run()

    # or choose the style with a small dialog
    style = tkui.choose_style()
    tkui.run("app.json", style=style)
"""
from __future__ import annotations

__version__ = "0.1.0"

from .app import App, SpecWarning
from .actions import ActionError, Event
from .catalog import (ALIASES, CATEGORIES, COMMON_PROPS, COMPONENTS, ICONS,
                      LAYOUT_FIELDS, SPEC_VERSION, catalog, component,
                      component_names, to_markdown)
from .spec import (Issue, SpecError, check, json_schema, load, nav_items,
                   page_node, validate)
from .theme import (DEFAULT_STYLE, STYLE_INFO, STYLES, StyleError, choose_style,
                    describe, normalize_style, read_config, relaunch,
                    resolve_style, save_style, saved_style, write_config)

UI = App
create = App


def run(spec, *, style=None, actions=None, theme=None, master=None, **kwargs):
    """Create an application, run its mainloop, and return the App."""
    app = App(spec, style=style, actions=actions, theme=theme, master=master, **kwargs)
    app.run()
    return app


def mount(master, spec, *, style=None, actions=None, theme=None, **kwargs):
    """Embed a spec in an existing Tk container."""
    return App(spec, style=style, actions=actions, theme=theme, master=master, **kwargs)


def demo(*, style=None, page=None):
    """Run the bundled gallery."""
    from .demo import run_demo
    return run_demo(style=style, page=page)


def prompt() -> str:
    """Return the Markdown prompt that teaches an AI to write TkUI specs."""
    from .ai import prompt as build_prompt
    return build_prompt()


__all__ = [
    "__version__",
    "App", "UI", "create", "run", "mount", "demo", "prompt",
    "SpecError", "SpecWarning", "Issue", "ActionError", "Event",
    "validate", "check", "load", "json_schema", "nav_items", "page_node",
    "catalog", "component", "component_names", "to_markdown",
    "COMPONENTS", "CATEGORIES", "ALIASES", "ICONS", "LAYOUT_FIELDS",
    "COMMON_PROPS", "SPEC_VERSION",
    "STYLES", "STYLE_INFO", "DEFAULT_STYLE", "StyleError",
    "normalize_style", "resolve_style", "choose_style", "relaunch",
    "describe", "save_style", "saved_style", "read_config", "write_config",
]
