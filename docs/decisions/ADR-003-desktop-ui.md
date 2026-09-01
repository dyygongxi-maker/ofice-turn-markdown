# ADR-003：推荐原生桌面 UI 作为 MVP 宿主

## Status

Superseded by D-006

## Date

2026-09-01

## Context

产品要求纯本地处理，用户必须选择输入文件与输出目录。此前设计中提出的本地浏览器界面无法跨浏览器可靠地获得任意输出目录写入权限，和产品流程存在摩擦。

## Decision

采用 Tkinter 构建 Windows 原生界面，UI 直接调用应用服务；PyInstaller 构建固定使用包含 Tcl/Tk 8.6 的 Python 3.13 环境。核心不依赖具体 UI 框架，未来可以替换 UI 宿主。

## Alternatives Considered

### 本地 FastAPI + 浏览器界面

- 优点：前端生态丰富、浏览器预览方便。
- 缺点：输出目录选择需要下载 ZIP、浏览器特定 API 或额外原生对话框，增加边界复杂度。
- 结论：当前拒绝。

### Tauri + React + Python sidecar

- 优点：现代桌面体验、未来跨平台潜力。
- 缺点：Rust、TypeScript 与 Python 多运行时组合超出 MVP 的必要复杂度。
- 结论：以后评估。

### PySide6-Essentials

- 优点：组件和视觉能力更强。
- 缺点：当前构建环境的 Windows 原生 DLL 链无法被 PyInstaller 稳定解析；多次干净构建仍无法加载 `QtWidgets`。
- 结论：拒绝作为当前分发方案。

## Consequences

- Windows 成为 MVP 的明确目标平台。
- Python 3.13 Tcl/Tk 和候选解析库须随每次发布执行 PyInstaller 构建与主窗口验证；高级可访问性与视觉定制留待后续版本。
- 浏览器 UI 只能作为未来替代宿主，不能改变核心合同。
