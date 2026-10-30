"""Ask the user for web/win11 with the dependency-free chooser.

    python scripts/choose_style.py
    python scripts/choose_style.py --default web --json

The choice is saved for the next launch unless --no-remember is passed.
"""
from __future__ import annotations

import argparse
import json

from _bootstrap import add_runtime


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--default", choices=["web", "win11"])
    parser.add_argument("--no-remember", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    add_runtime()
    import tkui

    style = tkui.choose_style(default=args.default,
                              remember=not args.no_remember)
    if args.json:
        print(json.dumps({"style": style, "info": tkui.describe(style)},
                         ensure_ascii=False, indent=2))
    else:
        print(style)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
