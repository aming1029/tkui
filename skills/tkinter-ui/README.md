# tkinter-ui skill

An Agent Skill for building Python tkinter UIs with:

- **TkWebUI** — modern Web look;
- **TkWin11** — Windows 11 Fluent look;
- **TkUI** — bundled declarative JSON runtime that renders the same spec in both.

The skill routes between direct upstream code (Mode A) and declarative TkUI specs
(Mode B), so it covers single-file tools and multi-page apps with a user-selectable
look.

## Install

Copy this directory, or link it, into your runtime's skills directory:

```text
~/.codex/skills/tkinter-ui
~/.claude/skills/tkinter-ui
~/.agents/skills/tkinter-ui
```

On Windows, a directory junction works without admin rights:

```powershell
New-Item -ItemType Junction -Path "$HOME\.codex\skills\tkinter-ui" `
  -Target "D:\path\to\tkui\skills\tkinter-ui"
```

## Requirements

- Python 3.8+ with tkinter.
- No extra install is required: the skill bundles the TkUI runtime in
  `runtime/tkui` and both upstream packages in
  `runtime/vendor/tkwebui` / `runtime/vendor/tkwin11`.
- If you prefer a project-local or pip-installed copy of the upstreams, set
  `TKUI_TKWEBUI_PATH` / `TKUI_TKWIN11_PATH`; the bundled copy remains the
  fallback.
- If you move the TkUI runtime out of `runtime/`, set `TKUI_HOME` to the directory
  containing `tkui/`.

Optional environment variables:

```text
TKUI_TKWEBUI_PATH=D:\path\to\tkwebui-main
TKUI_TKWIN11_PATH=D:\path\to\tkwin11-main
```

## Try it

```bash
python scripts/selftest.py --render
python scripts/scaffold.py --style web --kind dashboard --output app.py
python scripts/scaffold.py --style win11 --kind form --output app.py
python scripts/choose_style.py
python scripts/use_tkui.py demo --choose
python scripts/use_tkui.py check assets/examples/dashboard.json --json
python scripts/use_tkui.py run assets/examples/dashboard.json --style win11
```

## Layout

```text
SKILL.md               routing + rules
references/
  research.md          effect comparison and selection guide
  tkwebui.md           direct TkWebUI API
  tkwin11.md           direct TkWin11 API
  components.md        component map + full TkUI catalog
  spec.md              declarative spec reference
  declarative.md       Mode B workflow and actions
scripts/
  scaffold.py          generate direct-upstream starter code
  check.py             static check for .py, full check for .json
  choose_style.py      user-facing Web/Win11 chooser
  use_tkui.py          catalog/check/run/demo/choose
  selftest.py          examples + scaffold + optional render test
  sync_runtime.py      refresh runtime/tkui from the repo
assets/
  examples/            runnable examples
  images/              screenshots
runtime/tkui/          bundled declarative runtime
runtime/vendor/        bundled MIT upstream packages
```

## License

MIT. TkWebUI and TkWin11 are MIT-licensed upstream projects by bvb6417; their
licenses are kept in `runtime/vendor/`.
