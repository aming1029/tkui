# TkWebUI direct-use guide (`web` look)

Modern Web application style for tkinter/ttk. Standard library only; no image assets.
Use this reference only when the chosen look is `web` and you are writing upstream
code directly (Mode A).

## Setup

```python
import tkinter as tk
from tkinter import ttk
from tkwebui import enable_dpi_awareness, apply_theme

enable_dpi_awareness()          # before Tk()
root = tk.Tk()
apply_theme(root)               # before creating widgets
root.mainloop()
```

Options:

```python
apply_theme(root, font_family="Microsoft YaHei UI", font_size=10,
            accent="#087DFF", accent_hover="#066BDB")
```

Import styles:

- `from tkwebui import ...` for all public components.
- `from tkwebui.charts import LineChart` etc. when keeping imports narrow.

## Theme coverage

ttk widgets automatically use the theme after `apply_theme`:

`Button`, `Entry`, `Spinbox`, `Checkbutton`, `Radiobutton`, `LabelFrame`,
`Notebook`, `Panedwindow`, `Treeview`, `Progressbar`, `Scale`, `Scrollbar`,
`Separator`, `Sizegrip`.

Common ttk styles:

| Style | Use |
| --- | --- |
| `Primary.TButton` | main action |
| `TButton` | secondary action |
| `Quiet.TButton` | low-emphasis action |
| `Danger.TButton` / `Success.TButton` | destructive / success |
| `Toggle.TButton` | toggle button (`ToggleButton`) |
| `Toolbutton` | icon-only toolbar button (`ToolButton`) |
| `Switch.TCheckbutton` | round switch |
| `Square.Switch.TCheckbutton` | square switch (`SquareSwitch`) |

Classic `tk.Button`, `tk.Text`, `tk.Menu` are **not** automatically replaced.
Use ttk or the components below.

## Layout and containers

```python
from tkwebui import Card, SectionCard, Sidebar, SegmentedControl
from tkwebui import ScrollArea, Accordion, SettingRow

card = Card(parent, selected=False, padding=18)
card.pack(fill="x")

section = SectionCard(parent, text="Basic settings", padding=14)
section.pack(fill="x")
ttk.Label(section, text="Any widget here").pack(anchor="w")

sidebar = Sidebar(parent, [
    ("home", "Home", "settings"),
    ("data", "Data", "folder"),
], command=lambda key: print(key), width=230)
sidebar.pack(side="left", fill="y")

area = ScrollArea(parent)
area.pack(fill="both", expand=True)
ttk.Label(area.body, text="Scrollable content").pack(anchor="w")
```

Notes:

- `Sidebar.items` is `(key, label, icon)` triples; the icon names are the shared
  icon set (check `tkwebui.icon`).
- `ScrollArea.body` is the content frame.
- `Accordion(parent, title, opened=False).body` is the collapsible content.
- `SettingRow(parent, title, description).action` is the right-side action frame.
- `SegmentedControl(parent, [(value, label), ...], variable, command=...)`.

## Inputs

```python
from tkwebui import (PlaceholderEntry, set_placeholder, ThemedCombobox,
                     RoundedText, DateEntry, ValidatedEntry, ValueSlider)

entry = PlaceholderEntry(parent, placeholder="Name")
set_placeholder(existing_entry, "Search")       # existing Entry/Combobox/Spinbox

combo = ThemedCombobox(parent, values=["Low", "Mid", "High"], state="readonly")
text = RoundedText(parent, height=6)            # real tk.Text, methods preserved
date = DateEntry(parent, value="2026-10-30")
price = ValidatedEntry(parent, kind="float", minimum=0, label="Price")
volume = ValueSlider(parent, from_=0, to=10, step=1, unit="level")
```

`PlaceholderEntry`/`set_placeholder` keep the real value empty: `get()` returns `""`
even while the hint is visible.

Use `ThemedCombobox` when the native ttk dropdown popup must match the theme.

## Buttons and choices

```python
from tkwebui import ToggleButton, ToolButton, SquareSwitch, MenuButton, OptionMenu

ttk.Button(parent, text="Save", style="Primary.TButton",
           command=save).pack()
ToggleButton(parent, text="Favorite", variable=tk.BooleanVar(value=True)).pack()
ToolButton(parent, text="+").pack()
SquareSwitch(parent, text="Auto sync", variable=tk.BooleanVar(value=True)).pack()

value = tk.StringVar(value="Normal")
OptionMenu(parent, value, "Normal", "Normal", "Important", "Urgent").pack(fill="x")
```

## Menus and dialogs

```python
from tkwebui import MenuButton, ThemedMenu, icon, Dialogs, notify

button = MenuButton(parent, text="More")
menu = ThemedMenu(button, tearoff=False)
submenu = ThemedMenu(menu, tearoff=False)
submenu.add_command(label="CSV", command=export_csv)
menu.add_command(label="New", image=icon(root, "plus", 16), compound="left",
                 accelerator="Ctrl+N", command=new)
menu.add_cascade(label="Export", menu=submenu)
button.configure(menu=menu)

Dialogs.info(root, "Saved")
ok = Dialogs.confirm(root, "Delete this item?", danger=True)
notify(root, "Done", kind="success", position="bottom-right")
```

Right-click menus use `menu.tk_popup(event.x_root, event.y_root)`.

## Tables and lists

```python
from tkwebui import SortableTreeview, Spreadsheet, DataTable, RoundedListbox

tree = SortableTreeview(parent, columns=("name", "count"), show="headings")
tree.heading("name", text="Name")
tree.insert("", "end", values=("Item 2", 10))

sheet = Spreadsheet(parent, data=[["Item", "Count"], ["A", "12"]],
                    rows=24, columns=8)

table = DataTable(parent, columns=[
    {"key": "name", "text": "Name", "width": 240},
    {"key": "count", "text": "Count", "width": 100},
], rows=[["A", 12], ["B", 7]], page_size=10)

listbox = RoundedListbox(parent, height=8)
```

- `SortableTreeview` sorts on heading click.
- `Spreadsheet` supports rectangular selection, Ctrl+C/V to Excel, undo/redo.
- `DataTable` has search, per-column filter, pagination, column management, CSV export.
- `configure_table(tree)` enables sorting and responsive scrollbars for an existing Treeview.

## Charts

```python
from tkwebui import LineChart, ColumnChart, ScatterChart, DonutChart, PieChart

line = LineChart(parent, values=[12, 18, 14, 26],
                 labels=["Mon", "Tue", "Wed", "Thu"], height=230)
line.set_data(values=[15, 20, 18, 30])

column = ColumnChart(parent, labels=["A", "B"], series=[
    {"name": "Plan", "values": [10, 20]},
    {"name": "Actual", "values": [12, 18]},
])

scatter = ScatterChart(parent, series=[
    {"name": "Obs", "points": [(1, 2), (2.5, 4)]},
])

donut = DonutChart(parent, data=[("Done", 42), ("Doing", 18)])
pie = PieChart(parent, data=[("A", 3), ("B", 5)])
```

Callbacks and data:

```python
chart = LineChart(parent, values=[1, 2, 3],
                  on_click=lambda point: print(point))
chart.get_data()
chart.set_data(values=[3, 2, 1])
chart.toggle_series("Data")
chart.reset_view()
```

Charts are Canvas-native, no NumPy/Matplotlib; use them for dozens to a few
thousand points, not as a plotting library replacement.

## Feedback and status

```python
from tkwebui import Badge, TextProgress, Meter, ToastNotification

Badge(parent, text="Done", kind="success")
TextProgress(parent, value=62, text="Build")
Meter(parent, value=72, subtext="Health")
ToastNotification(root, "Saved", kind="success", duration=2500,
                  position="bottom-right").show_toast()
```

`notify(root, message, **kwargs)` is the short form.

## Media

```python
from tkwebui import ImageViewer, ColorPicker, FontPicker

viewer = ImageViewer(parent, height=300)
viewer.load("photo.png")
ColorPicker(parent, color="#087DFF", command=print)
FontPicker(parent, font="TkDefaultFont")
```

`ImageViewer` supports PNG/GIF/PPM/PGM natively; other formats need Pillow.

## Window chrome

`WindowChrome(root, toolbar, drag_widgets=(), on_close=None, sidebar=None)` is
optional and Windows-focused. Call `detach()` before closing the window. Most
apps should keep the system title bar.

## Common pitfalls

| Symptom | Cause / fix |
| --- | --- |
| Widgets look unthemed | `apply_theme` called after widget creation |
| Combobox popup looks native | use `ThemedCombobox` |
| Classic tk.Button not themed | TkWebUI does not patch classic widgets; use ttk |
| Blank / invisible scrollbar | use `AutoScrollbar` with grid, or `configure_table` |
| Mixing errors / weird styles | `tkwin11` also imported in the same process |
| Image will not load | format unsupported; install Pillow |
| Heavy startup | expected static theme generation; reuse one root |

## Full example

```python
import tkinter as tk
from tkinter import ttk
from tkwebui import enable_dpi_awareness, apply_theme, Card, DataTable

enable_dpi_awareness()
root = tk.Tk()
apply_theme(root)
root.geometry("900x620")

outer = ttk.Frame(root, padding=20)
outer.pack(fill="both", expand=True)

ttk.Label(outer, text="Tasks", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
entry = ttk.Entry(outer)
entry.pack(fill="x", pady=10)

card = Card(outer)
card.pack(fill="both", expand=True, pady=10)
table = DataTable(card, columns=["Task", "Owner", "Status"],
                  rows=[["Review", "Mia", "Doing"]], page_size=8)
table.pack(fill="both", expand=True)

ttk.Button(outer, text="Save", style="Primary.TButton").pack(anchor="e")
root.mainloop()
```
