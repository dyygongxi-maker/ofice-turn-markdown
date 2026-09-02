# 技术路线：v0.3 知识库归档增强版

**状态：** 已规划，尚未实现
**日期：** 2026-09-01

## 1. 技术结论

保持现有 Python 转换核心与 Tkinter 本地桌面 UI，不增加数据库、HTTP API 或网络依赖。下一阶段新增批处理应用服务与输出选项，单文件转换仍是唯一负责解析、暂存和原子发布的底层合同。

首版队列采用单工作线程顺序执行。它比并发实现更容易解释输出冲突、取消边界和文件资源占用；只有样本验证显示性能不足时才评估有限并发。

## 2. 目标架构

```text
Tkinter 主线程
  -> 队列控制器 / 线程安全事件队列
  -> 后台 BatchConversionService（顺序）
  -> ConversionService（单文件校验、解析、暂存、原子发布）
  -> OOXML adapters -> ParsedDocument -> Markdown renderer / report / manifest
```

Tkinter 控件只能在主线程更新；后台线程只发布进度事件。适配器不感知队列、UI 或 Obsidian 路径规则。

## 3. 合同演进

在 `models.py` 中新增不可变选项与批处理模型：

```text
ConversionOptions
  obsidian_mode: bool
  tags: tuple[str, ...]
  include_frontmatter: bool
  include_source_link: bool
  source_link_root: Path | None
  copy_source: bool

BatchItem
  source_path, status, result, error_code, error_message

BatchResult
  items, started_at, completed_at
```

`ConversionService.convert(source, output_parent, options)` 保持单文件边界；没有选项时输出与 v0.2 保持兼容。新增 `BatchConversionService` 循环调用该服务，不能把批处理逻辑放入 OOXML 适配器或 UI。

报告和 `source-manifest.json` 扩展为记录转换选项摘要、稳定警告代码和批处理项状态，但不记录正文、绝对原路径或其他隐私数据。

## 4. Obsidian 实现约束

- 用受控序列化函数生成 YAML，不能拼接未校验的用户文本。
- 标签限制字符集、长度与数量；非法标签在转换前拒绝并给出明确错误。
- 相对链接先解析并验证在用户指定根目录内；绝不写入绝对路径。
- `safe_name()` 的 ASCII 文件名策略继续保护输出路径；中文工作表/文件名的可读性改进必须以映射清单和冲突测试实现，不能直接放宽路径安全规则。
- 原文件复制为显式选择，默认关闭；复制时仍经受控输出路径写入。

## 5. 兼容性策略

先建立能力矩阵和回归样本，再逐项实现。每次改进遵循：检测 -> 保留可表达内容 -> 对不可表达部分给稳定警告 -> 通过结构与报告断言验证。不得以推测的视觉顺序、公式结果或图表内容替代来源数据。

PPTX 的形状坐标排序仍仅是确定性降级策略，不是阅读顺序保证；两栏、重叠与组合形状要有专门样本和歧义警告。XLSX 不计算公式，只报告缓存可用性。

## 6. 实施顺序

1. 定义选项、批处理状态、错误代码和报告/清单兼容性合同。
2. 为单文件转换实现 Obsidian frontmatter、标签和相对来源链接，并保持默认输出不变。
3. 实现不含 UI 的目录扫描与顺序批处理服务，覆盖部分失败、冲突、取消边界。
4. 汇总批处理结果和报告。
5. 改造 Tkinter：多选、文件夹、队列表、进度、取消和结果操作。
6. 建立脱敏回归样本矩阵和能力合同。
7. 以 DOCX、PPTX、XLSX 的小切片依次提升兼容性。
8. 最后执行完整测试、Windows 打包和干净环境验收。

详细任务、依赖和检查点见 [实施计划](../tasks/plan.md) 与 [任务清单](../tasks/todo.md)。

## 7. 主要风险

| 风险 | 缓解 |
| --- | --- |
| 大目录或复杂文件导致界面无响应 | 后台顺序线程、进度事件、文件数量/大小限制与可取消边界 |
| 元数据或链接泄露本地路径 | 只允许校验后的相对路径，自动化扫描输出中绝对路径 |
| 输出冲突或中途失败损坏归档 | 复用单文件暂存/原子发布，默认跳过冲突 |
| 复杂布局被错误表述为已转换 | 能力矩阵、稳定警告代码和真实样本回归 |
