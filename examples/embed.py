"""Embed a TkUI component tree in an existing Tk window."""
import tkinter as tk
from tkinter import ttk

import tkui


def main():
    root = tk.Tk()
    root.title("嵌入示例")
    root.geometry("760x520")

    header = ttk.Frame(root, padding=(20, 16))
    header.pack(fill="x")
    ttk.Label(header, text="宿主窗口（普通 ttk）").pack(anchor="w")

    panel = ttk.Frame(root, padding=(20, 0, 20, 20))
    panel.pack(fill="both", expand=True)

    tkui.mount(
        panel,
        {
            "type": "column",
            "gap": 12,
            "children": [
                {"type": "section", "title": "TkUI 嵌入内容", "children": [
                    {"type": "label", "text": "这段内容由 TkUI 渲染。"},
                    {"type": "entry", "id": "embedded_name",
                     "label": "名称", "placeholder": "试试输入"},
                    {"type": "row", "children": [
                        {"type": "button", "text": "发通知", "variant": "primary",
                         "command": "notify"},
                    ]},
                ]},
            ],
        },
        style="web",
        actions={
            "notify": lambda event: event.app.notify(
                "你好，" + (event.app.get("embedded_name") or "朋友"), kind="success")
        },
    )

    root.mainloop()


if __name__ == "__main__":
    main()
