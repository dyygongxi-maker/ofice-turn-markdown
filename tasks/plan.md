# 实施计划：Office to Markdown MVP

## 前提

本计划不授权实现。必须先确认 ADR-003，并准备每类至少一个可使用样本。

## 依赖关系

```text
sample baseline
  -> domain contract and output transaction
  -> DOCX vertical slice
  -> PPTX and XLSX adapters
  -> reliability hardening
  -> packaging
```

## 阶段与检查点

### 阶段 0：可行性

- 样本基准与预期输出。
- 候选解析库技术尖峰。

**检查点：** 确认 MVP 支持边界和实际解析限制。

### 阶段 1：DOCX 完整路径

- 统一模型与安全输出事务。
- DOCX 适配器、Markdown 渲染、报告与最小桌面流程。

**检查点：** DOCX 从选择到输出的端到端路径可用。

### 阶段 2：格式扩展

- PPTX 适配器。
- XLSX 适配器。

**检查点：** 三种格式均有回归样本和明确降级报告。

### 阶段 3：可靠性与发布

- 恶意输入、清理、冲突与无网络验证。
- Windows 打包和干净机器试运行。

**检查点：** 全部验收标准完成后才评估 MVP 发布。

## 风险与缓解

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| PPT 阅读顺序错误 | 高 | 先用样本验证坐标排序，报告歧义 |
| Excel 表格过大或多区域 | 中 | 建立限制和降级报告，不隐式截断 |
| OOXML 包恶意或损坏 | 高 | ZIP/路径/XML 限制与失败清理 |
| 打包后依赖失效 | 中 | 早期做最小打包尖峰，干净环境验证 |
