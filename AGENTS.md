# AGENTS.md — 给编码 Agent 的项目约定

## 这是什么

`tkui/` 是对两个同源 Tk 主题库的统一层：

- `web` → TkWebUI（现代 Web 风）
- `win11` → TkWin11（Windows 11 Fluent 风）

AI 的主要工作方式是**写 JSON 规格**，而不是写 Tk 代码。规格由
`tkui/catalog.py` 定义、由 `tkui/spec.py` 校验、由 `tkui/renderer.py` 渲染。

仓库还提供 Agent Skill：`skills/tkinter-ui/SKILL.md`。它有两种实现路径：

- Mode A：直接生成 `tkwebui` / `tkwin11` 代码（单文件、上游专属能力）；
- Mode B：生成 TkUI JSON 规格（多页、两种外观、可校验）。

在 Codex/Claude 中工作时先读该 skill，再按其中路由选择 A 或 B。

## 首先阅读

1. `AI_PROMPT.md`：完整的组件目录和生成规则。
2. `docs/spec.md`：规格字段、布局、动作。
3. `docs/research.md`：两个上游的差异与设计理由。
4. `tkui/catalog.py`：唯一事实来源。

## 生成界面

```bash
python -m tkui check app.json --json
python -m tkui run app.json --style web
python -m tkui run app.json --style win11
```

规则：

- 只输出 JSON；不要输出 Tk/Tcl。
- 不写颜色、字体、像素尺寸；用 `variant`、`kind`、`layout`。
- 不写 `web`/`win11` 分支；两种风格必须共用一份规格。
- 动态控件加唯一 `id`；用 `command` / `on` 接动作。
- 纯 JSON 原型只用内置动作；业务逻辑放 `actions`。

## 修改库

新增组件时必须同步：

1. `tkui/catalog.py` 的 `COMPONENTS`（名称、属性、事件、示例、默认布局）；
2. `tkui/renderer.py` 的渲染函数与 `_RENDERERS`；
3. `tests/_render_all.py` 的全组件规格；
4. 重新生成：

```bash
python -m unittest discover -s tests -v
python -m tkui schema -o schema/tkui-1.json
python -m tkui catalog --markdown > docs/components.md
python -m tkui prompt -o AI_PROMPT.md
```

## 不要做

- 不要修改 `tkwebui-main/`、`tkwin11-main/`；它们是只读上游。
- 不要在同一个 Tk 解释器里 import 两个后端；风格切换必须重启。
- 不要把 `web` 专属实现写进规格；用 `catalog` 的降级规则。
- 不要吞掉规格错误；`check` 的路径和动作列表是 AI 的修复入口。

## 验证

```bash
python -m unittest discover -s tests -v
python demo.py --style web
python demo.py --style win11
```

全组件渲染测试会分别在两个子进程里跑，避免两个主题库混用。
