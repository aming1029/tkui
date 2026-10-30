"""Run a spec with Python callbacks."""
from pathlib import Path

import tkui

HERE = Path(__file__).resolve().parent


def main():
    holder = {}

    def on_save(event):
        name = event.app.get("name") or "（空）"
        event.app.notify(f"已保存：{name}", title="TkUI", kind="success")

    def on_style(event):
        event.app.restart_in_style(event.value)

    app = tkui.App(
        HERE / "minimal.json",
        actions={"save": on_save, "style": on_style},
        style=None,   # None = 环境变量/配置文件/默认值
    )
    holder["app"] = app
    app.run()


if __name__ == "__main__":
    main()
