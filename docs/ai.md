# 让 AI 使用 TkUI

TkUI 的设计目标：**AI 只写一份 JSON 规格，就能在两种 Tk 外观下运行**。本文是给
模型和给“给模型写提示词的人”的操作手册。

## 最短提示

把下面这段和 `AI_PROMPT.md` 一起给模型：

```text
你是 TkUI 的界面生成器。请只输出一个 TkUI JSON 规格（不要 Tk 代码）。
先阅读 AI_PROMPT.md 的组件目录与规则。用 id 标记需要读写的控件，
用 command / on 接动作，用 layout 控制排布。不要写颜色、字体或
web/win11 分支。生成后运行 `python -m tkui check app.json` 自检。
```

## 工作流

```bash
python -m tkui prompt -o AI_PROMPT.md       # 1. 生成/更新提示词
python -m tkui catalog                      # 2. 查看机器可读目录
python -m tkui check app.json --json        # 3. 校验（含动作名列表）
python -m tkui run app.json --style web     # 4. 预览 Web
python -m tkui run app.json --style win11   # 5. 预览 Win11
```

给模型的结果应当是**可直接保存的 JSON**，而不是解释性 Markdown。需要交互逻辑时，
再让它写一个小 Python 文件：

```python
import tkui

def on_save(event):
    event.app.notify("已保存", kind="success")

app = tkui.App("app.json", actions={"save": on_save})
app.run()
```

## 输出契约

模型输出必须满足：

1. 顶层是对象，`version: 1`；
2. 有 `body` 或 `pages`；
3. 每个节点有 `type`；
4. 只在容器上用 `children`；
5. `id` 唯一；
6. 枚举值来自目录；
7. 动作只能是字符串、内置动作对象或它们的列表；
8. 不出现 Tk 控件名、颜色、像素间距、字体或 web/win11 分支。

## 选择页面结构

| 用户意图 | 结构 |
| --- | --- |
| 单个工具/表单 | `body` + `column` |
| 多功能桌面工具 | `nav.mode: sidebar` + `pages` |
| 轻量多视图 | `nav.mode: segmented` + `pages` |
| 仪表盘 | `pages` + `row` 的 `stat` + `grid` 的 `section` |
| 设置面板 | `settings_row` / `settings_card` / `expander` |
| 数据管理 | `table` + `tree` / `spreadsheet` + 表单 |

## 风格无关规则

- 用 `variant="primary"`，不要写 `style="Primary.TButton"`；
- 用 `kind="success"`，不要写绿色；
- 用 `layout.fill/expand`，不要写像素宽度；
- 用 `section` / `card` / `settings_row` 组织信息；
- 只给需要读取或联动的控件加 `id`；
- 需要两种风格都好看时，不要依赖某个库独有的外观细节。

## 动作

### 优先用内置动作交付可运行原型

```json
{"type": "button", "text": "保存",
 "command": {"action": "notify", "message": "已保存", "kind": "success"}}
```

```json
{"type": "button", "text": "打开设置",
 "command": {"action": "navigate", "page": "settings"}}
```

```json
{"type": "switch", "id": "auto", "value": true,
 "on": {"change": {"action": "set", "target": "status", "value": "$value"}}}
```

### 需要业务逻辑时用动作名

规格：

```json
{"type": "button", "text": "保存", "command": "save"}
```

Python：

```python
def on_save(event):
    name = event.app.get("name")
    ...

app = tkui.App(spec, actions={"save": on_save})
```

`event.value` 对输入控件是当前值；对表格 `activate` 是行字典；对图表是数据点。

## 常用配方

### 1. 仪表盘

```json
{
  "type": "page",
  "title": "概览",
  "children": [
    {"type": "row", "gap": 12, "children": [
      {"type": "stat", "label": "进行中", "value": "8", "delta": "+2",
       "layout": {"fill": "both", "expand": true}},
      {"type": "stat", "label": "已完成", "value": "24", "delta": "+12%",
       "kind": "success", "layout": {"fill": "both", "expand": true}}
    ]},
    {"type": "grid", "columns": 2, "gap": 14, "children": [
      {"type": "section", "title": "趋势", "children": [
        {"type": "chart", "kind": "line", "values": [12, 18, 14, 26],
         "labels": ["一", "二", "三", "四"]}
      ]},
      {"type": "section", "title": "风险", "children": [
        {"type": "alert", "kind": "warning", "message": "2 个任务延期"}
      ]}
    ]}
  ]
}
```

### 2. 表单

```json
{
  "type": "section",
  "title": "新建任务",
  "children": [
    {"type": "entry", "id": "name", "label": "名称", "required": true,
     "placeholder": "例如：发布检查"},
    {"type": "combo", "id": "owner", "values": ["小林", "Mia"], "value": "小林"},
    {"type": "date", "id": "due", "value": "2026-11-05"},
    {"type": "text", "id": "notes", "height": 4},
    {"type": "row", "children": [
      {"type": "button", "text": "创建", "variant": "primary", "command": "create"},
      {"type": "button", "text": "取消", "variant": "quiet", "command": "cancel"}
    ]}
  ]
}
```

### 3. 数据表 + 操作

```json
{
  "type": "page",
  "title": "任务",
  "children": [
    {"type": "row", "children": [
      {"type": "button", "text": "新建", "variant": "primary", "icon": "plus",
       "command": "create"},
      {"type": "spacer", "expand": true},
      {"type": "badge", "text": "4 条", "kind": "info"}
    ]},
    {"type": "table", "id": "tasks",
     "columns": [{"key": "name", "text": "任务", "width": 260},
                 {"key": "owner", "text": "负责人", "width": 120},
                 {"key": "status", "text": "状态", "width": 100}],
     "rows": [["支付联调", "小林", "进行中"]],
     "page_size": 10}
  ]
}
```

Python：

```python
def create(event):
    event.app.native("tasks").insert_row(["新任务", "Mia", "待开始"])
```

### 4. 设置面板

```json
{"type": "settings_card", "title": "自动保存", "description": "退出时保存",
 "icon": "download",
 "children": [{"type": "switch", "id": "autosave", "value": true}]}
```

```json
{"type": "settings_row", "title": "主题", "description": "切换后重启",
 "children": [{"type": "segmented", "id": "look",
               "options": [{"value": "web", "label": "Web"},
                           {"value": "win11", "label": "Win11"}],
               "command": {"action": "style", "style": "$value"}}]}
```

### 5. 让用户选风格

```python
import tkui
style = tkui.choose_style()
tkui.run("app.json", style=style)
```

或在界面里：

```json
{"type": "row", "children": [
  {"type": "button", "text": "Web 风格",
   "command": {"action": "style", "style": "web"}},
  {"type": "button", "text": "Windows 11 风格",
   "command": {"action": "style", "style": "win11"}}
]}
```

## 校验与修复

`check --json` 返回：

```json
{
  "ok": false,
  "issues": [
    {"path": "$.body.children[0].type", "level": "error",
     "message": "未知组件 'buton'，是否想写 'button'？"}
  ],
  "actions": ["save"]
}
```

修复顺序：

1. 先修 `error`，再考虑 `warning`；
2. 按 `path` 定位，不要整页重写；
3. `actions` 是规格引用的 Python 动作，确保 `actions={}` 提供了同名函数；
4. 修完再次运行 `check`，直到 `ok: true`。

## 反模式

| 不要 | 原因 |
| --- | --- |
| `{"type": "Button"}` | 组件名小写，且必须是目录中的名字 |
| 在节点里写 `bg: "#fff"` | 会破坏两种风格的一致性 |
| 用 `width`/`height` 硬塞布局 | 用 `layout.fill/expand` 和 `grid` 权重 |
| 把所有控件塞进一个 `column` | 用 `section`/`card`/`settings_row` 分组 |
| 给所有控件都加 `id` | 只给需要读写的控件加 |
| 在规格里写 Python 表达式 | 动作对象只接受内置动作；逻辑写在 `actions` |
| 同一进程里先建 web 再建 win11 | 上游不允许混用；必须重启 |

## 安全边界

- 规格只是数据：TkUI 不会执行规格中的任意代码或文件路径；
- 只有宿主程序提供的 `actions` 才能访问业务逻辑、文件或网络；
- `image.path` 只读取用户显式给出的图片文件；
- 纯 JSON 运行器只启用内置动作（通知、页面切换、设值等）。

## 给编码 Agent 的扩展指南

添加一个新组件需要同步四处：

1. `tkui/catalog.py`：名称、类别、属性、事件、示例、默认布局；
2. `tkui/renderer.py`：渲染函数，并注册到 `_RENDERERS`；
3. `tkui/spec.py`：通常无需改；校验会从目录自动生效；
4. `tests/_render_all.py`：加入规格并用两种风格各跑一次。

然后：

```bash
python -m unittest discover -s tests -v
python -m tkui schema -o schema/tkui-1.json
python -m tkui catalog --markdown > docs/components.md
python -m tkui prompt -o AI_PROMPT.md
```

不要修改 `tkwebui-main/` 与 `tkwin11-main/`；它们作为上游只读依赖保留。
