---
name: tkinter-ui
description: Use when building or modifying Python tkinter desktop UIs with TkWebUI or TkWin11, when the user asks for a modern web-style or Windows 11 Fluent look, or when one interface must offer a user-selectable Web/Win11 theme.
---

# Tkinter UI: TkWebUI / TkWin11 / TkUI

This skill covers two upstream libraries and one bundled declarative runtime:

- **TkWebUI** (`tkwebui`) — modern Web application look: white surfaces, rounded cards, `#087DFF`, no animation.
- **TkWin11** (`tkwin11`) — Windows 11 Fluent look: Mica-like workspace, `#0067C0`, motion, per-monitor DPI, optional integrated title bar.
- **TkUI** (`runtime/tkui`) — a style-neutral JSON layer over both. Same spec, `--style web|win11`.

The two upstream libraries must never be imported into the same Tk interpreter.

Prerequisites: Python 3.8+ with tkinter. The skill bundles the declarative runtime
(`runtime/tkui`) and both upstream packages (`runtime/vendor/tkwebui`,
`runtime/vendor/tkwin11`), so it works without a separate checkout. If the project
already has `tkwebui` / `tkwin11` installed or vendored, those still work; override
with `TKUI_TKWEBUI_PATH` / `TKUI_TKWIN11_PATH` when needed.

## Step 0 — Choose the implementation shape

| Situation | Use |
| --- | --- |
| One screen, one file, special upstream widget, existing tkinter app | **A. Direct upstream code** |
| Multi-page app, dashboard, form/table-heavy, two looks from one source, AI-generated UI | **B. Declarative TkUI spec** |
| Small change to an existing themed app | **A** |
| User explicitly wants to switch Web/Win11 at runtime | **B** |

Default: A for one screen; B when there are pages, several data-heavy components, or a real style-switch requirement.

Do not build B for a five-line demo. Do not hand-write two versions of a full app when B covers it.

## Step 1 — Pick the look

| Look | Choose when |
| --- | --- |
| `web` | Internal tools, research/engineering utilities, dense data views, predictable behavior |
| `win11` | App distributed to Windows 11 users, native title bar, animations, per-monitor DPI |

If the user has no preference, use `web`. If the app is for Windows desktop users, prefer `win11`.

To ask the user with a small dependency-free dialog:

```bash
python scripts/choose_style.py
```

For B, the look can be selected at launch (`--style`), stored in config, or chosen by the user with `choose_style()`. Runtime switching restarts the process.

---

## Mode A — Direct upstream code

Read exactly one of:

- `references/tkwebui.md` for `web`
- `references/tkwin11.md` for `win11`

Then scaffold:

```bash
python scripts/scaffold.py --style web --kind dashboard --output app.py
python scripts/scaffold.py --style win11 --kind form --output app.py
```

Minimal setup:

```python
# web
from tkwebui import enable_dpi_awareness, apply_theme
enable_dpi_awareness()          # before Tk()
root = tk.Tk()
apply_theme(root)               # before widgets
```

```python
# win11 — new app
import tkwin11 as ui
ui.enable_dpi_awareness()       # before Tk()
root = tk.Tk()
ui.apply_theme(root)
ui.configure_fluent(root)
```

```python
# win11 — existing app, before Tk()
import tkwin11; tkwin11.install()
```

Rules for A:

- Use ttk or the library's own widgets; classic `tk.Button` only gets themed in `win11` via `install()`.
- Call `apply_theme` before creating widgets.
- Use `ThemedCombobox` when the dropdown popup must match the theme.
- Use `ttk.Style().map/configure` or documented variants instead of hardcoded colors.
- Do not import the other library.

Check the result:

```bash
python scripts/check.py app.py
```

---

## Mode B — Declarative TkUI spec

Read:

- `references/declarative.md` — workflow, actions, validation loop
- `references/spec.md` — fields, layout, component rules
- `references/components.md` — full component/property catalog

Commands (run from this skill directory):

```bash
python scripts/use_tkui.py catalog
python scripts/use_tkui.py check app.json --json
python scripts/use_tkui.py run app.json --style web
python scripts/use_tkui.py run app.json --style win11
python scripts/use_tkui.py demo --choose
```

Minimal spec:

```json
{
  "version": 1,
  "title": "My tool",
  "body": {
    "type": "column",
    "padding": 24,
    "gap": 12,
    "children": [
      {"type": "heading", "title": "Hello", "subtitle": "One spec, two looks"},
      {"type": "entry", "id": "name", "label": "Name"},
      {"type": "button", "text": "Save", "variant": "primary", "command": "save"}
    ]
  }
}
```

Python bridge:

```python
import tkui

def on_save(event):
    event.app.notify("Saved: " + event.app.get("name"), kind="success")

app = tkui.App("app.json", actions={"save": on_save})
app.run()
```

Rules for B:

- Output JSON only; no Tk code unless the user asks for Python integration.
- Use `id` only on controls that must be read or updated.
- Use `variant` / `kind` / `layout`, never colors, fonts, or backend branches.
- Use built-in actions for a runnable prototype; named actions for business logic.
- Validate with `check --json` and fix by JSON path. Do not guess after a validation error.
- If a required widget is missing from the catalog, either switch to A or extend the runtime; do not fake it with raw Tk.

Style switching in B:

```python
style = tkui.choose_style()          # user picks web/win11, saved
app = tkui.App(spec, style=style)
```

```python
app.restart_in_style("win11")        # saves preference and relaunches
```

---

## Routing rules

Use A when:

- there is one window and one main task;
- the task needs a specific upstream API not covered by the catalog;
- the user already has tkinter code and wants a reskin;
- the output should be a single, dependency-light `.py`;
- the user wants `FluentTitleBar`, `KeyChord`, `FormFlyout`, `NavigationView` groups, or custom canvas work.

Use B when:

- there are multiple pages or a sidebar/segmented navigation;
- the app is mostly forms, tables, charts, settings cards;
- the same interface must be previewed as both `web` and `win11`;
- an AI is generating the UI from a description and validation matters;
- the user wants a style chooser or a saved preference.

Mixed use is allowed only across processes or as embedding:

- A host app themed with one library can embed a B tree of the same style via `tkui.mount(frame, node, style=...)`.
- Never import both upstream libraries in one process.

## Non-negotiables

- Never import `tkwebui` and `tkwin11` in the same Tk interpreter.
- Call `enable_dpi_awareness()` before `Tk()` and `apply_theme(root)` before widgets.
- Never write theme-specific style names into a B spec.
- Keep user-facing text in the user's language.
- Do not silently swallow spec validation errors or upstream callback exceptions.
- In `win11`, only use `window.chrome: "custom"` if you can test the title bar; Web falls back to the system title bar.

## Reference map

Read only what the task needs:

- `references/research.md` — what each library looks like and which to choose.
- `references/tkwebui.md` — direct TkWebUI API and pitfalls.
- `references/tkwin11.md` — direct TkWin11 API and pitfalls.
- `references/components.md` — both libraries + TkUI component names and properties.
- `references/spec.md` — declarative spec reference.
- `references/declarative.md` — AI-oriented declarative workflow and actions.

Examples are in `assets/examples/`; screenshots are in `assets/images/`.
Machine-readable assets: `assets/catalog.json` (component catalog) and
`assets/tkui-1.schema.json` (JSON Schema).

## Verification

```bash
python scripts/selftest.py
python scripts/check.py app.py
python scripts/use_tkui.py check app.json --json
python scripts/use_tkui.py run app.json --style web
python scripts/use_tkui.py run app.json --style win11
```

The bundled runtime lives in `runtime/tkui`. If it is moved, set `TKUI_HOME` to the directory that contains the `tkui` package.
