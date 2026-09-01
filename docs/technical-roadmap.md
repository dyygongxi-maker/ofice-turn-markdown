# 技术路线：Office to Markdown

**状态：** MVP 已实现并通过基础验证
**日期：** 2026-09-01

## 1. 路线结论

推荐以 **Python 转换核心 + PySide6-Essentials Windows 原生桌面 UI** 构建 MVP。该选择直接满足纯本地运行、可靠的文件/目录选择和未来 Windows 分发需求，同时使解析与 UI 维持明确边界。

MVP 不建立云端、数据库或 HTTP API。转换记录只存在于当前进程和用户选择的输出目录中。

## 2. 方案比较

| 方案 | 优点 | 缺点 | 结论 |
| --- | --- | --- | --- |
| Python + PySide6-Essentials | 可随应用分发的 Qt Widgets、原生文件选择；适合离线与打包 | 增加约 77 MB 运行时 | 推荐 |
| FastAPI + 浏览器 UI | Web UI 开发快；未来 Web 服务可复用 | 输出目录写入受浏览器限制；多运行时 | 不适合当前流程 |
| Tauri + Web UI + Python sidecar | 现代桌面体验；未来跨平台潜力 | 双语言、进程通信和打包复杂度高 | 未来重新评估 |

## 3. 目标技术栈

| 层 | 候选 | 职责 |
| --- | --- | --- |
| 运行时 | Python 3.12 | 转换核心、文件操作、桌面运行时 |
| 桌面 UI | `PySide6-Essentials` | 文件/目录选择、结果与错误展示 |
| DOCX 适配器 | `python-docx` | 文本、段落、表格、图片和关系提取 |
| PPTX 适配器 | `python-pptx` | 幻灯片、形状、表格、图片与备注提取 |
| XLSX 适配器 | `openpyxl` | 工作表、单元格、合并区域和公式文本提取 |
| 输入防护 | ZIP/OOXML 检查与安全 XML 解析 | 类型、体积、压缩膨胀和宏风险控制 |
| 打包 | PyInstaller | 在验证完成后生成 Windows 安装/分发产物 |

库和版本在技术尖峰通过前均为候选，不应在公开界面中承诺支持范围。

## 4. 模块边界与合同

```text
ui/
  desktop/                -> presentation only
application/
  conversion_service.py   -> orchestration and progress
domain/
  models.py               -> normalized document contract
  warnings.py             -> stable warning codes
adapters/
  docx/ pptx/ xlsx/       -> read OOXML into domain models
renderers/
  markdown/               -> render domain models and reports
infrastructure/
  filesystem/             -> staging output, cleanup, atomic publish
```

核心合同在实现前先定义并测试：

```text
ConversionRequest
  source_path: Path
  output_parent: Path
  options: ConversionOptions

ConversionResult
  output_path: Path
  report_path: Path
  warnings: list[ConversionWarning]

NormalizedDocument
  blocks: ordered list[Block]
  assets: list[Asset]
  source_metadata: SourceMetadata
  warnings: list[ConversionWarning]
```

`Block` 使用显式类型区分标题、段落、列表、表格、图片、链接和幻灯片分隔，不让渲染器理解 OOXML 细节。警告使用稳定代码，例如 `PPTX_READING_ORDER_AMBIGUOUS`，报告文本可演进但代码保持可测试。

## 5. 关键数据流与安全控制

```text
selected source file
  -> validate extension, OOXML package, size and ZIP expansion
  -> parse without executing active content
  -> normalized document + warnings
  -> render Markdown and export static assets into staging directory
  -> write report and manifest
  -> validate output paths
  -> atomically publish final output directory
```

- 拒绝不匹配扩展名与 OOXML 内容的文件，限制压缩包解压后的总大小与条目数。
- 不执行宏、外部关系、嵌入脚本或链接目标；检测到宏和不支持对象时报告并按安全策略拒绝或跳过。
- 所有输出文件名由受控的安全名称生成，拒绝路径穿越和覆盖非空目录。
- 失败和取消时删除暂存目录；日志只保存错误代码、文件类型和统计数据，不保存正文。

## 6. 风险优先实施顺序

### 阶段 0：样本与可行性尖峰

建立至少 12 个脱敏或自行构造的输入样本，每类格式至少 4 个；为每个样本记录必需元素、允许降级和预期警告。

**通过条件：** 候选库能稳定读取目标元素，无法支持的元素可被检测或明确记录。

### 阶段 1：核心合同与 DOCX 垂直切片

实现统一模型、警告代码、暂存输出和 DOCX 基础转换，再通过一个桌面界面完成“选择文件 -> 选择目录 -> 转换 -> 打开输出”的闭环。

**通过条件：** DOCX 样本能够稳定输出 Markdown、图片和报告；失败不留下最终半成品目录。

### 阶段 2：PPTX 适配器

增加幻灯片、文本框、列表、表格、图片、备注和确定性阅读顺序；将歧义顺序与不支持对象写入报告。

**通过条件：** 所有 PPTX 样本均能得到可审核的页面分节与警告。

### 阶段 3：XLSX 适配器

增加工作簿索引、工作表文件、使用区域、单元格内容和公式文本；建立大表、合并单元格和缓存缺失的降级策略。

**通过条件：** XLSX 样本不伪造公式结果，表格和警告可重复生成。

### 阶段 4：可靠性与分发

补充输入恶意样本、取消/失败清理、回归测试、无网络运行检查和 Windows 打包验证。

**通过条件：** 目标 Windows 环境可离线运行，输出不会覆盖用户已有内容，所有回归样本通过。

## 7. 测试策略

- 单元测试：文档模型、Markdown 转义、文件名规范化、警告代码、输出目录事务。
- 适配器测试：每个样本的必需结构、资源数量、警告代码和 Markdown 片段。
- 集成测试：从文件输入到最终输出目录，覆盖成功、损坏、类型伪装、取消和输出冲突。
- 手工验收：在 Obsidian 打开输出，确认内部链接与相对图片路径可用。
- 安全测试：ZIP 膨胀、路径穿越、宏条目、外部关系与超大文件。

不以单一“文本数量”作为正确性判断；每个样本必须同时检查内容、结构、资源和警告。

## 8. 实施计划与审批门槛

实施任务详见 [计划](../tasks/plan.md) 与 [任务清单](../tasks/todo.md)。在以下条件前不得开始代码实现：

1. 用户确认 D-004 的桌面 UI 方案。
2. 至少每类一个真实或脱敏样本可用于可行性验证。
3. 候选库和 Python 版本通过技术尖峰，并记录实际限制。

## 9. 未来演进

核心合同保持文件系统和 UI 无关。后续可替换或新增 WPS 原生格式输入适配器、批量队列、PDF/OCR、Obsidian 模板或独立的云端产品，但这些功能不可修改已存在的 `ConversionResult` 基础语义或警告代码。
