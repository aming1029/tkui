"""Bundled gallery: the same pages in both looks, with an in-app style switch."""
from __future__ import annotations

from . import theme as theme_mod


def build_spec(style="web"):
    style = theme_mod.normalize_style(style, allow_auto=False) or "web"
    info = theme_mod.STYLE_INFO[style]
    window = {"size": [1180, 800], "min_size": [960, 640], "centered": True}
    if style == "win11":
        window["chrome"] = "custom"
    return {
        "version": 1,
        "title": f"TkUI 组件画廊 · {'Web' if style == 'web' else 'Win11'}",
        "window": window,
        "nav": {
            "mode": "sidebar",
            "width": 220,
            "selected": "overview",
            "items": [
                {"key": "overview", "label": "概览", "icon": "speed"},
                {"key": "controls", "label": "控件", "icon": "controls"},
                {"key": "data", "label": "数据", "icon": "library"},
                {"key": "charts", "label": "图表", "icon": "folder"},
                {"key": "style", "label": "风格", "icon": "settings"},
            ],
        },
        "pages": {
            "overview": {
                "type": "page",
                "title": "TkUI 组件画廊",
                "subtitle": "同一份声明式规格，两种原生 Tk 外观。用左侧导航切换页面。",
                "children": [
                    {
                        "type": "alert",
                        "kind": "info",
                        "title": f"当前风格：{info['label']}（{info['library']}）",
                        "message": info["summary"],
                    },
                    {
                        "type": "row",
                        "gap": 12,
                        "children": [
                            {"type": "stat", "label": "统一组件", "value": "43",
                             "delta": "Web + Win11", "kind": "info", "icon": "controls",
                             "layout": {"fill": "both", "expand": True}},
                            {"type": "stat", "label": "当前后端", "value": info["library"],
                             "delta": "可一键切换", "kind": "success", "icon": "check",
                             "layout": {"fill": "both", "expand": True}},
                            {"type": "stat", "label": "声明式", "value": "JSON",
                             "delta": "AI 友好", "kind": "warning", "icon": "edit",
                             "layout": {"fill": "both", "expand": True}},
                        ],
                    },
                    {
                        "type": "grid",
                        "columns": 2,
                        "gap": 14,
                        "children": [
                            {
                                "type": "section",
                                "title": "快速体验",
                                "children": [
                                    {"type": "label", "text": "所有动作都由同一套动作模型驱动。"},
                                    {"type": "row", "gap": 8, "children": [
                                        {"type": "button", "text": "发送通知", "variant": "primary",
                                         "icon": "check", "command": "toast"},
                                        {"type": "button", "text": "打开对话框",
                                         "command": "dialog"},
                                        {"type": "button", "text": "关于", "variant": "quiet",
                                         "command": "about"},
                                    ]},
                                    {"type": "separator"},
                                    {"type": "settings_row", "title": "自动保存",
                                     "description": "退出时保存当前设置",
                                     "children": [{"type": "switch", "id": "autosave",
                                                   "value": True}]},
                                    {"type": "settings_row", "title": "界面密度",
                                     "description": "影响列表与表格行高",
                                     "children": [
                                         {"type": "segmented", "id": "density",
                                          "options": ["舒适", "紧凑"], "value": "舒适"}]},
                                ],
                            },
                            {
                                "type": "section",
                                "title": "状态与反馈",
                                "children": [
                                    {"type": "progress", "id": "build_progress",
                                     "value": 68, "text": "构建进度"},
                                    {"type": "row", "gap": 16, "children": [
                                        {"type": "meter", "id": "health", "value": 82,
                                         "subtext": "健康度", "layout": {"fill": "none"}},
                                        {"type": "column", "gap": 8, "children": [
                                            {"type": "badge", "text": "已连接",
                                             "kind": "success"},
                                            {"type": "badge", "text": "2 个警告",
                                             "kind": "warning"},
                                            {"type": "badge", "text": "信息",
                                             "kind": "info"},
                                        ]},
                                    ]},
                                ],
                            },
                        ],
                    },
                    {
                        "type": "section",
                        "title": "每周活动",
                        "children": [
                            {"type": "chart", "kind": "column", "height": 210,
                             "values": [12, 18, 9, 22, 17, 26, 14],
                             "labels": ["一", "二", "三", "四", "五", "六", "日"]},
                        ],
                    },
                ],
            },
            "controls": {
                "type": "page",
                "title": "控件",
                "subtitle": "表单、选择、外观与反馈。不同风格下视觉不同，声明完全一致。",
                "children": [
                    {
                        "type": "tabs",
                        "children": [
                            {
                                "type": "tab",
                                "title": "输入",
                                "children": [
                                    {"type": "section", "title": "文本", "children": [
                                        {"type": "entry", "id": "name", "label": "名称",
                                         "placeholder": "例如：季度复盘"},
                                        {"type": "entry", "id": "password",
                                         "label": "密码", "kind": "password",
                                         "placeholder": "只读演示"},
                                        {"type": "text", "id": "notes", "height": 4,
                                         "value": "这里是多行文本。保留撤销、选择和滚动接口。"},
                                        {"type": "row", "gap": 8, "children": [
                                            {"type": "button", "text": "保存表单",
                                             "variant": "primary", "command": "save_form"},
                                            {"type": "button", "text": "清空",
                                             "variant": "quiet", "command": "clear_form"},
                                        ]},
                                    ]},
                                    {"type": "section", "title": "选择", "children": [
                                        {"type": "combo", "id": "level",
                                         "values": ["低", "中", "高"], "value": "中"},
                                        {"type": "dropdown", "id": "priority",
                                         "values": ["普通", "重要", "紧急"], "value": "普通"},
                                        {"type": "date", "id": "due", "value": "2026-10-30"},
                                        {"type": "spinbox", "id": "count", "min": 1, "max": 99,
                                         "value": 3},
                                    ]},
                                ],
                            },
                            {
                                "type": "tab",
                                "title": "开关与滑块",
                                "children": [
                                    {"type": "section", "title": "开关", "children": [
                                        {"type": "settings_row", "title": "自动同步",
                                         "description": "与远端保持同步",
                                         "children": [{"type": "switch", "id": "sync",
                                                       "value": True}]},
                                        {"type": "settings_row", "title": "启用通知",
                                         "children": [{"type": "checkbox",
                                                       "id": "notify_on", "text": "",
                                                       "value": True}]},
                                    ]},
                                    {"type": "section", "title": "选择与范围", "children": [
                                        {"type": "radio_group", "id": "size",
                                         "options": ["小", "中", "大"], "value": "中"},
                                        {"type": "segmented", "id": "range",
                                         "options": ["日", "周", "月"], "value": "周"},
                                        {"type": "slider", "id": "volume", "min": 0, "max": 10,
                                         "value": 4, "unit": "级"},
                                        {"type": "keychord", "id": "chord",
                                         "value": "Ctrl+S"},
                                    ]},
                                ],
                            },
                            {
                                "type": "tab",
                                "title": "外观",
                                "children": [
                                    {"type": "section", "title": "颜色", "children": [
                                        {"type": "color", "id": "accent_color",
                                         "value": info["accent"]},
                                    ]},
                                    {"type": "section", "title": "字体", "children": [
                                        {"type": "font", "id": "font_picker"},
                                    ]},
                                    {"type": "section", "title": "图片", "children": [
                                        {"type": "image", "id": "image", "height": 220},
                                    ]},
                                ],
                            },
                        ],
                    },
                ],
            },
            "data": {
                "type": "page",
                "title": "数据",
                "subtitle": "数据表、可排序列表、Excel 式表格与列表框。",
                "children": [
                    {
                        "type": "row",
                        "children": [
                            {"type": "button", "text": "添加示例行", "variant": "primary",
                             "icon": "plus", "command": "add_row"},
                            {"type": "spacer", "expand": True},
                            {"type": "badge", "text": "DataTable", "kind": "info"},
                        ],
                    },
                    {
                        "type": "section",
                        "title": "任务（搜索 / 筛选 / 分页 / CSV 导出）",
                        "children": [
                            {"type": "table", "id": "tasks_table",
                             "columns": [
                                 {"key": "name", "text": "任务", "width": 260},
                                 {"key": "owner", "text": "负责人", "width": 130},
                                 {"key": "status", "text": "状态", "width": 110},
                                 {"key": "due", "text": "截止", "width": 110},
                             ],
                             "rows": [
                                 ["支付联调", "小林", "进行中", "10-31"],
                                 ["权限审计", "阿澈", "待开始", "11-03"],
                                 ["数据回填", "Mia", "已完成", "10-28"],
                                 ["发布检查", "Ken", "进行中", "11-01"],
                             ],
                             "page_size": 5, "height": 6},
                        ],
                    },
                    {
                        "type": "grid",
                        "columns": 2,
                        "gap": 14,
                        "children": [
                            {"type": "section", "title": "可排序列表", "children": [
                                {"type": "tree", "id": "tree",
                                 "columns": ["资料", "数量", "状态"],
                                 "rows": [["资料 A", 12, "正常"],
                                          ["资料 B", 7, "延迟"],
                                          ["资料 C", 24, "正常"]]},
                            ]},
                            {"type": "section", "title": "列表", "children": [
                                {"type": "list", "id": "fruit",
                                 "items": ["苹果", "香蕉", "橙子", "葡萄", "西瓜"],
                                 "value": 1, "height": 7},
                            ]},
                        ],
                    },
                    {
                        "type": "section",
                        "title": "Excel 式单元格表格（可多选、复制粘贴、撤销）",
                        "children": [
                            {"type": "spreadsheet", "id": "sheet",
                             "rows": 12, "columns": 7,
                             "data": [
                                 ["项目", "一月", "二月", "三月"],
                                 ["资料整理", "12", "18", "15"],
                                 ["数据清洗", "8", "11", "9"],
                                 ["报告", "3", "5", "7"],
                             ]},
                        ],
                    },
                ],
            },
            "charts": {
                "type": "page",
                "title": "图表",
                "subtitle": "原生 Canvas 图表：悬停提示、图例开关、点击回调、缩放平移。",
                "children": [
                    {"type": "section", "title": "折线图", "children": [
                        {"type": "chart", "kind": "line", "height": 230,
                         "values": [12, 18, 14, 26, 23, 31],
                         "labels": ["一月", "二月", "三月", "四月", "五月", "六月"]},
                    ]},
                    {"type": "grid", "columns": 2, "gap": 14, "children": [
                        {"type": "section", "title": "分组柱状图", "children": [
                            {"type": "chart", "kind": "column", "height": 220,
                             "labels": ["A", "B", "C"],
                             "series": [
                                 {"name": "计划", "values": [10, 20, 30]},
                                 {"name": "实际", "values": [12, 18, 32]},
                             ]},
                        ]},
                        {"type": "section", "title": "环形图", "children": [
                            {"type": "chart", "kind": "donut", "height": 220,
                             "data": [["已完成", 42], ["处理中", 18], ["待处理", 12]]},
                        ]},
                    ]},
                ],
            },
            "style": {
                "type": "page",
                "title": "界面风格",
                "subtitle": "两种外观来自两个同源组件库。切换风格会保存偏好并重启程序。",
                "children": [
                    {
                        "type": "alert",
                        "kind": "success" if style == "win11" else "info",
                        "title": f"正在使用：{info['label']}",
                        "message": f"{info['short']} · {info['library']}。{info['summary']}",
                    },
                    {
                        "type": "grid",
                        "columns": 2,
                        "gap": 14,
                        "children": [
                            {
                                "type": "card",
                                "selected": style == "web",
                                "children": [
                                    {"type": "heading", "title": "Web 应用风",
                                     "subtitle": "TkWebUI · 静态、克制、信息密度高"},
                                    {"type": "label", "text": "适合科研、工程与内部数据工具："
                                     "白底圆角、清晰表单，启动后样式固定，行为可预期。",
                                     "style": "muted", "wrap": 420},
                                    {"type": "row", "gap": 8, "children": [
                                        {"type": "button", "text": "切换到 Web",
                                         "variant": "primary" if style != "web" else "quiet",
                                         "enabled": style != "web",
                                         "command": "use_web"},
                                    ]},
                                ],
                            },
                            {
                                "type": "card",
                                "selected": style == "win11",
                                "children": [
                                    {"type": "heading", "title": "Windows 11 风",
                                     "subtitle": "TkWin11 · Fluent、动画、每屏 DPI"},
                                    {"type": "label", "text": "适合发给 Windows 用户的桌面程序："
                                     "Mica 工作区、一体化标题栏、悬停/按下/页面切换动画。",
                                     "style": "muted", "wrap": 420},
                                    {"type": "row", "gap": 8, "children": [
                                        {"type": "button", "text": "切换到 Win11",
                                         "variant": "primary" if style != "win11" else "quiet",
                                         "enabled": style != "win11",
                                         "command": "use_win11"},
                                    ]},
                                ],
                            },
                        ],
                    },
                    {
                        "type": "section",
                        "title": "偏好设置",
                        "children": [
                            {"type": "settings_row", "title": "下次启动",
                             "description": "选择会写入用户配置文件",
                             "children": [
                                 {"type": "segmented", "id": "preferred",
                                  "options": [{"value": "web", "label": "Web"},
                                              {"value": "win11", "label": "Win11"}],
                                  "value": style,
                                  "command": {"action": "style", "style": "$value"}},
                             ]},
                            {"type": "label", "text": f"配置文件：{theme_mod.config_path()}",
                             "style": "caption"},
                            {"type": "row", "children": [
                                {"type": "button", "text": "打开风格选择器",
                                 "variant": "quiet", "icon": "settings",
                                 "command": "choose_style"},
                            ]},
                        ],
                    },
                    {
                        "type": "section",
                        "title": "两个组件库怎么选",
                        "children": [
                            {"type": "label", "wrap": 900, "style": "muted",
                             "text": "TkWebUI：外观稳定、代码量小、无动画，重点是表格、图表与表单；"
                             "TkWin11：目标平台 Windows 11，多了 Fluent 控件、一体化标题栏、"
                             "多显示器 DPI 与过渡动画，代价是运行时代码更重。"},
                            {"type": "label", "wrap": 900, "style": "muted",
                             "text": "两者接口同源，因此 TkUI 只保留一套声明；"
                             "组件名、属性、布局和动作在两种风格下完全一致。"},
                        ],
                    },
                ],
            },
        },
    }


def run_demo(*, style=None, page=None, choose=False):
    from . import App, choose_style

    resolved = theme_mod.resolve_style(style)
    if choose or style == "ask":
        resolved = choose_style(default=resolved)
    spec = build_spec(resolved)
    holder = {}

    def app():
        return holder.get("app")

    def toast(event=None):
        app().notify("通知已到达。这个提示条由后端原生绘制。", title="TkUI",
                     kind="success")

    def dialog(event=None):
        app().dialog("这是一个原生模态对话框。\n两种风格的按钮与标题栏不同，调用一致。",
                     title="TkUI 对话框")

    def about(event=None):
        info = app().info()
        app().dialog(
            f"风格：{info['style_label']}\n后端：{info['backend']} {info['version']}\n"
            f"页面：{info['page']}\n已登记组件：{info['components']}",
            title="关于 TkUI")

    def save_form(event=None):
        fields = {
            "名称": app().get("name", ""),
            "级别": app().get("level", ""),
            "日期": app().get("due", ""),
            "备注": app().get("notes", ""),
        }
        summary = "，".join(f"{key}={value or '（空）'}" for key, value in fields.items())
        app().notify(summary, title="表单已保存", kind="success")

    def clear_form(event=None):
        for node_id in ("name", "password", "notes", "due"):
            try:
                app().set(node_id, "", silent=True)
            except Exception:
                pass
        app().notify("已清空表单", kind="info")

    def add_row(event=None):
        try:
            table = app().native("tasks_table")
            import random
            names = ["接口联调", "需求评审", "性能压测", "文案校对", "发布验收"]
            owners = ["小林", "阿澈", "Mia", "Ken"]
            table.insert_row([random.choice(names), random.choice(owners),
                              random.choice(["进行中", "待开始", "已完成"]), "11-05"])
            app().notify("已向数据表插入一行", kind="success")
        except Exception:
            app()._report_exception()

    def use_web(event=None):
        app().restart_in_style("web")

    def use_win11(event=None):
        app().restart_in_style("win11")

    def choose_again(event=None):
        choice = choose_style(default=resolved)
        if choice != resolved:
            app().restart_in_style(choice)

    actions = {
        "toast": toast,
        "dialog": dialog,
        "about": about,
        "save_form": save_form,
        "clear_form": clear_form,
        "add_row": add_row,
        "use_web": use_web,
        "use_win11": use_win11,
        "choose_style": choose_again,
    }
    application = App(spec, style=resolved, actions=actions, on_close=None)
    holder["app"] = application
    if page:
        application.navigate(page)
    application.run()
    return application


if __name__ == "__main__":
    run_demo()
