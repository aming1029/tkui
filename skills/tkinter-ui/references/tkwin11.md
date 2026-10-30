# TkWin11 direct-use guide (`win11` look)

Windows 11 Fluent style for tkinter/ttk. Standard library only. Use this reference
only when the chosen look is `win11` and you are writing upstream code directly
(Mode A).

## Setup

New app:

```python
import tkinter as tk
from tkinter import ttk
import tkwin11 as ui

ui.enable_dpi_awareness()       # before Tk()
root = tk.Tk()
ui.apply_theme(root)            # before widgets
ui.configure_fluent(root)       # FluentPage / workspace styles
root.mainloop()
```

Existing app, one-line upgrade:

```python
import tkwin11; tkwin11.install()   # BEFORE the first tk.Tk()

import tkinter as tk
root = tk.Tk()
```

`install(dpi=True, classic=True, lock_theme=True)` also restyles classic
`tk.Button`, `tk.Label`, `tk.Menu`, `tk.Entry`, etc. Use `install(dpi=False)` for
programs that hard-code pixel geometry. `uninstall()` undoes the hook for future
roots. `apply_theme(root)` and `theme_classic(root)` work on an existing root.

Theme options:

```python
ui.apply_theme(root, font_family="Microsoft YaHei UI", font_size=10,
               accent="#0067C0", accent_hover="#1975C5")
```

## Theme coverage

ttk widgets and classic widgets (after `install`/`theme_classic`) are themed.
The Fluent look adds motion and per-monitor DPI. The shared TkWebUI components
(`Card`, `DataTable`, `Spreadsheet`, charts, `DateEntry`, `Dialogs`, etc.) are
also present with the same names; see `components.md`.

## Fluent layout

```python
from tkwin11 import FluentPage, SettingsCard, ExpanderCard, NavigationView

page = FluentPage(root)
page.pack(fill="both", expand=True)

card = SettingsCard(page.body, "Auto save", "Save settings on exit",
                    symbol="download")
card.pack(fill="x", pady=8)
ui.FluentSwitch(card.actions, variable=tk.BooleanVar(value=True)).pack()

expander = ExpanderCard(page.body, "Advanced", "More options",
                        symbol="settings", opened=False)
expander.pack(fill="x", pady=8)

nav = NavigationView(root, command=lambda key: print(key), width=300)
nav.add("home", "Home", "controls")
nav.add_group("tools", "Tools", "folder", opened=True)
nav.add("convert", "Convert", "play", parent="tools")
nav.pack(side="left", fill="y")
```

`FluentPage.body` is the content frame. `SettingsCard.actions` is the trailing
control area. `ExpanderCard.body` is the collapsible content.

## Controls

```python
from tkwin11 import (FluentButton, FluentSwitch, FluentSlider, KeyChord,
                     FormFlyout, SegmentedControl, ThemedCombobox,
                     PlaceholderEntry, DateEntry, ValidatedEntry)

FluentButton(parent, text="Save", style="Primary.TButton").pack()
FluentSwitch(parent, variable=tk.BooleanVar(value=True)).pack()
slider = FluentSlider(parent, from_=0, to=10)
slider.set(4)
slider.pack(fill="x")
KeyChord(parent, value="Ctrl+S", command=print).pack(anchor="w")

SegmentedControl(parent, [("day", "Day"), ("week", "Week")],
                 tk.StringVar(value="day")).pack(anchor="w")

combo = ThemedCombobox(parent, values=["A", "B"], state="readonly")
entry = PlaceholderEntry(parent, placeholder="Name")
date = DateEntry(parent, value="2026-10-30")
number = ValidatedEntry(parent, kind="integer", minimum=0)

flyout = FormFlyout(button, width=310)
```

Most shared controls use the same signatures as TkWebUI: `Card`, `SectionCard`,
`Sidebar`, `ScrollArea`, `Accordion`, `SettingRow`, `SortableTreeview`,
`Spreadsheet`, `DataTable`, `LineChart`, `ColumnChart`, `ScatterChart`,
`DonutChart`, `PieChart`, `Badge`, `Dialogs`, `notify`, `TextProgress`, `Meter`,
`ColorPicker`, `FontPicker`, `ImageViewer`.

## Title bar and window chrome

`FluentTitleBar` provides an integrated Win11 title bar:

```python
from tkwin11 import FluentTitleBar, apply_theme, configure_fluent

apply_theme(root)
configure_fluent(root)

sidebar = ...   # create first if you want the brand area to match it
titlebar = FluentTitleBar(root, title="My app", sidebar_width=300,
                          sidebar=sidebar, on_close=root.destroy)
titlebar.pack(side="top", fill="x")

shell = ttk.Frame(root)
shell.pack(fill="both", expand=True)
```

`FluentWindowChrome` handles drag, snap, resize, maximize and close for a custom
toolbar. Keep the system title bar unless the whole window layout is custom.

## Motion and DPI

- Controls have hover/press/focus transitions; switches, sliders, navigation and
  pages animate.
- Fonts, images and geometry are adapted per monitor; moving the window across
  displays reflows it.
- `install(dpi=False)` disables the DPI hook if the app relies on fixed pixels.

## Common pitfalls

| Symptom | Cause / fix |
| --- | --- |
| Classic buttons still look standard | `install()`/`theme_classic` not called |
| Theme lost after `theme_use("clam")` | `install(lock_theme=True)` keeps the theme |
| FluentPage styles missing | call `configure_fluent(root)` after `apply_theme` |
| Title bar overlaps / no sidebar | pass the real sidebar to `FluentTitleBar` |
| Window does not close cleanly | wire `on_close`/`WM_DELETE_WINDOW` |
| `can't delete Tcl command` on exit (Tk 9) | harmless upstream teardown noise; filter it |
| Mixing styles | `tkwebui` also imported in the same process |
| Hard-coded pixel geometry misplaced | use `install(dpi=False)` or DPI-aware sizes |

## Full example

```python
import tkinter as tk
import tkwin11 as ui

ui.enable_dpi_awareness()
root = tk.Tk()
root.title("Tasks")
root.geometry("900x620")
ui.apply_theme(root)
ui.configure_fluent(root)

page = ui.FluentPage(root)
page.pack(fill="both", expand=True)

ui.SettingsCard(page.body, "Auto save", "Save settings on exit",
                symbol="download").pack(fill="x", pady=10)

ui.PlaceholderEntry(page.body, placeholder="Search tasks").pack(fill="x", pady=10)

table = ui.DataTable(page.body, columns=["Task", "Owner", "Status"],
                     rows=[["Review", "Mia", "Doing"]], page_size=8)
table.pack(fill="both", expand=True)

root.mainloop()
```
