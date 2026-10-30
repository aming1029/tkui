"""Run a spec with Python callbacks."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for base in (HERE.parents[1] / "runtime", HERE.parents[3]):
    if (base / "tkui" / "__init__.py").is_file():
        sys.path.insert(0, str(base))
        break

import tkui  # noqa: E402


def main():
    holder = {}

    def on_save(event):
        name = event.app.get("name") or "（空）"
        event.app.notify(f"已保存：{name}", title="TkUI", kind="success")

    app = tkui.App(
        HERE / "minimal.json",
        actions={"save": on_save},
        style=None,   # None = 环境变量/配置文件/默认值
    )
    holder["app"] = app
    app.run()


if __name__ == "__main__":
    main()
