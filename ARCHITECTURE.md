# Architecture

## 状态

本文记录已实现的 MVP 架构。

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
  -> Markdown renderer + asset exporter
  -> staging output writer + conversion report
```

## 数据边界

- 输入：用户明确选取的单个本地文件。
- 临时数据：仅在项目配置的临时目录中存在，转换结束后清理。
- 输出：用户选择的本地目录；包含 Markdown、资源和报告。
- 网络：MVP 运行时不发起外部网络请求。

## 实际技术栈

- Python 3.12：解析、转换核心、文件安全与桌面运行时。
- Tkinter（Python 标准库）：Windows 原生文件和目录选择、状态与错误入口。
- `python-docx 1.2.0`、`python-pptx 1.0.2`、`openpyxl 3.1.5`：三类 OOXML 输入适配器。
- PyInstaller 6.22.2：生成 Windows 分发目录。

桌面 UI 直接调用应用服务，不在 MVP 中建立本地 HTTP API；这样既避免浏览器目录权限限制，也减少文件内容经由请求层复制的路径。

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
  content.md | slides.md | sheets/
  assets/
  conversion-report.md
  source-manifest.json
```

## 待验证技术

- 复杂 Word 浮动对象、PPT 多栏/组合形状、图表和 Excel 多区域表仍采用报告降级策略。
- PPT 阅读顺序排序规则与 Excel 大工作表的性能阈值仍需真实样本确定。
