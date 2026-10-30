"""Run the bundled TkUI CLI.

    python scripts/use_tkui.py catalog
    python scripts/use_tkui.py check app.json --json
    python scripts/use_tkui.py run app.json --style web
"""
from __future__ import annotations

import sys

from _bootstrap import add_runtime, add_upstream


def main(argv=None):
    add_runtime()
    add_upstream("tkwebui")
    add_upstream("tkwin11")
    from tkui.__main__ import main as tkui_main
    return tkui_main(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())
