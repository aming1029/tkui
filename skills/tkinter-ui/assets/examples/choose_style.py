"""Pick a style with the built-in chooser, then run a spec."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for base in (HERE.parents[1] / "runtime", HERE.parents[3]):
    if (base / "tkui" / "__init__.py").is_file():
        sys.path.insert(0, str(base))
        break

import tkui  # noqa: E402


def main():
    style = tkui.choose_style()
    app = tkui.App(HERE / "dashboard.json", style=style)
    app.run()


if __name__ == "__main__":
    main()
