"""Pick a style with the built-in chooser, then run a spec."""
from pathlib import Path

import tkui

HERE = Path(__file__).resolve().parent


def main():
    style = tkui.choose_style()
    app = tkui.App(HERE / "dashboard.json", style=style)
    app.run()


if __name__ == "__main__":
    main()
