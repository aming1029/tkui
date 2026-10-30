# TkUI — 给 AI 用的一套声明式 Tk 组件层

TkUI 把 [TkWebUI](https://github.com/bvb6417/tkwebui) 的**现代 Web 应用风**与
[TkWin11](https://github.com/bvb6417/tkwin11) 的 **Windows 11 Fluent 风**统一到
一套**风格无关**的组件树上。同一份 JSON 规格，可以在两种外观下运行；用户可以在
启动前选择，也可以让程序保存偏好后重启切换。

它不是简单的再包一层：TkUI 提供的是 AI 真正需要的四件事——**稳定的组件词汇表、
声明式规格、可校验的规格、以及一套动作模型**。AI 不需要记住两个库的差异，也不需
要写 Tk 代码。

## 作为 Agent Skill 使用

仓库里同时提供 `skills/tkinter-ui/`（`SKILL.md` + references + scripts + assets +
内置运行时）。它先做路由：

- **A 直接写上游库**：单文件、小工具、需要 `FluentTitleBar` / `KeyChord` 等
  上游专属能力时，直接生成 `tkwebui` 或 `tkwin11` 代码；
- **B 声明式 TkUI**：多页、表单/表格/图表密集、需要同一份界面两种外观时，生成 JSON 规格；
- **C 两者都有**：该 skill 的形态，按任务自动选择 A 或 B。

安装（Windows 目录联接，或直接复制目录）：

```powershell
New-Item -ItemType Junction -Path "$HOME\.codex\skills\tkinter-ui" `
  -Target "D:\github_git\tkui\skills\tkinter-ui"
```

```text
~/.claude/skills/tkinter-ui
~/.agents/skills/tkinter-ui
```

入口：`skills/tkinter-ui/SKILL.md`。

该目录自带 `runtime/tkui` 和 `runtime/vendor/` 中的两个上游 MIT 包，可单独复制到
任意 skills 目录；不依赖本仓库路径，也不需要额外 pip 安装。

![Web 应用风](docs/images/web-overview.png)

![Windows 11 Fluent 风](docs/images/win11-overview.png)

## 两个上游分别代表什么

| | TkWebUI（`web`） | TkWin11（`win11`） |
| --- | --- | --- |
| 外观 | 现代 Web / SaaS：白底、圆角卡片、`#087DFF` 蓝 | Windows 11 Fluent：Mica 感工作区、`#0067C0`、原生控件感 |
| 实现方式 | 启动时生成一次 ttk 样式，不接管 Tk 内部命令 | 运行时接管样式、字体、控件命令，支持动画与每显示器 DPI |
| 接入 | `Tk()` 之后 `apply_theme(root)` | 可 `Tk()` 之前 `install()`，经典 `tk.*` 控件一起换肤 |
| 动效 | 无过渡，页面切换约 +16 ms | 悬停/按下/开关/导航/页面切换有过渡，首次打开每页约 +70 ms |
| 体积 | 库代码约 4.8k 行 | 库代码约 9.1k 行 |
| 长处 | 行为可预期、依赖少、表格/图表/表单直给 | 桌面质感、动画、DPI、一体化标题栏、WinUI 布局组件 |
| 适合 | 科研、工程、内部数据工具 | 发给 Windows 用户的桌面程序 |

详细对比与实践选择见 [docs/research.md](docs/research.md)。

> 两个主题**不能**在同一个 Tk 解释器里混用。TkUI 通过“重启换风格”绕开这个限制，
> 而不是把两个库同时导入。

## 三种选择风格的方式

1. **命令行**（推荐给脚本和 AI）：

   ```bash
   python -m tkui run app.json --style web
   python -m tkui run app.json --style win11
   python -m tkui run app.json --style auto     # 环境变量/配置文件/默认值
   ```

2. **用户选择对话框**（不依赖任何主题库，先选再创建主题窗口）：

   ```bash
   python -m tkui demo --choose
   ```

   ```python
   import tkui
   style = tkui.choose_style()      # 返回 "web" 或 "win11"，并记住选择
   tkui.run("app.json", style=style)
   ```

3. **程序内切换**：

   ```python
   app.restart_in_style("win11")    # 保存偏好，启动新进程后退出当前进程
   ```

偏好保存位置：Windows 为 `%APPDATA%\tkui\config.json`，其他平台为
`~/.config/tkui/config.json`；也可用 `TKUI_CONFIG` 指定文件。环境变量
`TKUI_STYLE=web|win11` 优先于配置文件。

## 快速开始

仓库里已经带有两个上游目录，直接运行即可：

```bash
python demo.py                              # 组件画廊
python demo.py --style win11
python demo.py --choose                     # 先选风格
python -m tkui demo --page charts
```

最小应用：

```json
{
  "version": 1,
  "title": "我的工具",
  "window": {"size": [900, 620]},
  "body": {
    "type": "column",
    "gap": 14,
    "padding": 24,
    "children": [
      {"type": "heading", "title": "你好", "subtitle": "一份规格，两种外观"},
      {"type": "entry", "id": "name", "label": "名称", "placeholder": "请输入"},
      {"type": "row", "children": [
        {"type": "button", "text": "保存", "variant": "primary", "command": "save"},
        {"type": "button", "text": "Web / Win11 切换", "variant": "quiet",
         "command": {"action": "style", "style": "win11"}}
      ]}
    ]
  }
}
```

```python
import tkui

def on_save(event):
    print("name =", event.app.get("name"))

app = tkui.App("examples/minimal.json", actions={"save": on_save})
app.run()
```

嵌入已有窗口：

```python
import tkinter as tk
from tkinter import ttk
import tkui

root = tk.Tk()
panel = ttk.Frame(root)
panel.pack(fill="both", expand=True)
tkui.mount(panel, {"type": "section", "title": "嵌入", "children": [
    {"type": "label", "text": "TkUI 可以只渲染一棵组件树"}
]}, style="web")
root.mainloop()
```

## 组件覆盖

| 类别 | 组件 |
| --- | --- |
| 布局 | `column` / `row` / `grid` / `spacer` / `separator` / `scroll` / `page` |
| 容器 | `card` / `section` / `accordion` / `tabs` + `tab` / `settings_row` / `settings_card` / `expander` |
| 文本 | `label` / `heading` |
| 输入 | `button` / `entry` / `text` / `combo` / `dropdown` / `spinbox` / `checkbox` / `radio_group` / `switch` / `segmented` / `slider` / `date` / `keychord` / `color` / `font` |
| 显示 | `progress` / `meter` / `badge` / `stat` / `alert` / `image` |
| 数据 | `table` / `list` / `tree` / `spreadsheet` / `chart`（line / column / scatter / pie / donut） |

共 43 个组件类型（不含别名）。完整属性、枚举、示例：

```bash
python -m tkui catalog --markdown
python -m tkui catalog             # JSON，适合喂给模型
```

Win11 专属组件在 Web 下自动降级：

- `expander` → `accordion`
- `settings_card` → `Card + SettingRow`
- `keychord` → 只读输入框
- `window.chrome: "custom"` → 系统标题栏

## AI 工作流

TkUI 的主要目标就是让 AI 少写错代码、少猜 API。

```bash
python -m tkui prompt -o AI_PROMPT.md     # 给模型的完整说明 + 组件目录
python -m tkui schema -o schema/tkui-1.json
python -m tkui check app.json --json      # 结构化校验结果与动作列表
python -m tkui run app.json --style web
```

推荐给模型的约定：

1. 读 `AI_PROMPT.md` 或运行 `python -m tkui catalog`。
2. **只输出 JSON 规格**，不写 Tk 代码、颜色、字体或后端分支。
3. 用 `id` 标记需要读写的控件，用 `command` / `on` 接动作。
4. 用 `python -m tkui check app.json --json` 自检，按 `path` 修错。
5. 需要真实业务逻辑时，再写 Python 的 `actions={"name": fn}`。

更完整的说明见 [docs/ai.md](docs/ai.md) 与自动生成的 `AI_PROMPT.md`。

## 规格长什么样

```json
{
  "version": 1,
  "title": "项目脉搏",
  "nav": {"mode": "sidebar", "selected": "overview",
          "items": [{"key": "overview", "label": "概览", "icon": "speed"},
                    {"key": "tasks", "label": "任务", "icon": "library"}]},
  "pages": {
    "overview": {
      "type": "page",
      "title": "概览",
      "children": [
        {"type": "stat", "label": "进行中", "value": "8", "delta": "+2"},
        {"type": "section", "title": "本周提交", "children": [
          {"type": "chart", "kind": "column",
           "values": [12, 18, 9, 22], "labels": ["一", "二", "三", "四"]}
        ]}
      ]
    },
    "tasks": {
      "type": "page",
      "title": "任务",
      "children": [
        {"type": "table",
         "columns": ["任务", "负责人", "状态"],
         "rows": [["支付联调", "小林", "进行中"]]}
      ]
    }
  }
}
```

布局、属性和动作的完整规则见 [docs/spec.md](docs/spec.md)。

## Python API

```python
app = tkui.App(spec_or_path, style=None, actions={}, theme={}, master=None)
app.run()

app["name"]                 # 控件实例
app.native("tasks_table")   # 复合控件的内部原生控件（如 Treeview）
app.get("name")             # 取值
app.set("name", "新值")     # 写值（默认触发 change）
app.navigate("settings")    # 切页
app.notify("已保存", kind="success")
app.dialog("提示内容")
app.restart_in_style("web")
app.info()                  # 风格、后端、版本、页面、组件数
```

动作回调签名：

```python
def on_save():            ...   # 无参数
def on_save(event):       ...   # event.name / value / id / widget / app
```

内置动作（纯 JSON 也能用）：`notify`、`navigate`、`set`、`toggle`、`dialog`、
`style`、`chain`、`quit`、`log`。详见 [docs/spec.md](docs/spec.md#动作)。

## 目录

```text
tkui/             统一层（本仓库新增）
  theme.py        风格解析、偏好、选择器、重启
  backends.py     只加载一个上游，风格检测与样式增强
  catalog.py      组件词汇表（AI 的契约）
  spec.py         校验 + JSON Schema
  renderer.py     声明式组件树 → Tk 控件
  app.py          窗口、页面、动作、取值
  ai.py           AI 提示词与示例
  demo.py         组件画廊
tkwebui-main/     上游：现代 Web 风
tkwin11-main/     上游：Windows 11 Fluent
skills/tkinter-ui/ Agent Skill（A 直接写库 / B 声明式 / C 路由）
examples/         可直接运行的 JSON / Python 示例
docs/             研究、规格、AI 用法
tests/            单元测试与两种风格的全组件渲染测试
```

## 测试

```bash
python -m unittest discover -s tests -v
```

包含：

- 目录/别名/JSON Schema 一致性；
- 规格校验的错误路径与动作收集；
- 风格解析优先级与配置持久化；
- 内置动作与回调签名；
- **两种风格各自在子进程里渲染全部 43 个组件**，并读写值、切页、关闭。

## 环境与限制

- 开发和测试环境：Windows 11 + Python 3.15 + Tk 9.0；上游声明支持 Python 3.8+。
- 只依赖 Python 标准库和两个上游库；`ImageViewer` 读取非 PNG/GIF/PPM 图片时需要 Pillow。
- `web` / `win11` 不能在同一 Tk 解释器里混用；运行中切换必须重启。
- 一体化标题栏（`window.chrome: "custom"`）目前只在 `win11` 生效，Web 使用系统标题栏。
- 图表定位是小工具里的常见图表（几十到几千点），不是 Matplotlib 的替代品。
- 两个上游的清理回调在 Python 3.15/Tk 9 下关闭时可能打印 `can't delete Tcl command`；
  `App.close()` 会屏蔽这类无害噪声。

## 许可与致谢

TkUI 使用 MIT 许可。上游 [TkWebUI](https://github.com/bvb6417/tkwebui) 与
[TkWin11](https://github.com/bvb6417/tkwin11) 同样使用 MIT 许可；本仓库保留两个
上游目录及其许可文件。样式、控件与图表的核心实现归上游作者所有，TkUI 只负责统一
入口、声明式渲染、校验、动作与风格选择。
