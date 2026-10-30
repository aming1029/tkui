# Examples

## Mode A — direct upstream code

```bash
python web_app.py          # TkWebUI dashboard
python win11_app.py        # TkWin11 form
```

Both files include a small `sys.path` bootstrap for sibling
`tkwebui-main/` / `tkwin11-main/` checkouts, the skill's bundled
`runtime/vendor/` copy, or `TKUI_TKWEBUI_PATH` / `TKUI_TKWIN11_PATH`.

## Mode B — declarative specs

```bash
python ../scripts/use_tkui.py run minimal.json --style web
python ../scripts/use_tkui.py run dashboard.json --style win11
```

- `minimal.json` — smallest useful spec.
- `dashboard.json` — pages, stats, charts, table, settings, style switch.

## Python integration

```bash
python python_app.py       # a spec + named actions
python embed.py            # embed a component tree in a plain ttk window
python choose_style.py     # ask the user, then run dashboard.json
```

`python_app.py`, `embed.py`, and `choose_style.py` bootstrap the bundled
`runtime/tkui` automatically.
