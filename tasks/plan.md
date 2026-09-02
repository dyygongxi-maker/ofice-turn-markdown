# 实施计划：v0.3 知识库归档增强版

## 概览

本计划在 v0.2 单文件转换 MVP 上增加批量归档、结果页、可选 Obsidian 元数据和复杂文档兼容性。实施以小的垂直切片进行；每一步均保持默认单文件输出兼容，不引入网络或数据库。

## 架构决策

- 单文件 `ConversionService` 保留为唯一的解析、暂存、原子发布入口。
- `BatchConversionService` 顺序复用单文件服务；队列状态与 UI 分离。
- Obsidian 功能通过 `ConversionOptions` 选择性启用，默认关闭。
- 兼容性改进以能力矩阵和无敏感样本回归驱动。

## 依赖关系

```text
Task 1 合同
  -> Task 2 Obsidian 单文件切片
  -> Task 3 扫描与批服务
  -> Task 4 结果聚合与报告
  -> Task 5 桌面队列与结果页
  -> Task 6 样本能力矩阵
  -> Tasks 7-9 格式增强
  -> Task 10 发布验收
```

## 任务列表

### 阶段 1：合同与单文件选项

## Task 1：定义批量与归档数据合同

**Description：** 在领域模型中定义转换选项、批项状态、稳定错误代码和向后兼容的报告/清单字段。

**Acceptance criteria：**
- [ ] 未传入选项时，v0.2 输出内容和路径保持不变。
- [ ] 状态、错误和警告使用可测试的稳定代码。
- [ ] 新模型不依赖 Tkinter 或 OOXML 解析库。

**Verification：** 模型和默认输出回归测试通过。

**Dependencies：** 无。
**Files likely touched：** `src/office_to_markdown/models.py`、`markdown.py`、`service.py`、`tests/test_conversion.py`。
**Estimated scope：** M。

## Task 2：实现 Obsidian 单文件归档选项

**Description：** 为单文件输出添加经验证的 frontmatter、标签和相对来源链接，保留默认模式。

**Acceptance criteria：**
- [ ] YAML 可解析，用户文本不会破坏 YAML 结构。
- [ ] 输出中不存在绝对原路径。
- [ ] 原文件复制默认关闭，开启时受控写入输出。

**Verification：** YAML、标签校验、相对链接、默认兼容和路径泄露测试通过。

**Dependencies：** Task 1。
**Files likely touched：** `models.py`、`markdown.py`、`service.py`、`security.py`、`tests/test_conversion.py`。
**Estimated scope：** M。

### 检查点：阶段 1

- [ ] 全部既有测试与新选项测试通过。
- [ ] Obsidian 模式输出可在隔离目录中解析，默认输出无变化。

### 阶段 2：批量归档闭环

## Task 3：实现文件夹扫描与顺序批处理服务

**Description：** 建立无 UI 的扫描、冲突跳过和批处理服务，逐项复用单文件转换。

**Acceptance criteria：**
- [ ] 扫描规则仅接收支持扩展名，递归默认关闭。
- [ ] 部分失败和输出冲突不阻塞其他项。
- [ ] 取消只在下一项开始前生效并有确定状态。

**Verification：** 目录扫描、部分失败、冲突、取消边界与清理测试通过。

**Dependencies：** Task 1。
**Files likely touched：** `service.py`、新增 `batch.py`、`models.py`、`security.py`、新增批处理测试。
**Estimated scope：** M。

## Task 4：实现批处理结果聚合与报告

**Description：** 生成可审阅的批处理汇总，连接每个成功结果的受控输出和报告路径。

**Acceptance criteria：**
- [ ] 各状态计数与明细完全一致。
- [ ] 失败内容不进入报告。
- [ ] 报告引用仅限本次生成的受控路径。

**Verification：** 汇总结构、状态计数和隐私回归测试通过。

**Dependencies：** Task 3。
**Files likely touched：** `markdown.py`、新增 `batch.py`、测试文件。
**Estimated scope：** S。

## Task 5：改造桌面队列与结果页

**Description：** 在 Tkinter 中接入多选、文件夹、后台进度、取消和结果操作。

**Acceptance criteria：**
- [ ] 转换不阻塞主线程，所有 UI 更新在主线程执行。
- [ ] 用户可查看队列、进度、汇总和每项结果。
- [ ] 打开操作仅允许本次输出目录与报告。

**Verification：** 手工批量流程、线程事件单元测试和 Windows 桌面冒烟测试通过。

**Dependencies：** Task 3、Task 4。
**Files likely touched：** `app.py`、新增 UI 控制器模块、批处理模块、测试。
**Estimated scope：** M。

### 检查点：阶段 2

- [ ] 混合成功、警告、失败和冲突的批处理可完整结束。
- [ ] 默认单文件流程仍可用。

### 阶段 3：兼容性回归

## Task 6：建立能力矩阵与脱敏回归样本

**Description：** 以合成或经授权的脱敏文件建立格式能力、允许降级、预期警告和结构断言。

**Acceptance criteria：**
- [ ] 每种格式覆盖基础与复杂案例，样本不含私人内容。
- [ ] 每项能力有支持等级、预期结构或警告。
- [ ] 样本清单与验证日志同步更新。

**Verification：** 清单校验、样本审阅和自动化结构断言通过。

**Dependencies：** Task 1。
**Files likely touched：** `tests/fixtures/`、`docs/sample-validation-log.md`、`docs/problems.md`、测试。
**Estimated scope：** M。

## Task 7：增强 DOCX 语义提取

**Description：** 按能力矩阵增加超链接、多级列表、复杂表格与图片顺序支持或明确降级。

**Acceptance criteria：**
- [ ] 每项新增能力有样本与回归断言。
- [ ] 浮动和不可稳定元素产生警告，不静默丢失。

**Verification：** DOCX 样本和默认回归测试通过。

**Dependencies：** Task 6。
**Files likely touched：** `adapters.py`、`markdown.py`、DOCX fixtures/tests。
**Estimated scope：** M。

## Task 8：增强 PPTX 阅读顺序与降级检测

**Description：** 针对两栏、重叠、组合形状、备注和表格改进提取或发出稳定警告。

**Acceptance criteria：**
- [ ] 不把坐标排序表述为视觉顺序保证。
- [ ] 歧义案例可复现并产生预期警告。

**Verification：** PPTX fixtures 的结构和警告断言通过。

**Dependencies：** Task 6。
**Files likely touched：** `adapters.py`、PPTX fixtures/tests。
**Estimated scope：** M。

## Task 9：增强 XLSX 结构降级策略

**Description：** 对隐藏行列、多区域表、合并单元格与公式缓存建立可预测的输出和报告。

**Acceptance criteria：**
- [ ] 不计算或伪造公式结果。
- [ ] 不支持布局有稳定警告和可读降级输出。

**Verification：** XLSX fixtures 的结构、警告和性能边界测试通过。

**Dependencies：** Task 6。
**Files likely touched：** `adapters.py`、`markdown.py`、XLSX fixtures/tests。
**Estimated scope：** M。

### 阶段 4：发布验收

## Task 10：执行完整回归与 Windows 分发验收

**Description：** 在新功能完成后执行安全、功能和打包验证。

**Acceptance criteria：**
- [ ] 全部自动化测试、静态检查和打包完成。
- [ ] 新构建产物可在 Windows 离线启动并完成批量转换。
- [ ] 文档、能力矩阵和变更记录反映真实交付状态。

**Verification：** `pytest`、`ruff check .`、`scripts/build.ps1` 与手工冒烟测试。

**Dependencies：** Task 2、Task 5、Task 7、Task 8、Task 9。
**Files likely touched：** `scripts/build.ps1`、项目文档、测试。
**Estimated scope：** M。

## 风险与缓解

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 大批量任务的资源占用 | 高 | 顺序执行、限制与可取消边界 |
| YAML 或链接注入 | 高 | 受控序列化、输入校验、路径包含检查 |
| 复杂布局错误归档 | 高 | 能力矩阵、稳定警告、样本回归 |
| UI 线程错误 | 中 | 后台事件队列与主线程更新约束 |
