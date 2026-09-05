# Changelog

## [Unreleased]

### Added

- Added a project-owned Windows application icon for the executable, installer, and generated shortcuts.

### Removed

- Removed obsolete incorrectly encoded Windows build directories and generated spec files from earlier releases.

### Changed

- 桌面界面迁移为模块化 Tkinter/ttk 双栏工作台，使用原生队列、设置和底部执行控件，保留原有本地批量转换流程。
- 重新设计桌面主界面：输出规则改为左右两栏，队列使用独立可滚动视口，底部操作栏固定，文件多时不会遮挡按钮。
- 按钮、复选框和文件行新增悬停颜色反馈；选中文件显示高亮背景。
- 进度条在转换中显示动态条纹；鼠标在主 Canvas 上移动时不再全量重绘，仅在悬停项变化时重绘。

### Added

- 新增交互测试覆盖 1280×800 默认布局、最小尺寸重绘、队列滚动、文件选中、悬停反馈、复选框状态、开始/取消处理以及打开输出/报告的按钮禁用状态。
- 新增与绘制坐标无关的 UI 契约测试，覆盖转换选项、队列去重顺序和受控结果打开行为。
- 新增 UI 状态与 ttk 主题模块，为工作台界面提供集中状态和视觉令牌。
- 新增 `QUEUE_ROW_HEIGHT` 与 `BOTTOM_BAR_HEIGHT` 布局常量，1280×800 默认尺寸下队列卡片与底部操作栏无重叠。
- 新增桌面工作台 UI 重构规格、分阶段技术路线和 Codex 执行清单；当前仅完成规划，尚未修改应用界面。

### Fixed

- Desktop and Start menu shortcuts now use the separately installed application icon, avoiding stale executable icon caching in Windows Explorer.
- 使用 Windows 原生标题栏替换无边框自绘窗口控制，修复窗口无法可靠缩放、最大化和吸附的问题。
- 文件夹扫描现在默认不包含子文件夹，避免选择上级目录时意外将大量 Office 文件加入队列；用户仍可按需启用递归扫描。

## [0.3.0] - 2026-09-04

### Added

- 重新设计本地桌面界面：以“导入文件、输出规则、待处理文件、开始处理”的单页连续流程替换此前的双栏工作台，并保留队列数量提示与状态语义颜色。
- 按 Windows 参考设计实现自绘主界面：40px 标题栏、指定颜色与圆角令牌、PPTX 视觉附件说明、演示队列、文件类型徽章、状态胶囊和进度条。
- Windows 正式安装包：Inno Setup 单文件安装器，包含开始菜单、可选桌面快捷方式、当前用户安装位置和卸载入口。

### Changed

- Windows 构建与开发默认环境改为 `.venv-ui`（Python 3.13、Tcl/Tk 8.6），修复既有 `.venv` 无法创建 Tkinter 窗口的问题。
- 优化 `1280x800` 主界面布局：输出规则改为两列紧凑排列，视觉附件选项恢复到卡片内，四条队列与底部操作栏不再重叠。
- 首次启动改为真实空队列，不再展示虚构文件、进度或警告；Obsidian、原文件链接和 PPTX 图片导出改为默认关闭，空标签在启用 Obsidian 时自动采用 `office-import`。

- WPS 演示优先的 PPTX 视觉导出：使用 WPS 自动化生成每页 PNG 与 PDF，并在失败时回退至 PowerPoint。
- 批量文件/文件夹队列、冲突跳过、部分失败隔离、取消边界和结果汇总。
- 可选 Obsidian frontmatter、标签校验、相对来源链接与原文件复制。
- 桌面队列表、后台转换和受控打开输出/报告操作。
- 可选 PPTX 视觉导出：每页 PNG、整份版式 PDF 及索引链接，统一放入 `visuals/`。

### Fixed

- Windows 构建脚本改为失败即停止，并验证 Python 运行时路径，避免发布目录替换失败时静默保留旧版本。
- 发布包显式收集 `lxml` 原生扩展，修复安装后启动时 `cannot import name etree from lxml` 的崩溃。

- 视觉导出 PowerShell 子进程现在强制使用 STA COM 套间启动，满足 PowerPoint 自动化的线程模型要求。
- 显式分发 Tcl/Tk 数据、DLL 与 `_tkinter` 扩展；最新 Windows exe 已实际启动验证。
- PPTX 中无内嵌数据的链接图片现在会记录 `PPTX_LINKED_IMAGE_UNSUPPORTED` 警告并继续转换，不再使整份文件失败。
- Windows PowerShell 下的中文 PyInstaller `--name` 参数编码问题：内部使用 ASCII 构建名，再安全发布为“廾匸转换”目录和 exe。

### Verified

- 使用真实 PPTX 在隔离目录验证视觉导出降级路径：受限命令行会话无法创建 PowerPoint COM 实例时，Markdown 转换仍完成，不保留失效 `visuals/` 目录，并报告 `PPTX_VISUAL_EXPORT_FAILED`；验证产物已删除。

### Changed

- 产品显示名称调整为“廾匸转换”；桌面界面、校验提示、转换输出和正式文档改为中文。
- Windows 分发文件名调整为 `廾匸转换.exe`；内部 Python 包名、输出文件名和 JSON 字段保持稳定。
- 转换正文统一存入 `markdown/<文件名>.md`，转换报告存入 `reports/<文件名>转换报告.md`；XLSX 额外保留 `markdown/sheets/` 的逐工作表文件。

### Fixed

- 将桌面 UI 从无法由当前环境打包的 Tkinter 替换为 `PySide6-Essentials`，修复 Windows 分发应用启动时的相对导入和 Tcl/Tk 运行时缺失问题。
- 将 `shiboken6.abi3.dll` 收集到 `PySide6` 目录，修复 Windows 分发应用加载 `QtWidgets` 时的 DLL 解析失败。
- 放弃不稳定的 Qt 分发链，改用完整 Python 3.13 Tcl/Tk 环境构建 Tkinter 分发应用，修复 Windows 启动失败。

### Added

- 技术路线、风险优先实施计划与任务清单。
- 样本基准清单、样本数据规则与验证日志。

### Changed

- 确认原生桌面 UI 方案，进入样本基准与可行性验证阶段。

## [0.2.0] - 2026-09-01

### Added

- 本地 Tkinter 桌面应用，支持选择 DOCX、PPTX、XLSX 和输出目录。
- 安全 OOXML 包校验、原子输出发布、Markdown/资源/报告/清单生成。
- DOCX、PPTX、XLSX 转换器及 6 项自动化安全和集成测试。
- 本地虚拟环境配置、依赖锁定和 PyInstaller Windows 打包脚本。

### Security

- 拒绝扩展名伪装、宏条目、异常 ZIP 路径、超限包和已有输出目录覆盖。

## [0.1.0] - 2026-09-01

### Added

- 创建项目基础文档和产品设计。
- 记录本地优先、OOXML 优先与语义化输出的初始决策。

### Notes

- 本版本仅完成设计，尚未实现可运行的转换功能。
