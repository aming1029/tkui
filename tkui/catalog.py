"""Style-neutral component catalog.

The catalog is the contract between an AI (or a human) and the renderer.  It
describes component names, props, events and how each component is mapped in
the two visual styles.  Nothing here imports tkinter or either theme library,
so it can be inspected without a display.
"""
from __future__ import annotations

import copy

SPEC_VERSION = 1

ICONS = (
    "plus", "search", "edit", "play", "check", "library", "sources", "settings",
    "controls", "folder", "download", "back", "speed", "pin", "chevronup",
    "chevrondown", "chevronright", "collapse", "expand", "info",
)

LAYOUT_FIELDS = {
    "side": {"kind": "enum", "values": ["top", "bottom", "left", "right"],
             "desc": "pack 方向"},
    "fill": {"kind": "enum", "values": ["x", "y", "both", "none"],
             "desc": "填充方向"},
    "expand": {"kind": "bool", "desc": "是否占用剩余空间"},
    "padx": {"kind": "int", "desc": "水平外边距（可写 [左, 右]）"},
    "pady": {"kind": "int", "desc": "垂直外边距（可写 [上, 下]）"},
    "ipadx": {"kind": "int", "desc": "水平内边距"},
    "ipady": {"kind": "int", "desc": "垂直内边距"},
    "anchor": {"kind": "enum", "values": ["n", "s", "e", "w", "center", "ne", "nw", "se", "sw"],
               "desc": "对齐点"},
    "row": {"kind": "int", "desc": "grid 行（grid 父容器内）"},
    "column": {"kind": "int", "desc": "grid 列（grid 父容器内）"},
    "rowspan": {"kind": "int", "desc": "grid 跨行"},
    "columnspan": {"kind": "int", "desc": "grid 跨列"},
    "sticky": {"kind": "str", "desc": "grid 拉伸，如 nsew"},
    "weightx": {"kind": "int", "desc": "grid 列权重"},
    "weighty": {"kind": "int", "desc": "grid 行权重"},
    "width": {"kind": "int", "desc": "固定宽度"},
    "height": {"kind": "int", "desc": "固定高度"},
}

COMMON_PROPS = {
    "id": {"kind": "str", "desc": "组件 id，用于 app['id'] / app.get('id')，必须唯一"},
    "variable": {"kind": "str", "desc": "共享 Tk 变量名；同名控件自动共享状态"},
    "tooltip": {"kind": "str", "desc": "悬停提示"},
    "enabled": {"kind": "bool", "default": True, "desc": "是否可用"},
}

EVENTS = {
    "click": "点击",
    "change": "值变化",
    "select": "选择变化（表格/图表/列表）",
    "activate": "双击/回车激活",
}


def _prop(kind, desc, default=..., values=None, required=False):
    item = {"kind": kind, "desc": desc}
    if default is not ...:
        item["default"] = default
    if values is not None:
        item["values"] = list(values)
    if required:
        item["required"] = True
    return item


def _node(name, category, summary, *, container=False, props=None, events=("click",),
          styles=("web", "win11"), fallback=None, example=None, layout=None,
          children=None, notes=None):
    return {
        "name": name,
        "category": category,
        "summary": summary,
        "container": container,
        "children": children,
        "props": props or {},
        "events": list(events),
        "styles": list(styles),
        "fallback": fallback,
        "default_layout": layout or {},
        "example": example or {"type": name},
        "notes": notes,
    }


def _options_prop():
    return _prop("list", "选项；字符串或 {value,label}，至少两项", required=True)


def _command_prop(desc="点击动作：动作名或内置动作对象"):
    return _prop("action", desc)


_ACTION = {"kind": "action", "desc": "动作名或内置动作对象"}

COMPONENTS = {
    # ---------------------------------------------------------------- layout
    "column": _node(
        "column", "布局", "纵向堆叠容器（默认填充 x）。", container=True,
        props={"gap": _prop("int", "子项间距", 8),
               "padding": _prop("int", "容器内边距", 0),
               "surface": _prop("enum", "背景面", "panel", ["panel", "workspace", "sidebar"])},
        events=(), example={"type": "column", "gap": 12, "children": []},
        children="任意非 tab 组件",
    ),
    "row": _node(
        "row", "布局", "横向排列容器，子项默认垂直填充。", container=True,
        props={"gap": _prop("int", "子项间距", 8),
               "padding": _prop("int", "容器内边距", 0),
               "align": _prop("enum", "子项对齐", "center", ["center", "start", "end", "stretch"]),
               "surface": _prop("enum", "背景面", "panel", ["panel", "workspace", "sidebar"])},
        events=(), example={"type": "row", "gap": 8, "children": []},
        children="任意非 tab 组件",
    ),
    "grid": _node(
        "grid", "布局", "网格容器；子项用 layout.row / layout.column 指定位置。", container=True,
        props={"gap": _prop("int", "子项间距", 8),
               "padding": _prop("int", "容器内边距", 0),
               "columns": _prop("int", "未指定位置时自动排列的列数", 2),
               "surface": _prop("enum", "背景面", "panel", ["panel", "workspace", "sidebar"])},
        events=(), example={"type": "grid", "columns": 2, "children": []},
        children="任意非 tab 组件",
    ),
    "spacer": _node(
        "spacer", "布局", "固定或弹性空白。", events=(),
        props={"size": _prop("int", "空白尺寸", 8),
               "expand": _prop("bool", "是否吸收剩余空间", False)},
        example={"type": "spacer", "size": 12},
    ),
    "separator": _node(
        "separator", "布局", "分隔线。", events=(),
        props={"orient": _prop("enum", "方向", "horizontal", ["horizontal", "vertical"])},
        example={"type": "separator"},
    ),
    "scroll": _node(
        "scroll", "布局", "可滚动区域，内容放在 body 中。", container=True,
        props={"height": _prop("int", "建议高度", 320),
               "gap": _prop("int", "子项间距", 10),
               "padding": _prop("int", "内容内边距", 0)},
        events=(), layout={"fill": "both", "expand": True},
        example={"type": "scroll", "height": 360, "children": []},
    ),
    "page": _node(
        "page", "布局", "页面：标题 + 可滚动内容。通常只出现在 pages 下。", container=True,
        props={"title": _prop("str", "页面标题"),
               "subtitle": _prop("str", "页面副标题"),
               "scroll": _prop("bool", "内容是否可滚动", True),
               "padding": _prop("int", "内容内边距", 24),
               "gap": _prop("int", "内容间距", 14)},
        events=(), layout={"fill": "both", "expand": True},
        example={"type": "page", "title": "概览", "children": []},
    ),
    # ------------------------------------------------------------- containers
    "card": _node(
        "card", "容器", "圆角卡片容器，可点击。", container=True,
        props={"selected": _prop("bool", "强调边框", False),
               "padding": _prop("int", "内边距", 16),
               "command": _command_prop("点击卡片时执行的动作")},
        children="任意非 tab 组件",
        example={"type": "card", "children": []},
    ),
    "section": _node(
        "section", "容器", "带标题的分组卡片。", container=True,
        props={"title": _prop("str", "分组标题"),
               "padding": _prop("int", "内边距", 14),
               "selected": _prop("bool", "强调边框", False)},
        children="任意非 tab 组件",
        example={"type": "section", "title": "基本设置", "children": []},
    ),
    "accordion": _node(
        "accordion", "容器", "可折叠分组。", container=True,
        props={"title": _prop("str", "标题", required=True),
               "opened": _prop("bool", "初始展开", False)},
        children="任意非 tab 组件",
        example={"type": "accordion", "title": "高级选项", "opened": True, "children": []},
    ),
    "tabs": _node(
        "tabs", "容器", "标签页容器，子项必须是 tab。", container=True,
        props={"padding": _prop("int", "标签内容内边距", 12)},
        events=(), children="tab",
        example={"type": "tabs", "children": [{"type": "tab", "title": "一", "children": []}]},
    ),
    "tab": _node(
        "tab", "容器", "tabs 的单个标签页。", container=True,
        props={"title": _prop("str", "标签标题", required=True),
               "padding": _prop("int", "内边距", 12)},
        events=(), children="任意非 tab 组件",
        example={"type": "tab", "title": "一", "children": []},
    ),
    "settings_row": _node(
        "settings_row", "容器", "设置行：左侧标题/说明，右侧放控件。", container=True,
        props={"title": _prop("str", "标题", required=True),
               "description": _prop("str", "说明"),
               "help": _prop("str", "问号提示文字")},
        events=(), children="通常放 switch / combo / button 等单个控件",
        example={"type": "settings_row", "title": "自动保存", "description": "退出时保存",
                 "children": [{"type": "switch", "label": ""}]},
    ),
    "settings_card": _node(
        "settings_card", "容器", "带图标的设置卡片（Win11 使用原生 SettingsCard，Web 使用等价布局）。",
        container=True,
        props={"title": _prop("str", "标题", required=True),
               "description": _prop("str", "说明"),
               "icon": _prop("enum", "左侧图标", "settings", ICONS),
               "command": _command_prop()},
        children="通常放 switch / combo / button 等单个控件",
        example={"type": "settings_card", "title": "自动保存", "icon": "download",
                 "children": [{"type": "switch", "label": ""}]},
    ),
    "expander": _node(
        "expander", "容器", "可展开卡片（Win11 原生动画，Web 退化为 Accordion）。", container=True,
        props={"title": _prop("str", "标题", required=True),
               "description": _prop("str", "说明"),
               "icon": _prop("enum", "图标", "settings", ICONS),
               "opened": _prop("bool", "初始展开", False)},
        styles=("win11",), fallback="accordion",
        children="任意非 tab 组件",
        example={"type": "expander", "title": "更多设置", "children": []},
    ),
    # ------------------------------------------------------------- typography
    "label": _node(
        "label", "文本", "文本标签。", events=(),
        props={"text": _prop("str", "文本", ""),
               "style": _prop("enum", "排版", "body",
                              ["body", "muted", "strong", "title", "subtitle", "caption"]),
               "wrap": _prop("int", "换行宽度（像素，0 表示不换行）", 0),
               "justify": _prop("enum", "多行对齐", "left", ["left", "center", "right"]),
               "anchor": _prop("enum", "单行对齐", "w", ["w", "center", "e"]),
               "icon": _prop("enum", "行内图标", None, ICONS)},
        example={"type": "label", "text": "说明文字", "style": "muted"},
    ),
    "heading": _node(
        "heading", "文本", "标题 + 副标题块。", events=(),
        props={"title": _prop("str", "标题", required=True),
               "subtitle": _prop("str", "副标题"),
               "level": _prop("int", "1 为页面标题，2 为区块标题", 2),
               "align": _prop("enum", "对齐", "w", ["w", "center", "e"])},
        example={"type": "heading", "title": "数据概览", "subtitle": "最近 7 天"},
    ),
    # ---------------------------------------------------------------- inputs
    "button": _node(
        "button", "输入", "按钮。",
        props={"text": _prop("str", "按钮文字", ""),
               "variant": _prop("enum", "视觉变体", "secondary",
                                ["primary", "secondary", "quiet", "link", "danger", "success", "toggle", "tool"]),
               "icon": _prop("enum", "图标", None, ICONS),
               "command": _command_prop(),
               "width": _prop("int", "字符宽度")},
        example={"type": "button", "text": "保存", "variant": "primary", "command": "save"},
    ),
    "entry": _node(
        "entry", "输入", "单行输入框，可带校验。",
        props={"value": _prop("str", "初始值", ""),
               "placeholder": _prop("str", "占位提示"),
               "kind": _prop("enum", "校验类型", "text",
                             ["text", "password", "integer", "float", "email", "date"]),
               "label": _prop("str", "上方标签"),
               "required": _prop("bool", "必填", False),
               "min": _prop("float", "数值下限"),
               "max": _prop("float", "数值上限"),
               "width": _prop("int", "字符宽度"),
               "command": _command_prop("内容变化时执行")},
        events=("change",),
        example={"type": "entry", "id": "name", "placeholder": "请输入名称", "label": "名称"},
    ),
    "text": _node(
        "text", "输入", "多行文本框。",
        props={"value": _prop("str", "初始文本", ""),
               "height": _prop("int", "行数", 5),
               "readonly": _prop("bool", "只读", False),
               "wrap": _prop("enum", "换行方式", "word", ["word", "char", "none"]),
               "command": _command_prop("内容变化时执行")},
        events=("change",),
        example={"type": "text", "height": 6, "placeholder": "备注"},
    ),
    "combo": _node(
        "combo", "输入", "下拉选择框（可编辑或只读）。",
        props={"values": _prop("list", "选项", [], required=True),
               "value": _prop("str", "初始值", ""),
               "readonly": _prop("bool", "只读选择", True),
               "placeholder": _prop("str", "占位提示"),
               "width": _prop("int", "字符宽度"),
               "command": _command_prop("选择变化时执行")},
        events=("change",),
        example={"type": "combo", "values": ["低", "中", "高"], "value": "中", "command": "priority"},
    ),
    "dropdown": _node(
        "dropdown", "输入", "带自定义浮层的下拉框。",
        props={"values": _prop("list", "选项", [], required=True),
               "value": _prop("str", "初始值", ""),
               "placeholder": _prop("str", "占位提示"),
               "command": _command_prop("选择变化时执行")},
        events=("change",),
        example={"type": "dropdown", "values": ["A", "B"], "command": "pick"},
    ),
    "spinbox": _node(
        "spinbox", "输入", "数值微调框。",
        props={"value": _prop("float", "初始值", 0),
               "min": _prop("float", "最小值", 0),
               "max": _prop("float", "最大值", 100),
               "step": _prop("float", "步长", 1),
               "width": _prop("int", "字符宽度", 8),
               "command": _command_prop("值变化时执行")},
        events=("change",),
        example={"type": "spinbox", "min": 1, "max": 12, "value": 3},
    ),
    "checkbox": _node(
        "checkbox", "输入", "复选按钮。",
        props={"text": _prop("str", "文字", ""),
               "value": _prop("bool", "是否勾选", False),
               "command": _command_prop("状态变化时执行")},
        events=("change",),
        example={"type": "checkbox", "text": "记住选择", "value": True},
    ),
    "radio_group": _node(
        "radio_group", "输入", "一组单选按钮。",
        props={"options": _options_prop(),
               "value": _prop("str", "当前值"),
               "orientation": _prop("enum", "排列方向", "horizontal", ["horizontal", "vertical"]),
               "command": _command_prop("选择变化时执行")},
        events=("change",),
        example={"type": "radio_group", "options": ["小", "中", "大"], "value": "中"},
    ),
    "switch": _node(
        "switch", "输入", "滑动开关。",
        props={"label": _prop("str", "左侧标签", ""),
               "value": _prop("bool", "初始状态", False),
               "command": _command_prop("状态变化时执行")},
        events=("change",),
        example={"type": "switch", "label": "自动同步", "value": True},
    ),
    "segmented": _node(
        "segmented", "输入", "分段选择器。",
        props={"options": _options_prop(),
               "value": _prop("str", "当前值"),
               "command": _command_prop("选择变化时执行")},
        events=("change",),
        example={"type": "segmented", "options": ["日", "周", "月"], "value": "日"},
    ),
    "slider": _node(
        "slider", "输入", "带数值框的滑块。",
        props={"value": _prop("float", "当前值", 0),
               "min": _prop("float", "最小值", 0),
               "max": _prop("float", "最大值", 100),
               "step": _prop("float", "步长", 1),
               "unit": _prop("str", "单位", ""),
               "command": _command_prop("值变化时执行")},
        events=("change",),
        example={"type": "slider", "min": 0, "max": 10, "value": 4, "unit": "级"},
    ),
    "date": _node(
        "date", "输入", "日期选择框。",
        props={"value": _prop("str", "初始日期 YYYY-MM-DD"),
               "min": _prop("str", "最早日期"),
               "max": _prop("str", "最晚日期"),
               "command": _command_prop("日期变化时执行")},
        events=("change",),
        example={"type": "date", "value": "2026-10-30"},
    ),
    "keychord": _node(
        "keychord", "输入", "快捷键徽章（Win11 可编辑，Web 退化为只读输入框）。",
        props={"value": _prop("str", "组合键", "Ctrl+S"),
               "command": _command_prop("修改后执行")},
        styles=("win11",), fallback="readonly entry",
        example={"type": "keychord", "value": "Alt+Shift+A"},
    ),
    "color": _node(
        "color", "输入", "颜色选择器。",
        props={"value": _prop("str", "颜色 #RRGGBB", "#087DFF"),
               "command": _command_prop("颜色变化时执行")},
        events=("change",), example={"type": "color"},
    ),
    "font": _node(
        "font", "输入", "字体选择器。",
        props={"value": _prop("str", "字体名", "TkDefaultFont")},
        events=("change",), example={"type": "font"},
    ),
    # ---------------------------------------------------------------- display
    "progress": _node(
        "progress", "显示", "带文字进度条。",
        props={"value": _prop("float", "当前值", 0),
               "max": _prop("float", "最大值", 100),
               "text": _prop("str", "前缀文字"),
               "mode": _prop("enum", "模式", "determinate", ["determinate", "indeterminate"]),
               "kind": _prop("enum", "语义色", "primary",
                             ["primary", "success", "warning", "danger", "info"]),
               "orient": _prop("enum", "方向", "horizontal", ["horizontal", "vertical"]),
               "length": _prop("int", "长度", 240),
               "thickness": _prop("int", "粗细", 28)},
        events=(), example={"type": "progress", "value": 62, "text": "构建"},
    ),
    "meter": _node(
        "meter", "显示", "圆形/半圆仪表。",
        props={"value": _prop("float", "当前值", 0),
               "min": _prop("float", "最小值", 0),
               "max": _prop("float", "最大值", 100),
               "shape": _prop("enum", "形状", "full", ["full", "semi"]),
               "unit": _prop("str", "单位", "%"),
               "subtext": _prop("str", "副文字"),
               "interactive": _prop("bool", "可拖动", False),
               "size": _prop("int", "尺寸", 190),
               "command": _command_prop("值变化时执行")},
        events=("change",), example={"type": "meter", "value": 72, "subtext": "健康度"},
    ),
    "badge": _node(
        "badge", "显示", "语义色小徽章。", events=(),
        props={"text": _prop("str", "文字", ""),
               "kind": _prop("enum", "语义", "info",
                             ["info", "success", "warning", "danger", "neutral"])},
        example={"type": "badge", "text": "已完成", "kind": "success"},
    ),
    "stat": _node(
        "stat", "显示", "指标卡：标签、大数字、变化量。", events=(),
        props={"label": _prop("str", "指标名", required=True),
               "value": _prop("str", "指标值", required=True),
               "suffix": _prop("str", "单位后缀"),
               "delta": _prop("str", "变化量文字，如 +12%"),
               "kind": _prop("enum", "变化量语义", "info",
                             ["info", "success", "warning", "danger", "neutral"]),
               "icon": _prop("enum", "图标", None, ICONS)},
        example={"type": "stat", "label": "今日访问", "value": "12,480", "delta": "+8.2%",
                 "kind": "success"},
    ),
    "alert": _node(
        "alert", "显示", "内联提示条。", events=(),
        props={"message": _prop("str", "正文", required=True),
               "title": _prop("str", "标题"),
               "kind": _prop("enum", "语义", "info",
                             ["info", "success", "warning", "danger", "neutral"])},
        example={"type": "alert", "title": "注意", "message": "数据尚未保存", "kind": "warning"},
    ),
    "image": _node(
        "image", "显示", "图片查看器（PNG/GIF/PPM 原生，其他格式需 Pillow）。", events=(),
        props={"path": _prop("str", "图片路径"),
               "height": _prop("int", "初始高度", 300)},
        example={"type": "image", "height": 260},
    ),
    # ------------------------------------------------------------------ data
    "table": _node(
        "table", "数据", "搜索、筛选、分页、导出 CSV 的数据表。",
        props={"columns": _prop("list", "列：字符串或 {key,text,width}", required=True),
               "rows": _prop("list", "行数据：字典或列表", []),
               "page_size": _prop("int", "每页行数", 10),
               "height": _prop("int", "可见行数", 8),
               "command": _command_prop("双击行时执行")},
        events=("activate", "select"), layout={"fill": "both", "expand": True},
        example={"type": "table", "columns": ["名称", "数量"],
                 "rows": [["资料 A", 12], ["资料 B", 7]]},
    ),
    "list": _node(
        "list", "数据", "单列列表框。",
        props={"items": _prop("list", "条目", [], required=True),
               "value": _prop("int", "选中索引", -1),
               "selectmode": _prop("enum", "选择模式", "browse",
                                   ["browse", "single", "multiple", "extended"]),
               "height": _prop("int", "可见行数", 8),
               "command": _command_prop("选择变化时执行")},
        events=("change", "select"), layout={"fill": "both", "expand": True},
        example={"type": "list", "items": ["苹果", "香蕉", "橙子"], "value": 0},
    ),
    "tree": _node(
        "tree", "数据", "可排序多列表格。",
        props={"columns": _prop("list", "列", required=True),
               "rows": _prop("list", "行", []),
               "height": _prop("int", "可见行数", 8),
               "command": _command_prop("双击行时执行")},
        events=("activate", "select"), layout={"fill": "both", "expand": True},
        example={"type": "tree", "columns": ["名称", "数量"],
                 "rows": [["A", 3], ["B", 5]]},
    ),
    "spreadsheet": _node(
        "spreadsheet", "数据", "Excel 式单元格表格，支持多选、复制粘贴、撤销。",
        props={"data": _prop("list", "二维数据", []),
               "rows": _prop("int", "行数", 30),
               "columns": _prop("int", "列数", 8),
               "column_width": _prop("int", "列宽", 122),
               "row_height": _prop("int", "行高", 30),
               "command": _command_prop("内容变化时执行")},
        events=("change",), layout={"fill": "both", "expand": True},
        example={"type": "spreadsheet", "data": [["项目", "数量"], ["资料整理", "12"]]},
    ),
    "chart": _node(
        "chart", "数据", "原生交互图表（折线/柱状/散点/饼/环）。",
        props={"kind": _prop("enum", "类型", "line", ["line", "column", "scatter", "donut", "pie"]),
               "values": _prop("list", "单系列数值"),
               "labels": _prop("list", "横轴/分类标签"),
               "series": _prop("list", "多系列：[{name,values/points,color}]"),
               "data": _prop("list", "饼/环数据：[[名称,数值]] 或 [{name,value}]"),
               "height": _prop("int", "高度", 240),
               "command": _command_prop("点击数据时执行，事件 value 为数据点")},
        events=("select", "click"), layout={"fill": "both", "expand": True},
        example={"type": "chart", "kind": "line", "values": [12, 18, 14, 26],
                 "labels": ["一", "二", "三", "四"]},
    ),
}

ALIASES = {
    "stack": "column",
    "vstack": "column",
    "frame": "column",
    "hstack": "row",
    "toolbar": "row",
    "divider": "separator",
    "listbox": "list",
    "combobox": "combo",
    "select": "combo",
    "text_input": "entry",
    "input": "entry",
    "textarea": "text",
    "radio": "radio_group",
    "switch_group": "radio_group",
    "figure": "chart",
    "datatable": "table",
    "data_table": "table",
    "grid_table": "tree",
}

CATEGORIES = ("布局", "容器", "文本", "输入", "显示", "数据")


def canonical_type(name) -> str:
    return ALIASES.get(str(name), str(name))


def component(name):
    return COMPONENTS.get(canonical_type(name))


def component_names(*, include_aliases: bool = False):
    names = list(COMPONENTS)
    if include_aliases:
        names.extend(ALIASES)
    return names


def catalog() -> dict:
    return {
        "format": "tkui-spec",
        "schema_version": SPEC_VERSION,
        "styles": {
            "web": "现代 Web 应用风（TkWebUI）",
            "win11": "Windows 11 Fluent（TkWin11）",
        },
        "icons": list(ICONS),
        "aliases": dict(ALIASES),
        "common_props": copy.deepcopy(COMMON_PROPS),
        "layout_fields": copy.deepcopy(LAYOUT_FIELDS),
        "events": dict(EVENTS),
        "components": copy.deepcopy(COMPONENTS),
    }


def _fmt_props(props):
    if not props:
        return ""
    parts = []
    for name, info in props.items():
        kind = info["kind"]
        if kind == "enum":
            kind = "|".join(info.get("values", []))
        default = info.get("default", "—")
        parts.append(f"`{name}`:{kind}={default}")
    return ", ".join(parts)


def to_markdown() -> str:
    lines = [
        "# TkUI 组件目录",
        "",
        f"规格版本：{SPEC_VERSION}。所有组件都只有一份风格无关的声明；`web` / `win11` 的差异由渲染器处理。",
        "",
        "## 布局字段",
        "",
        "任何组件都可以带 `layout`：",
        "",
        "| 字段 | 类型 | 说明 |",
        "| --- | --- | --- |",
    ]
    for name, info in LAYOUT_FIELDS.items():
        kind = info["kind"]
        if kind == "enum":
            kind = " / ".join(info["values"])
        lines.append(f"| `{name}` | {kind} | {info['desc']} |")
    lines += ["", "## 组件", ""]
    for category in CATEGORIES:
        lines += [f"### {category}", ""]
        for name, item in COMPONENTS.items():
            if item["category"] != category:
                continue
            lines.append(f"#### `{name}`")
            lines.append("")
            style = " · ".join(item["styles"])
            suffix = f"（仅 {style}，Web 回退：{item['fallback']}）" if item["fallback"] else ""
            lines.append(f"{item['summary']}{suffix}")
            lines.append("")
            if item["container"]:
                lines.append(f"容器：是；子项：{item['children'] or '任意组件'}。")
                lines.append("")
            if item["props"]:
                lines.append("属性：" + _fmt_props(item["props"]))
                lines.append("")
            if item["events"]:
                lines.append("事件：" + ", ".join(f"`{e}`" for e in item["events"]))
                lines.append("")
            lines.append("```json")
            import json
            lines.append(json.dumps(item["example"], ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")
    return "\n".join(lines)
