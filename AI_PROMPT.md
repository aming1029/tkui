# 给 AI 的 TkUI 使用说明

你是 TkUI 的使用者。TkUI 把 TkWebUI（现代 Web 风）和 TkWin11（Windows 11 Fluent 风）
统一成一套**风格无关**的组件树。你只需要输出一份 JSON 规格，同一份规格可以在两种
外观下运行。不要在规格里写 Tk 代码、字体、像素级颜色或针对某个库的分支。

## 工作流

1. 阅读本说明和下面的组件目录。
2. 只输出一个 JSON 对象（或写入 `app.json`）。
3. 校验：`python -m tkui check app.json`
4. 预览：`python -m tkui run app.json --style web`
5. 换外观：`python -m tkui run app.json --style win11`
6. 需要业务逻辑时，把动作名交给 Python：

```python
import tkui

def on_save(event):
    print("saved", event.value)

app = tkui.App("app.json", actions={"save": on_save})
app.run()
```

回调可以写成 `def fn():`（无参数）或 `def fn(event):`。`event` 有 `name`、
`value`、`id`、`widget`、`app` 属性。

## 规格结构

```json
{
  "version": 1,
  "title": "窗口标题",
  "window": {"size": [1120, 760], "min_size": [900, 600],
             "centered": true, "resizable": true, "chrome": "native"},
  "theme": {"accent": "#0067C0"},
  "nav": {"mode": "sidebar", "selected": "home",
          "items": [{"key": "home", "label": "首页", "icon": "speed"}]},
  "pages": {
    "home": {"type": "page", "title": "首页", "subtitle": "说明",
             "children": [{"type": "label", "text": "你好"}]}
  }
}
```

- 只有一页时用 `body` 代替 `pages`。
- `nav.mode` 可选 `sidebar` / `segmented` / `none`。
- 每个节点：`type` 必填；`id` 可选但建议给需要读取的控件；`layout` 控制排布；
  其余键是该组件的属性；容器用 `children`。
- `pages` 下的页面可省略 `type`（默认 page），只需 `title` 和 `children`。

## 布局

父容器默认纵向排列；`row` 横向；`grid` 用子项的 `layout.row/column` 定位。
`layout` 可用字段：

- `side` (enum): pack 方向
- `fill` (enum): 填充方向
- `expand` (bool): 是否占用剩余空间
- `padx` (int): 水平外边距（可写 [左, 右]）
- `pady` (int): 垂直外边距（可写 [上, 下]）
- `ipadx` (int): 水平内边距
- `ipady` (int): 垂直内边距
- `anchor` (enum): 对齐点
- `row` (int): grid 行（grid 父容器内）
- `column` (int): grid 列（grid 父容器内）
- `rowspan` (int): grid 跨行
- `columnspan` (int): grid 跨列
- `sticky` (str): grid 拉伸，如 nsew
- `weightx` (int): grid 列权重
- `weighty` (int): grid 行权重
- `width` (int): 固定宽度
- `height` (int): 固定高度

- 固定宽度/高度用组件的 `width` / `height` 属性；不要用像素硬编码。
- 需要占满剩余空间时写 `"layout": {"fill": "both", "expand": true}`。
- `spacer` + `"expand": true` 可把后面的控件推到右侧/底部。
- 表格、图表、滚动区默认就会填满，不必重复写。

## 动作

`command` 和 `on` 里可以写：

1. **动作名字符串**：`"command": "save"`，由 Python 的 `actions={"save": fn}` 提供。
2. **内置动作对象**（纯 JSON 也能运行）：

```json
{"action": "notify", "message": "已保存", "kind": "success"}
{"action": "navigate", "page": "settings"}
{"action": "set", "target": "name", "value": "新值"}
{"action": "toggle", "target": "autosave"}
{"action": "dialog", "message": "确认吗？", "title": "提示"}
{"action": "style", "style": "win11"}
{"action": "chain", "chain": [{"action": "notify", "message": "完成"}]}
```

3. **动作列表**：按顺序执行。

事件键：`click`（按钮/卡片）、`change`（输入控件）、`select`（列表/表格/图表）、
`activate`（双击行）。

## 变量

- 给控件 `"id": "name"` 后，`app.get("name")` / `app.set("name", value)`。
- 多个控件共享 `"variable": "shared"` 即共享状态（例如单选组）。
- 输入控件的 `command` / `on.change` 会在值变化时执行。

## 组件目录

`属性!` 表示必填；`{a|b}` 表示枚举。

- column [容器] (布局): gap, padding, surface={panel|workspace|sidebar}
- row [容器] (布局): gap, padding, align={center|start|end|stretch}, surface={panel|workspace|sidebar}
- grid [容器] (布局): gap, padding, columns, surface={panel|workspace|sidebar}
- spacer (布局): size, expand
- separator (布局): orient={horizontal|vertical}
- scroll [容器] (布局): height, gap, padding
- page [容器] (布局): title, subtitle, scroll, padding, gap
- card [容器] (容器): selected, padding, command 事件:click
- section [容器] (容器): title, padding, selected 事件:click
- accordion [容器] (容器): title!, opened 事件:click
- tabs [容器] (容器): padding
- tab [容器] (容器): title!, padding
- settings_row [容器] (容器): title!, description, help
- settings_card [容器] (容器): title!, description, icon={plus|search|edit|play|check|library|sources|settings|controls|folder|download|back|speed|pin|chevronup|chevrondown|chevronright|collapse|expand|info}, command 事件:click
- expander [容器/仅win11] (容器): title!, description, icon={plus|search|edit|play|check|library|sources|settings|controls|folder|download|back|speed|pin|chevronup|chevrondown|chevronright|collapse|expand|info}, opened 事件:click
- label (文本): text, style={body|muted|strong|title|subtitle|caption}, wrap, justify={left|center|right}, anchor={w|center|e}, icon={plus|search|edit|play|check|library|sources|settings|controls|folder|download|back|speed|pin|chevronup|chevrondown|chevronright|collapse|expand|info}
- heading (文本): title!, subtitle, level, align={w|center|e}
- button (输入): text, variant={primary|secondary|quiet|link|danger|success|toggle|tool}, icon={plus|search|edit|play|check|library|sources|settings|controls|folder|download|back|speed|pin|chevronup|chevrondown|chevronright|collapse|expand|info}, command, width 事件:click
- entry (输入): value, placeholder, kind={text|password|integer|float|email|date}, label, required, min, max, width, command 事件:change
- text (输入): value, height, readonly, wrap={word|char|none}, command 事件:change
- combo (输入): values!, value, readonly, placeholder, width, command 事件:change
- dropdown (输入): values!, value, placeholder, command 事件:change
- spinbox (输入): value, min, max, step, width, command 事件:change
- checkbox (输入): text, value, command 事件:change
- radio_group (输入): options!, value, orientation={horizontal|vertical}, command 事件:change
- switch (输入): label, value, command 事件:change
- segmented (输入): options!, value, command 事件:change
- slider (输入): value, min, max, step, unit, command 事件:change
- date (输入): value, min, max, command 事件:change
- keychord [仅win11] (输入): value, command 事件:click
- color (输入): value, command 事件:change
- font (输入): value 事件:change
- progress (显示): value, max, text, mode={determinate|indeterminate}, kind={primary|success|warning|danger|info}, orient={horizontal|vertical}, length, thickness
- meter (显示): value, min, max, shape={full|semi}, unit, subtext, interactive, size, command 事件:change
- badge (显示): text, kind={info|success|warning|danger|neutral}
- stat (显示): label!, value!, suffix, delta, kind={info|success|warning|danger|neutral}, icon={plus|search|edit|play|check|library|sources|settings|controls|folder|download|back|speed|pin|chevronup|chevrondown|chevronright|collapse|expand|info}
- alert (显示): message!, title, kind={info|success|warning|danger|neutral}
- image (显示): path, height
- table (数据): columns!, rows, page_size, height, command 事件:activate/select
- list (数据): items!, value, selectmode={browse|single|multiple|extended}, height, command 事件:change/select
- tree (数据): columns!, rows, height, command 事件:activate/select
- spreadsheet (数据): data, rows, columns, column_width, row_height, command 事件:change
- chart (数据): kind={line|column|scatter|donut|pie}, values, labels, series, data, height, command 事件:select/click

图标可用：plus, search, edit, play, check, library, sources, settings, controls, folder, download, back, speed, pin, chevronup, chevrondown, chevronright, collapse, expand, info。

## 完整示例

```json
{
  "version": 1,
  "title": "项目脉搏",
  "window": {
    "size": [
      1120,
      760
    ],
    "min_size": [
      900,
      600
    ],
    "centered": true
  },
  "nav": {
    "mode": "sidebar",
    "selected": "overview",
    "items": [
      {
        "key": "overview",
        "label": "概览",
        "icon": "speed"
      },
      {
        "key": "tasks",
        "label": "任务",
        "icon": "library"
      },
      {
        "key": "settings",
        "label": "设置",
        "icon": "settings"
      }
    ]
  },
  "pages": {
    "overview": {
      "type": "page",
      "title": "项目概览",
      "subtitle": "最近 7 天的进展与风险",
      "children": [
        {
          "type": "row",
          "gap": 12,
          "children": [
            {
              "type": "stat",
              "label": "进行中",
              "value": "8",
              "delta": "+2",
              "kind": "info",
              "icon": "controls",
              "layout": {
                "fill": "both",
                "expand": true
              }
            },
            {
              "type": "stat",
              "label": "已完成",
              "value": "24",
              "delta": "+12%",
              "kind": "success",
              "icon": "check",
              "layout": {
                "fill": "both",
                "expand": true
              }
            },
            {
              "type": "stat",
              "label": "风险项",
              "value": "3",
              "delta": "-1",
              "kind": "warning",
              "icon": "info",
              "layout": {
                "fill": "both",
                "expand": true
              }
            }
          ]
        },
        {
          "type": "grid",
          "columns": 2,
          "gap": 14,
          "children": [
            {
              "type": "section",
              "title": "本周提交",
              "children": [
                {
                  "type": "chart",
                  "kind": "column",
                  "values": [
                    12,
                    18,
                    9,
                    22,
                    17,
                    26,
                    14
                  ],
                  "labels": [
                    "一",
                    "二",
                    "三",
                    "四",
                    "五",
                    "六",
                    "日"
                  ]
                }
              ]
            },
            {
              "type": "section",
              "title": "健康度",
              "children": [
                {
                  "type": "meter",
                  "value": 76,
                  "subtext": "团队负载",
                  "layout": {
                    "fill": "none"
                  }
                },
                {
                  "type": "progress",
                  "value": 68,
                  "text": "里程碑"
                },
                {
                  "type": "alert",
                  "kind": "warning",
                  "title": "注意",
                  "message": "有 2 个任务超过预计工期。"
                }
              ]
            }
          ]
        }
      ]
    },
    "tasks": {
      "type": "page",
      "title": "任务列表",
      "subtitle": "搜索、筛选和分页由 table 自动提供",
      "children": [
        {
          "type": "row",
          "children": [
            {
              "type": "button",
              "text": "新建任务",
              "variant": "primary",
              "icon": "plus",
              "command": {
                "action": "notify",
                "message": "可以接自己的新建逻辑",
                "kind": "success"
              }
            },
            {
              "type": "spacer",
              "expand": true
            },
            {
              "type": "segmented",
              "id": "scope",
              "options": [
                "全部",
                "我的"
              ],
              "value": "全部"
            }
          ]
        },
        {
          "type": "table",
          "columns": [
            {
              "key": "name",
              "text": "任务",
              "width": 260
            },
            {
              "key": "owner",
              "text": "负责人",
              "width": 120
            },
            {
              "key": "status",
              "text": "状态",
              "width": 100
            },
            {
              "key": "due",
              "text": "截止",
              "width": 120
            }
          ],
          "rows": [
            [
              "支付联调",
              "小林",
              "进行中",
              "10-31"
            ],
            [
              "权限审计",
              "阿澈",
              "待开始",
              "11-03"
            ],
            [
              "数据回填",
              "Mia",
              "已完成",
              "10-28"
            ]
          ]
        }
      ]
    },
    "settings": {
      "type": "page",
      "title": "设置",
      "children": [
        {
          "type": "settings_card",
          "title": "自动保存",
          "description": "退出时保存当前设置",
          "icon": "download",
          "children": [
            {
              "type": "switch",
              "id": "autosave",
              "value": true
            }
          ]
        },
        {
          "type": "settings_row",
          "title": "主题",
          "description": "切换后程序会重启",
          "children": [
            {
              "type": "segmented",
              "id": "look",
              "options": [
                {
                  "value": "web",
                  "label": "Web"
                },
                {
                  "value": "win11",
                  "label": "Win11"
                }
              ],
              "value": "web",
              "command": {
                "action": "style",
                "style": "$value"
              }
            }
          ]
        },
        {
          "type": "expander",
          "title": "高级选项",
          "description": "仅 Win11 使用原生展开动画，Web 自动降级",
          "opened": false,
          "children": [
            {
              "type": "settings_row",
              "title": "快捷键",
              "children": [
                {
                  "type": "keychord",
                  "value": "Ctrl+S"
                }
              ]
            },
            {
              "type": "settings_row",
              "title": "日期",
              "children": [
                {
                  "type": "date",
                  "value": "2026-10-30"
                }
              ]
            }
          ]
        }
      ]
    }
  }
}
```

## 规则

- 不要输出 Markdown 解释，除非用户要求；优先输出能直接保存的 JSON。
- 不要写颜色主题；`theme.accent` 最多一个品牌色。
- 不要用 `tk.*` 控件或直接操作 Tk。所有平台差异由 TkUI 处理。
- 给动态内容加 `id`，方便 Python 读写。
- 表格的 `rows` 是二维数组（按列顺序）；列可以是字符串或 `{key,text,width}`。
- 图表：折线/柱状/散点用 `values + labels` 或 `series`；饼/环用 `data`。
- 默认使用 `section`、`settings_row`、`card` 组合信息；避免一长串裸控件。
- 纯 JSON 预览时只用内置动作；需要真实业务时再写 Python `actions`。
- 两种风格不能在同一个 Tk 解释器里混用；运行时切换一律调用
  `app.restart_in_style("web"|"win11")` 或 `tkui.relaunch()`。
