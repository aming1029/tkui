# TkUI 规格参考

版本：`1`。规格是一个 JSON 对象，描述窗口、导航、页面和组件树。所有组件都是
风格无关的；`web` / `win11` 的差异由渲染器处理。

## 顶层字段

```json
{
  "version": 1,
  "title": "窗口标题",
  "description": "可选说明",
  "style": "auto",
  "window": {},
  "theme": {},
  "nav": {},
  "pages": {},
  "body": {},
  "meta": {}
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` | `1` | 必填（省略按 1 处理） |
| `title` | string | 窗口标题的补充；`window.title` 优先 |
| `description` | string | 仅文档用途 |
| `style` | `web` / `win11` / `auto` | 默认 `auto`，可被 `App(style=...)` 覆盖 |
| `window` | object | 见下 |
| `theme` | object | 品牌色与字体 |
| `nav` | object | 侧栏/分段导航 |
| `pages` | object | 多页：页面 key → page 节点 |
| `body` | node | 单页内容；与 `pages` 二选一 |
| `meta` | object | 应用自定义元数据，TkUI 不使用 |

### `window`

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `title` | string | spec.title | 窗口标题 |
| `size` | `[w, h]` | `[980, 700]` | 初始尺寸 |
| `min_size` | `[w, h]` | — | 最小尺寸 |
| `resizable` | bool / `[w, h]` | `true` | 是否可缩放 |
| `centered` | bool | `true` | 是否居中 |
| `chrome` | `native` / `custom` | `native` | `custom` 仅 `win11` 生效 |
| `padding` | int | — | 预留 |
| `icon` | string | — | 预留 |

### `theme`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `accent` | `#RRGGBB` | 品牌主色 |
| `accent_hover` | `#RRGGBB` | 悬停主色 |
| `font_family` | string | 字体族 |
| `font_size` | int | 基础字号 |
| `dpi` | bool | 是否启用 DPI 感知，默认 `true` |

建议只设置 `accent`，其余交给主题。不要在组件里写颜色。

### `nav`

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `mode` | `sidebar` / `segmented` / `none` | 有 pages 时为 `sidebar` | 导航形式 |
| `items` | array | 由 pages 推导 | `[{key,label,icon}]` 或字符串 |
| `selected` | string | 第一个 item | 初始页面 |
| `width` | int | 230 | 侧栏宽度 |
| `title` / `subtitle` | string | — | 预留 |

`items[].icon` 取值：见文末图标列表。

### `pages`

页面 key → 页面对象。页面对象可以省略 `type`：

```json
{
  "home": {
    "title": "首页",
    "subtitle": "可选",
    "scroll": true,
    "padding": 24,
    "gap": 14,
    "children": []
  }
}
```

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `type` | `page` | `page` | 可省略 |
| `title` | string | 页面 key | 标题 |
| `subtitle` | string | — | 副标题 |
| `scroll` | bool | `true` | 是否滚动 |
| `padding` | int | Web 24 / Win11 40 | 内容内边距 |
| `gap` | int | 14 | 子项间距 |
| `children` | node[] | `[]` | 页面内容 |

## 节点

```json
{
  "type": "button",
  "id": "save",
  "text": "保存",
  "variant": "primary",
  "command": "save",
  "tooltip": "快捷键 Ctrl+S",
  "layout": {"fill": "none"},
  "children": []
}
```

| 公共字段 | 说明 |
| --- | --- |
| `type` | 必填，组件类型或别名 |
| `id` | 唯一；用于 `app["id"]` / `app.get("id")` |
| `variable` | 共享 Tk 变量名 |
| `tooltip` | 悬停提示 |
| `enabled` | 是否可用，默认 true |
| `layout` | 排布，见下 |
| `children` | 仅容器可用 |
| `on` | 事件 → 动作 |

**除以上字段外，其余键都是组件属性。** 字符串节点会被当作 `label`：

```json
{"type": "column", "children": ["第一行", {"type": "label", "text": "第二行"}]}
```

## 布局

父容器决定默认方向：

- `column`：纵向，子项默认 `fill=x`；
- `row`：横向，子项默认 `fill=y`；
- `grid`：网格，子项默认按 `columns` 自动排列（默认 2 列）；
- `page` / `scroll` / `card` / `section` / `accordion` / `tab`：纵向。

每个节点可用 `layout` 覆盖：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `side` | `top` / `bottom` / `left` / `right` | pack 方向 |
| `fill` | `x` / `y` / `both` / `none` | 填充方向 |
| `expand` | bool | 是否吸收剩余空间 |
| `padx` / `pady` | int 或 `[a, b]` | 外边距 |
| `ipadx` / `ipady` | int | 内边距 |
| `anchor` | `n/s/e/w/center/...` | 对齐点 |
| `row` / `column` | int | grid 位置 |
| `rowspan` / `columnspan` | int | grid 跨格 |
| `sticky` | string | grid 拉伸，如 `nsew` |
| `weightx` / `weighty` | int | grid 权重 |
| `width` / `height` | int | 固定尺寸 |

常用组合：

```json
{"type": "table", "columns": ["A"], "layout": {"fill": "both", "expand": true}}
```

```json
{"type": "row", "children": [
  {"type": "label", "text": "左侧"},
  {"type": "spacer", "expand": true},
  {"type": "button", "text": "右侧"}
]}
```

```json
{"type": "grid", "columns": 2, "children": [
  {"type": "card", "children": []},
  {"type": "card", "children": []},
  {"type": "card", "layout": {"columnspan": 2}, "children": []}
]}
```

表格、图表、列表、滚动区默认 `fill=both, expand=true`；标签、按钮、徽章默认不拉伸。

## 组件

完整属性、枚举与示例见 [components.md](components.md)（由
`python -m tkui catalog --markdown` 生成）或运行：

```bash
python -m tkui catalog
```

按类别速览：

| 类别 | 组件 |
| --- | --- |
| 布局 | `column` `row` `grid` `spacer` `separator` `scroll` `page` |
| 容器 | `card` `section` `accordion` `tabs` `tab` `settings_row` `settings_card` `expander` |
| 文本 | `label` `heading` |
| 输入 | `button` `entry` `text` `combo` `dropdown` `spinbox` `checkbox` `radio_group` `switch` `segmented` `slider` `date` `keychord` `color` `font` |
| 显示 | `progress` `meter` `badge` `stat` `alert` `image` |
| 数据 | `table` `list` `tree` `spreadsheet` `chart` |

### 别名

| 别名 | 组件 |
| --- | --- |
| `stack` / `vstack` / `frame` | `column` |
| `hstack` / `toolbar` | `row` |
| `divider` | `separator` |
| `listbox` | `list` |
| `combobox` / `select` | `combo` |
| `text_input` / `input` | `entry` |
| `textarea` | `text` |
| `radio` | `radio_group` |
| `figure` | `chart` |
| `datatable` / `data_table` | `table` |
| `grid_table` | `tree` |

### 常用属性速查

| 组件 | 关键属性 |
| --- | --- |
| `button` | `text`, `variant`（primary/secondary/quiet/link/danger/success/toggle/tool）, `icon`, `command` |
| `entry` | `value`, `placeholder`, `kind`（text/password/integer/float/email/date）, `label`, `required`, `min`, `max` |
| `combo` | `values`, `value`, `readonly`, `placeholder` |
| `switch` / `checkbox` | `label`/`text`, `value`, `command` |
| `segmented` | `options`（字符串或 `{value,label}`）, `value` |
| `slider` | `min`, `max`, `step`, `value`, `unit` |
| `progress` | `value`, `max`, `text`, `mode`, `kind`, `orient` |
| `meter` | `value`, `min`, `max`, `shape`（full/semi）, `unit`, `subtext` |
| `stat` | `label`, `value`, `suffix`, `delta`, `kind`, `icon` |
| `alert` | `title`, `message`, `kind` |
| `table` | `columns`（字符串或 `{key,text,width}`）, `rows`（二维数组）, `page_size`, `height` |
| `tree` | `columns`, `rows`, `height` |
| `spreadsheet` | `data`（二维数组）, `rows`, `columns`, `column_width`, `row_height` |
| `chart` | `kind`（line/column/scatter/pie/donut）, `values`, `labels`, `series`, `data`, `height` |
| `settings_row` | `title`, `description`, `help`；children 放到右侧 |
| `settings_card` | `title`, `description`, `icon`, `command`；children 放到右侧 |
| `expander` | `title`, `description`, `icon`, `opened` |

### 图表数据

折线/柱状：

```json
{"type": "chart", "kind": "column", "labels": ["A", "B"],
 "series": [{"name": "计划", "values": [10, 20]},
            {"name": "实际", "values": [12, 18]}]}
```

散点：

```json
{"type": "chart", "kind": "scatter",
 "series": [{"name": "观测", "points": [[1, 2], [2.5, 4]]}]}
```

饼/环：

```json
{"type": "chart", "kind": "donut",
 "data": [["已完成", 42], ["处理中", 18]]}
```

### 表格行

`table` 的 `rows` 是按列顺序的二维数组：

```json
{"type": "table",
 "columns": [{"key": "name", "text": "名称", "width": 240}, "数量"],
 "rows": [["资料 A", 12], ["资料 B", 7]]}
```

`tree` 也接受字典行；`table` 建议用数组行。

## 状态与取值

```python
app.get("name")               # entry/combo/switch/slider/... 的当前值
app.set("name", "新的值")     # 默认触发 change 动作
app.set("name", "静默", silent=True)   # 不触发动作
app["name"]                   # 控件
app.native("tasks_table")     # 复合控件内部的原生控件
```

共享变量：

```json
{"type": "radio_group", "variable": "size", "options": ["S", "M", "L"]}
```

任何控件都可以写 `variable`，同名变量自动共享。

## 动作

### 1. 动作名（Python）

```json
{"type": "button", "text": "保存", "command": "save"}
```

```python
app = tkui.App(spec, actions={"save": on_save})
```

回调签名：

```python
def on_save():        ...
def on_save(event):   ...
```

`event` 字段：

| 字段 | 说明 |
| --- | --- |
| `name` | `click` / `change` / `select` / `activate` |
| `value` | 当前值或数据点 |
| `id` | 组件 id |
| `widget` | 控件 |
| `app` | App 实例 |

### 2. 内置动作（纯 JSON）

```json
{"action": "notify", "message": "已保存", "title": "完成", "kind": "success"}
{"action": "navigate", "page": "settings"}
{"action": "set", "target": "name", "value": "新值"}
{"action": "toggle", "target": "autosave"}
{"action": "dialog", "message": "提示内容", "title": "提示", "kind": "warning"}
{"action": "style", "style": "win11"}
{"action": "chain", "chain": [{"action": "notify", "message": "第一步"},
                              {"action": "navigate", "page": "home"}]}
{"action": "quit"}
{"action": "log", "message": "debug"}
```

`style` 与 `set` 的值支持 `"$value"`，表示事件当前值。例如：

```json
{"type": "segmented", "options": ["web", "win11"],
 "command": {"action": "style", "style": "$value"}}
```

### 3. 事件映射

| 事件 | 适用组件 |
| --- | --- |
| `click` | `button`, `card`, `chart` |
| `change` | 输入类、`slider`、`meter`、`spreadsheet` |
| `select` | `list`, `tree`, `table`, `chart` |
| `activate` | `tree`, `table`（双击行） |

```json
{"type": "entry", "on": {"change": {"action": "set", "target": "preview",
                                    "value": "$value"}}}
```

## Python 集成

```python
import tkui

spec = tkui.load("app.json")
app = tkui.App(spec, style="win11", actions={
    "save": lambda event: app.notify("已保存", kind="success"),
})
app.navigate("settings")
app.run()
```

嵌入：

```python
app = tkui.mount(frame, spec_or_node, style="web", actions={})
```

嵌入时没有自己的 mainloop，由宿主窗口负责。

## 风格选择

| 方式 | 代码 |
| --- | --- |
| 参数 | `tkui.App(spec, style="win11")` |
| 环境变量 | `TKUI_STYLE=win11` |
| 配置文件 | `python -m tkui choose` / `tkui.choose_style()` |
| 运行中 | `app.restart_in_style("web")` |

优先级：显式参数 → 环境变量 → 配置文件 → 默认 `web`。

## 校验

```bash
python -m tkui check app.json
python -m tkui check app.json --json
```

错误级别：

- `错误`：未知组件、未知枚举、类型错误、必填缺失、id 冲突、tab 位置错误；
- `提示`：未知字段、可疑的快捷写法、导航指向不存在的页面。

未知字段只提示不阻止运行，方便渐进式扩展；未知组件和类型错误会阻止构建。

## JSON Schema

```bash
python -m tkui schema -o schema/tkui-1.json
```

Schema 由目录生成，覆盖根对象、页面、布局和每个组件的属性。运行时校验比 Schema
更严格，也会检查 id、tab 位置和图表数据完整性。

## 图标

`plus` `search` `edit` `play` `check` `library` `sources` `settings`
`controls` `folder` `download` `back` `speed` `pin` `chevronup`
`chevrondown` `chevronright` `collapse` `expand` `info`

## 常见错误

| 症状 | 修复 |
| --- | --- |
| `未知组件 'buton'` | 用 `button`，或运行 `catalog` 确认名称 |
| 表格行数不匹配 | `rows` 每行长度必须等于 `columns` 数量 |
| 图表空白 | 折线/柱状需要 `values` 或 `series`；饼/环需要 `data` |
| `tab` 报错 | `tab` 只能放在 `tabs` 的 `children` 里 |
| 动作未注册 | 在 `actions={}` 里提供同名函数，或改用内置动作 |
| 控件不拉伸 | 加 `"layout": {"fill": "both", "expand": true}` |
| 切换风格报错 | 两个主题不能同进程共存；用 `restart_in_style()` |
