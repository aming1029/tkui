# TkUI 组件目录

规格版本：1。所有组件都只有一份风格无关的声明；`web` / `win11` 的差异由渲染器处理。

## 布局字段

任何组件都可以带 `layout`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `side` | top / bottom / left / right | pack 方向 |
| `fill` | x / y / both / none | 填充方向 |
| `expand` | bool | 是否占用剩余空间 |
| `padx` | int | 水平外边距（可写 [左, 右]） |
| `pady` | int | 垂直外边距（可写 [上, 下]） |
| `ipadx` | int | 水平内边距 |
| `ipady` | int | 垂直内边距 |
| `anchor` | n / s / e / w / center / ne / nw / se / sw | 对齐点 |
| `row` | int | grid 行（grid 父容器内） |
| `column` | int | grid 列（grid 父容器内） |
| `rowspan` | int | grid 跨行 |
| `columnspan` | int | grid 跨列 |
| `sticky` | str | grid 拉伸，如 nsew |
| `weightx` | int | grid 列权重 |
| `weighty` | int | grid 行权重 |
| `width` | int | 固定宽度 |
| `height` | int | 固定高度 |

## 组件

### 布局

#### `column`

纵向堆叠容器（默认填充 x）。

容器：是；子项：任意非 tab 组件。

属性：`gap`:int=8, `padding`:int=0, `surface`:panel|workspace|sidebar=panel

```json
{
  "type": "column",
  "gap": 12,
  "children": []
}
```

#### `row`

横向排列容器，子项默认垂直填充。

容器：是；子项：任意非 tab 组件。

属性：`gap`:int=8, `padding`:int=0, `align`:center|start|end|stretch=center, `surface`:panel|workspace|sidebar=panel

```json
{
  "type": "row",
  "gap": 8,
  "children": []
}
```

#### `grid`

网格容器；子项用 layout.row / layout.column 指定位置。

容器：是；子项：任意非 tab 组件。

属性：`gap`:int=8, `padding`:int=0, `columns`:int=2, `surface`:panel|workspace|sidebar=panel

```json
{
  "type": "grid",
  "columns": 2,
  "children": []
}
```

#### `spacer`

固定或弹性空白。

属性：`size`:int=8, `expand`:bool=False

```json
{
  "type": "spacer",
  "size": 12
}
```

#### `separator`

分隔线。

属性：`orient`:horizontal|vertical=horizontal

```json
{
  "type": "separator"
}
```

#### `scroll`

可滚动区域，内容放在 body 中。

容器：是；子项：任意组件。

属性：`height`:int=320, `gap`:int=10, `padding`:int=0

```json
{
  "type": "scroll",
  "height": 360,
  "children": []
}
```

#### `page`

页面：标题 + 可滚动内容。通常只出现在 pages 下。

容器：是；子项：任意组件。

属性：`title`:str=—, `subtitle`:str=—, `scroll`:bool=True, `padding`:int=24, `gap`:int=14

```json
{
  "type": "page",
  "title": "概览",
  "children": []
}
```

### 容器

#### `card`

圆角卡片容器，可点击。

容器：是；子项：任意非 tab 组件。

属性：`selected`:bool=False, `padding`:int=16, `command`:action=—

事件：`click`

```json
{
  "type": "card",
  "children": []
}
```

#### `section`

带标题的分组卡片。

容器：是；子项：任意非 tab 组件。

属性：`title`:str=—, `padding`:int=14, `selected`:bool=False

事件：`click`

```json
{
  "type": "section",
  "title": "基本设置",
  "children": []
}
```

#### `accordion`

可折叠分组。

容器：是；子项：任意非 tab 组件。

属性：`title`:str=—, `opened`:bool=False

事件：`click`

```json
{
  "type": "accordion",
  "title": "高级选项",
  "opened": true,
  "children": []
}
```

#### `tabs`

标签页容器，子项必须是 tab。

容器：是；子项：tab。

属性：`padding`:int=12

```json
{
  "type": "tabs",
  "children": [
    {
      "type": "tab",
      "title": "一",
      "children": []
    }
  ]
}
```

#### `tab`

tabs 的单个标签页。

容器：是；子项：任意非 tab 组件。

属性：`title`:str=—, `padding`:int=12

```json
{
  "type": "tab",
  "title": "一",
  "children": []
}
```

#### `settings_row`

设置行：左侧标题/说明，右侧放控件。

容器：是；子项：通常放 switch / combo / button 等单个控件。

属性：`title`:str=—, `description`:str=—, `help`:str=—

```json
{
  "type": "settings_row",
  "title": "自动保存",
  "description": "退出时保存",
  "children": [
    {
      "type": "switch",
      "label": ""
    }
  ]
}
```

#### `settings_card`

带图标的设置卡片（Win11 使用原生 SettingsCard，Web 使用等价布局）。

容器：是；子项：通常放 switch / combo / button 等单个控件。

属性：`title`:str=—, `description`:str=—, `icon`:plus|search|edit|play|check|library|sources|settings|controls|folder|download|back|speed|pin|chevronup|chevrondown|chevronright|collapse|expand|info=settings, `command`:action=—

事件：`click`

```json
{
  "type": "settings_card",
  "title": "自动保存",
  "icon": "download",
  "children": [
    {
      "type": "switch",
      "label": ""
    }
  ]
}
```

#### `expander`

可展开卡片（Win11 原生动画，Web 退化为 Accordion）。（仅 win11，Web 回退：accordion）

容器：是；子项：任意非 tab 组件。

属性：`title`:str=—, `description`:str=—, `icon`:plus|search|edit|play|check|library|sources|settings|controls|folder|download|back|speed|pin|chevronup|chevrondown|chevronright|collapse|expand|info=settings, `opened`:bool=False

事件：`click`

```json
{
  "type": "expander",
  "title": "更多设置",
  "children": []
}
```

### 文本

#### `label`

文本标签。

属性：`text`:str=, `style`:body|muted|strong|title|subtitle|caption=body, `wrap`:int=0, `justify`:left|center|right=left, `anchor`:w|center|e=w, `icon`:plus|search|edit|play|check|library|sources|settings|controls|folder|download|back|speed|pin|chevronup|chevrondown|chevronright|collapse|expand|info=None

```json
{
  "type": "label",
  "text": "说明文字",
  "style": "muted"
}
```

#### `heading`

标题 + 副标题块。

属性：`title`:str=—, `subtitle`:str=—, `level`:int=2, `align`:w|center|e=w

```json
{
  "type": "heading",
  "title": "数据概览",
  "subtitle": "最近 7 天"
}
```

### 输入

#### `button`

按钮。

属性：`text`:str=, `variant`:primary|secondary|quiet|link|danger|success|toggle|tool=secondary, `icon`:plus|search|edit|play|check|library|sources|settings|controls|folder|download|back|speed|pin|chevronup|chevrondown|chevronright|collapse|expand|info=None, `command`:action=—, `width`:int=—

事件：`click`

```json
{
  "type": "button",
  "text": "保存",
  "variant": "primary",
  "command": "save"
}
```

#### `entry`

单行输入框，可带校验。

属性：`value`:str=, `placeholder`:str=—, `kind`:text|password|integer|float|email|date=text, `label`:str=—, `required`:bool=False, `min`:float=—, `max`:float=—, `width`:int=—, `command`:action=—

事件：`change`

```json
{
  "type": "entry",
  "id": "name",
  "placeholder": "请输入名称",
  "label": "名称"
}
```

#### `text`

多行文本框。

属性：`value`:str=, `height`:int=5, `readonly`:bool=False, `wrap`:word|char|none=word, `command`:action=—

事件：`change`

```json
{
  "type": "text",
  "height": 6,
  "placeholder": "备注"
}
```

#### `combo`

下拉选择框（可编辑或只读）。

属性：`values`:list=[], `value`:str=, `readonly`:bool=True, `placeholder`:str=—, `width`:int=—, `command`:action=—

事件：`change`

```json
{
  "type": "combo",
  "values": [
    "低",
    "中",
    "高"
  ],
  "value": "中",
  "command": "priority"
}
```

#### `dropdown`

带自定义浮层的下拉框。

属性：`values`:list=[], `value`:str=, `placeholder`:str=—, `command`:action=—

事件：`change`

```json
{
  "type": "dropdown",
  "values": [
    "A",
    "B"
  ],
  "command": "pick"
}
```

#### `spinbox`

数值微调框。

属性：`value`:float=0, `min`:float=0, `max`:float=100, `step`:float=1, `width`:int=8, `command`:action=—

事件：`change`

```json
{
  "type": "spinbox",
  "min": 1,
  "max": 12,
  "value": 3
}
```

#### `checkbox`

复选按钮。

属性：`text`:str=, `value`:bool=False, `command`:action=—

事件：`change`

```json
{
  "type": "checkbox",
  "text": "记住选择",
  "value": true
}
```

#### `radio_group`

一组单选按钮。

属性：`options`:list=—, `value`:str=—, `orientation`:horizontal|vertical=horizontal, `command`:action=—

事件：`change`

```json
{
  "type": "radio_group",
  "options": [
    "小",
    "中",
    "大"
  ],
  "value": "中"
}
```

#### `switch`

滑动开关。

属性：`label`:str=, `value`:bool=False, `command`:action=—

事件：`change`

```json
{
  "type": "switch",
  "label": "自动同步",
  "value": true
}
```

#### `segmented`

分段选择器。

属性：`options`:list=—, `value`:str=—, `command`:action=—

事件：`change`

```json
{
  "type": "segmented",
  "options": [
    "日",
    "周",
    "月"
  ],
  "value": "日"
}
```

#### `slider`

带数值框的滑块。

属性：`value`:float=0, `min`:float=0, `max`:float=100, `step`:float=1, `unit`:str=, `command`:action=—

事件：`change`

```json
{
  "type": "slider",
  "min": 0,
  "max": 10,
  "value": 4,
  "unit": "级"
}
```

#### `date`

日期选择框。

属性：`value`:str=—, `min`:str=—, `max`:str=—, `command`:action=—

事件：`change`

```json
{
  "type": "date",
  "value": "2026-10-30"
}
```

#### `keychord`

快捷键徽章（Win11 可编辑，Web 退化为只读输入框）。（仅 win11，Web 回退：readonly entry）

属性：`value`:str=Ctrl+S, `command`:action=—

事件：`click`

```json
{
  "type": "keychord",
  "value": "Alt+Shift+A"
}
```

#### `color`

颜色选择器。

属性：`value`:str=#087DFF, `command`:action=—

事件：`change`

```json
{
  "type": "color"
}
```

#### `font`

字体选择器。

属性：`value`:str=TkDefaultFont

事件：`change`

```json
{
  "type": "font"
}
```

### 显示

#### `progress`

带文字进度条。

属性：`value`:float=0, `max`:float=100, `text`:str=—, `mode`:determinate|indeterminate=determinate, `kind`:primary|success|warning|danger|info=primary, `orient`:horizontal|vertical=horizontal, `length`:int=240, `thickness`:int=28

```json
{
  "type": "progress",
  "value": 62,
  "text": "构建"
}
```

#### `meter`

圆形/半圆仪表。

属性：`value`:float=0, `min`:float=0, `max`:float=100, `shape`:full|semi=full, `unit`:str=%, `subtext`:str=—, `interactive`:bool=False, `size`:int=190, `command`:action=—

事件：`change`

```json
{
  "type": "meter",
  "value": 72,
  "subtext": "健康度"
}
```

#### `badge`

语义色小徽章。

属性：`text`:str=, `kind`:info|success|warning|danger|neutral=info

```json
{
  "type": "badge",
  "text": "已完成",
  "kind": "success"
}
```

#### `stat`

指标卡：标签、大数字、变化量。

属性：`label`:str=—, `value`:str=—, `suffix`:str=—, `delta`:str=—, `kind`:info|success|warning|danger|neutral=info, `icon`:plus|search|edit|play|check|library|sources|settings|controls|folder|download|back|speed|pin|chevronup|chevrondown|chevronright|collapse|expand|info=None

```json
{
  "type": "stat",
  "label": "今日访问",
  "value": "12,480",
  "delta": "+8.2%",
  "kind": "success"
}
```

#### `alert`

内联提示条。

属性：`message`:str=—, `title`:str=—, `kind`:info|success|warning|danger|neutral=info

```json
{
  "type": "alert",
  "title": "注意",
  "message": "数据尚未保存",
  "kind": "warning"
}
```

#### `image`

图片查看器（PNG/GIF/PPM 原生，其他格式需 Pillow）。

属性：`path`:str=—, `height`:int=300

```json
{
  "type": "image",
  "height": 260
}
```

### 数据

#### `table`

搜索、筛选、分页、导出 CSV 的数据表。

属性：`columns`:list=—, `rows`:list=[], `page_size`:int=10, `height`:int=8, `command`:action=—

事件：`activate`, `select`

```json
{
  "type": "table",
  "columns": [
    "名称",
    "数量"
  ],
  "rows": [
    [
      "资料 A",
      12
    ],
    [
      "资料 B",
      7
    ]
  ]
}
```

#### `list`

单列列表框。

属性：`items`:list=[], `value`:int=-1, `selectmode`:browse|single|multiple|extended=browse, `height`:int=8, `command`:action=—

事件：`change`, `select`

```json
{
  "type": "list",
  "items": [
    "苹果",
    "香蕉",
    "橙子"
  ],
  "value": 0
}
```

#### `tree`

可排序多列表格。

属性：`columns`:list=—, `rows`:list=[], `height`:int=8, `command`:action=—

事件：`activate`, `select`

```json
{
  "type": "tree",
  "columns": [
    "名称",
    "数量"
  ],
  "rows": [
    [
      "A",
      3
    ],
    [
      "B",
      5
    ]
  ]
}
```

#### `spreadsheet`

Excel 式单元格表格，支持多选、复制粘贴、撤销。

属性：`data`:list=[], `rows`:int=30, `columns`:int=8, `column_width`:int=122, `row_height`:int=30, `command`:action=—

事件：`change`

```json
{
  "type": "spreadsheet",
  "data": [
    [
      "项目",
      "数量"
    ],
    [
      "资料整理",
      "12"
    ]
  ]
}
```

#### `chart`

原生交互图表（折线/柱状/散点/饼/环）。

属性：`kind`:line|column|scatter|donut|pie=line, `values`:list=—, `labels`:list=—, `series`:list=—, `data`:list=—, `height`:int=240, `command`:action=—

事件：`select`, `click`

```json
{
  "type": "chart",
  "kind": "line",
  "values": [
    12,
    18,
    14,
    26
  ],
  "labels": [
    "一",
    "二",
    "三",
    "四"
  ]
}
```
