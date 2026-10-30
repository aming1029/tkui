"""Subprocess helper: render every component in one style."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import tkui  # noqa: E402


def spec():
    data_children = [
        {"type": "heading", "title": "全部组件", "subtitle": "render smoke test"},
        {
            "type": "grid",
            "columns": 2,
            "gap": 10,
            "children": [
                {
                    "type": "card",
                    "children": [
                        {"type": "label", "text": "卡片", "style": "strong"},
                        {"type": "label", "text": "muted", "style": "muted"},
                        {"type": "badge", "text": "info", "kind": "info"},
                    ],
                },
                {
                    "type": "section",
                    "title": "输入",
                    "children": [
                        {"type": "entry", "id": "name", "label": "名称", "value": "abc"},
                        {"type": "entry", "id": "pwd", "kind": "password"},
                        {"type": "entry", "id": "num", "kind": "integer", "min": 1, "max": 9,
                         "value": "3"},
                        {"type": "text", "id": "notes", "height": 3, "value": "text"},
                        {"type": "combo", "id": "combo", "values": ["A", "B"], "value": "A"},
                        {"type": "dropdown", "id": "drop", "values": ["A", "B"]},
                        {"type": "spinbox", "id": "spin", "min": 0, "max": 10, "value": 2},
                        {"type": "date", "id": "date", "value": "2026-10-30"},
                    ],
                },
            ],
        },
        {
            "type": "section",
            "title": "选择与显示",
            "children": [
                {"type": "checkbox", "id": "check", "text": "复选"},
                {"type": "switch", "id": "switch", "label": "开关", "value": True},
                {"type": "radio_group", "id": "radio", "options": ["一", "二"], "value": "一"},
                {"type": "segmented", "id": "seg", "options": ["日", "周"], "value": "日"},
                {"type": "slider", "id": "slider", "min": 0, "max": 10, "value": 4},
                {"type": "progress", "id": "progress", "value": 30},
                {"type": "meter", "id": "meter", "value": 50, "shape": "semi"},
                {"type": "keychord", "id": "chord", "value": "Ctrl+S"},
                {"type": "stat", "label": "指标", "value": "42", "delta": "+1",
                 "kind": "success"},
                {"type": "alert", "title": "提醒", "message": "测试", "kind": "warning"},
            ],
        },
        {
            "type": "settings_card",
            "title": "设置卡片",
            "description": "说明",
            "children": [{"type": "switch", "value": False}],
        },
        {
            "type": "settings_row",
            "title": "设置行",
            "description": "说明",
            "children": [{"type": "button", "text": "操作"}],
        },
        {
            "type": "expander",
            "title": "展开",
            "description": "说明",
            "opened": True,
            "children": [{"type": "label", "text": "展开内容"}],
        },
        {
            "type": "accordion",
            "title": "折叠",
            "opened": True,
            "children": [{"type": "label", "text": "折叠内容"}],
        },
        {
            "type": "tabs",
            "children": [
                {"type": "tab", "title": "一", "children": [
                    {"type": "label", "text": "tab one"},
                    {"type": "row", "children": [
                        {"type": "button", "text": "主要", "variant": "primary", "id": "btn"},
                        {"type": "button", "text": "危险", "variant": "danger"},
                        {"type": "button", "text": "链接", "variant": "link"},
                        {"type": "button", "text": "工具", "variant": "tool", "icon": "plus"},
                    ]},
                ]},
                {"type": "tab", "title": "二", "children": [
                    {"type": "color", "id": "color"},
                    {"type": "font", "id": "font"},
                ]},
            ],
        },
        {
            "type": "section",
            "title": "数据",
            "children": [
                {"type": "table", "id": "table", "columns": ["A", "B"],
                 "rows": [["x", 1], ["y", 2]], "page_size": 3, "height": 3},
                {"type": "tree", "id": "tree", "columns": ["A", "B"],
                 "rows": [["x", 1]], "height": 3},
                {"type": "list", "id": "list", "items": ["a", "b"], "value": 0,
                 "height": 3},
                {"type": "spreadsheet", "id": "sheet", "data": [["a", "b"]],
                 "rows": 6, "columns": 4},
                {"type": "image", "id": "image", "height": 120},
            ],
        },
        {
            "type": "grid",
            "columns": 2,
            "gap": 10,
            "children": [
                {"type": "chart", "kind": "line", "values": [1, 2, 3],
                 "labels": ["a", "b", "c"], "height": 140},
                {"type": "chart", "kind": "column", "values": [1, 2], "labels": ["a", "b"],
                 "height": 140},
                {"type": "chart", "kind": "scatter", "series": [
                    {"name": "s", "points": [(1, 2), (2, 3)]}], "height": 140},
                {"type": "chart", "kind": "donut", "data": [["a", 1], ["b", 2]],
                 "height": 140},
                {"type": "chart", "kind": "pie", "data": [["a", 1], ["b", 2]],
                 "height": 140},
            ],
        },
        {"type": "separator"},
        {"type": "spacer", "size": 10},
        {"type": "scroll", "height": 120, "children": [
            {"type": "label", "text": "scroll body"},
        ]},
    ]
    return {
        "version": 1,
        "title": "all components",
        "window": {"size": [1000, 760]},
        "nav": {"mode": "sidebar", "items": [
            {"key": "gallery", "label": "Gallery", "icon": "controls"}]},
        "pages": {"gallery": {"type": "page", "title": "Gallery",
                              "children": data_children}},
    }


def main(style):
    app = tkui.App(spec(), style=style, actions={
        "save": lambda event: None,
    })
    app.root.withdraw()
    app.root.update_idletasks()
    expected = ["name", "pwd", "num", "notes", "combo", "drop", "spin", "date",
                "check", "switch", "radio", "seg", "slider", "progress", "meter",
                "chord", "btn", "color", "font", "table", "tree", "list", "sheet",
                "image"]
    missing = [item for item in expected if item not in app.widgets]
    if missing:
        raise SystemExit(f"missing widgets: {missing}")
    assert app.get("name") == "abc", app.get("name")
    app.set("name", "changed")
    assert app.get("name") == "changed"
    assert app.get("switch") is True
    app.set("switch", False)
    assert app.get("switch") is False
    assert app.get("spin") == 2
    assert len(app.get("table")) == 2
    app.set("table", [["z", 9]])
    assert len(app.get("table")) == 1
    assert app.get("sheet")[0][0] == "a"
    app.navigate("gallery")
    app.root.update_idletasks()
    print(f"OK {style} widgets={len(app.widgets)}")
    app.close()


if __name__ == "__main__":
    main(sys.argv[1])
