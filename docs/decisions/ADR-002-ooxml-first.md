# ADR-002：MVP 仅支持标准 OOXML 格式

## Status

Accepted

## Date

2026-09-01

## Context

用户主要处理 DOCX、PPTX、XLSX 文件，且 WPS 能导出这些格式。WPS 原生格式与旧版二进制格式会增加平台依赖和兼容性复杂度。

## Decision

首版只接受 DOCX、PPTX、XLSX。解析器围绕 OOXML 建立，原生 WPS 和旧格式以后以独立输入适配器评估。

## Alternatives Considered

### 同时支持 WPS 原生格式

- 优点：覆盖更多输入。
- 缺点：可能依赖用户安装的 WPS、自动化接口和不可预测的版本兼容性。
- 结论：当前拒绝。

### 先转 PDF 再识别

- 优点：输入格式统一。
- 缺点：丢失 OOXML 中的结构信息，OCR 和布局分析会显著扩大范围。
- 结论：当前拒绝。

## Consequences

- UI 需要明确支持格式和用户的导出路径。
- 核心模型不能依赖某个特定 OOXML 库的对象，以便未来扩展输入适配器。
