# Architecture

## 状态

本文记录已实现的 v0.3 架构及其演进边界。

## 架构原则

- 本地优先：文件内容只在用户设备上处理。
- 语义优先：输出面向知识检索和 AI，不追求页面像素级还原。
- 解析与输出解耦：所有格式适配器先生成统一中间文档模型，再由渲染器生成 Markdown。

## 目标模块

```text
Tkinter desktop UI
  -> application service
  -> input and archive validation
  -> OOXML adapter (DOCX | PPTX | XLSX)
  -> normalized document model
  -> Markdown renderer + asset exporter + optional WPS-first visual exporter
  -> staging output writer + conversion report
```

## 数据边界

- 输入：用户明确选取的单个本地文件。
- 临时数据：仅在项目配置的临时目录中存在，转换结束后清理。
- 输出：用户选择的本地目录；包含 Markdown、资源、报告，以及可选的 PPT 页面预览和 PDF。
- 网络：MVP 运行时不发起外部网络请求。

## 实际技术栈

- Python 3.13.9：项目 `.venv-ui` 的 Windows 构建运行时，包含 Tcl/Tk 8.6。
- Tkinter（Python 标准库）：Windows 原生文件和目录选择、状态与错误入口；构建脚本随 PyInstaller 分发 Tcl/Tk 资源。
- `python-docx 1.2.0`、`python-pptx 1.0.2`、`openpyxl 3.1.5`：三类 OOXML 输入适配器。
- PyInstaller 6.22.2：生成 Windows 分发目录。
- Inno Setup 6：将经过启动验证的 PyInstaller 分发目录封装为当前用户安装程序，负责开始菜单、可选桌面快捷方式与卸载注册。
- WPS 演示（默认）与 Microsoft PowerPoint（后备）：通过本机 COM 自动化只读打开 PPTX，导出页面 PNG 和 PDF。WPS 使用 `SaveAs(..., 32)` 导出 PDF；两类导出脚本均由 Windows PowerShell 以 STA 模式启动，不可用时降级为报告警告。

桌面 UI 直接调用应用服务，不在 MVP 中建立本地 HTTP API；这样既避免浏览器目录权限限制，也减少文件内容经由请求层复制的路径。

## Windows 安装包

```text
scripts/build.ps1
  -> dist/廾匸转换/                 # 可运行目录包
  -> installer/office-to-markdown.iss
  -> release/廾匸转换-Setup-0.3.0.exe
  -> %LocalAppData%/Programs/廾匸转换/ # 安装后的当前用户应用
```

`scripts/package-installer.ps1` 是唯一的正式安装包入口：它先重建分发目录，再调用 Inno Setup 编译器。`assets/app-icon.ico` 由 `scripts/create-icon.py` 生成，并同时嵌入 PyInstaller 可执行文件和 Inno Setup 安装程序。`dist/` 与 `release/` 都是可再生发布产物，必须保持 Git 忽略。

## 关键合同

```text
ConversionRequest(source_path, output_parent, options)
  -> ConversionResult(output_path, report_path, warnings)

OOXML adapter
  -> NormalizedDocument(blocks, assets, source_metadata, warnings)
```

适配器不直接写文件，渲染器不读取 OOXML，UI 不处理文档内容。输出先写入同级临时目录，全部成功后才原子性地改名为最终目录。

## 预期输出结构

```text
<source-name>-markdown/
  index.md
  markdown/
    <source-name>.md
    sheets/                  # 仅 XLSX：每个工作表一个 Markdown
  reports/
    <source-name>转换报告.md
  visuals/                  # 仅按需导出的 PPTX 视觉预览
    pages/slide-001.png
    <source-name>.pdf
  assets/
  source-manifest.json
```

## 待验证技术

- 复杂 Word 浮动对象、PPT 多栏/组合形状、图表和 Excel 多区域表仍采用报告降级策略。
- PPT 阅读顺序排序规则与 Excel 大工作表的性能阈值仍需真实样本确定。

## v0.3 规划演进

```text
Tkinter 主线程
  -> 队列控制器和线程安全事件队列
  -> BatchConversionService（顺序处理）
  -> ConversionService（现有单文件事务）
  -> adapters -> normalized document -> renderer / report
```

- `ConversionService` 保持单文件解析、暂存与原子发布边界；批处理服务只负责扫描、调度、状态和汇总。
- 新增 `ConversionOptions` 承载可选 Obsidian 输出，不改变默认 Markdown 协议。
- UI 不直接访问解析器；后台线程只回传事件，所有 Tkinter 控件在主线程更新。
- 桌面界面使用 Windows 原生标题栏提供窗口缩放、吸附和窗口控制；导入卡、输出规则卡、文件行和底部操作栏由 Tkinter Canvas 呈现，输入框以 Canvas 嵌入原生 Entry 保持文本输入能力。队列状态由 `BatchStatus` 映射为自绘的状态胶囊和进度条，不改变领域状态合同。
- 默认 `1280x800` 布局将输出规则组织为左右两栏，队列使用独立的 `tk.Canvas` 视口并配套滚动条，底部操作栏固定；卡片高度与操作栏位置由响应式几何约束计算，并由源码回归断言保护，避免文件行覆盖操作按钮。
- 主 Canvas 仅在尺寸变化或悬停项变化时全量重绘，队列滚动只重绘队列 Canvas；按钮、复选框和文件行提供悬停颜色反馈与选中高亮，提升交互可读性。
- YAML 和来源链接必须使用受控序列化与相对路径校验，报告、清单和 UI 不得暴露绝对输入路径。

详细路线见 [docs/technical-roadmap.md](docs/technical-roadmap.md)。

## 计划中的桌面 UI 重构

本节描述已确认但尚未实施的目标结构，不代表当前源码已经完成迁移。

```text
office_to_markdown.app（兼容入口）
  -> ui.main_window（窗口编排与任务生命周期）
      -> ui.state（UI 状态与领域选项映射）
      -> ui.queue_panel（有序文件队列与结果动作）
      -> ui.settings_panel（输出与可选转换设置）
      -> ui.status_bar（状态摘要、开始与取消）
      -> ui.theme（ttk 视觉令牌）
  -> BatchConversionService（保持现有顺序处理合同）
```

目标实现保留 Tkinter/Tcl-Tk 和现有发布链，以原生 Tk/ttk 控件替换主要 Canvas 命中区；Canvas 只用于原生控件无法合理表达的轻量视觉。UI 仍通过线程安全队列接收后台事件，所有 Tk 控件只在主线程更新。领域模型、转换服务、文件安全校验和输出协议不变。

完整边界、状态矩阵和验收条件见 [docs/ui-redesign-spec.md](docs/ui-redesign-spec.md)，任务依赖见 [tasks/ui-redesign-plan.md](tasks/ui-redesign-plan.md)。
