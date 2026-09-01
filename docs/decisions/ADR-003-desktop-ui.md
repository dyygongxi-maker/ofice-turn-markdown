# ADR-003：推荐原生桌面 UI 作为 MVP 宿主

## Status

Accepted

## Date

2026-09-01

## Context

产品要求纯本地处理，用户必须选择输入文件与输出目录。此前设计中提出的本地浏览器界面无法跨浏览器可靠地获得任意输出目录写入权限，和产品流程存在摩擦。

## Decision

采用 Python 标准库 Tkinter 构建 Windows 原生界面，UI 直接调用应用服务。核心不依赖 Tkinter，未来可以替换 UI 宿主。

## Alternatives Considered

### 本地 FastAPI + 浏览器界面

- 优点：前端生态丰富、浏览器预览方便。
- 缺点：输出目录选择需要下载 ZIP、浏览器特定 API 或额外原生对话框，增加边界复杂度。
- 结论：当前拒绝。

### Tauri + React + Python sidecar

- 优点：现代桌面体验、未来跨平台潜力。
- 缺点：Rust、TypeScript 与 Python 多运行时组合超出 MVP 的必要复杂度。
- 结论：以后评估。

### PySide6

- 优点：组件和视觉能力更强。
- 缺点：当前环境下载其运行时多次中断，且 MVP 不需要高级控件。
- 结论：当前拒绝；核心稳定后可重新评估。

## Consequences

- Windows 成为 MVP 的明确目标平台。
- 确认后需验证 PySide6 打包、可访问性和候选解析库的兼容性。
- 浏览器 UI 只能作为未来替代宿主，不能改变核心合同。
