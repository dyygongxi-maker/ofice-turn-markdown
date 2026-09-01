# MVP 任务清单

## 阶段 0：可行性

- [x] Task 1：建立脱敏样本基准与预期元素清单。
  - Acceptance：每类 OOXML 至少 4 个样本，包含正常与异常元素。
  - Verify：人工审阅样本登记，确认无敏感正文或私人数据。
  - Dependencies：无。

- [x] Task 2：完成候选解析库技术尖峰。
  - Acceptance：能记录每类样本的可读取元素、缺口和异常。
  - Verify：运行隔离尖峰并将结果写入 `docs/problems.md`。
  - Dependencies：Task 1。

## 阶段 1：DOCX 完整路径

- [x] Task 3：定义域模型、警告代码和暂存输出事务。
  - Acceptance：合同独立于 UI 与 OOXML 库；失败不发布最终目录。
  - Verify：单元测试覆盖路径冲突、清理和警告序列化。
  - Dependencies：Task 2。

- [x] Task 4：实现 DOCX 到 Markdown 的垂直切片。
  - Acceptance：标题、段落、列表、简单表格和图片可转换并有报告。
  - Verify：DOCX 回归样本与桌面手工流程通过。
  - Dependencies：Task 3。

## 阶段 2：格式扩展

- [x] Task 5：实现 PPTX 适配器和阅读顺序警告。
  - Acceptance：幻灯片、文本、图片、表格和备注有确定性输出。
  - Verify：PPTX 回归样本与歧义顺序用例通过。
  - Dependencies：Task 3。

- [x] Task 6：实现 XLSX 适配器和公式降级报告。
  - Acceptance：工作表文件、使用区域、公式文本和警告可生成。
  - Verify：XLSX 回归样本覆盖合并单元格和缓存缺失。
  - Dependencies：Task 3。

## 阶段 3：可靠性与发布

- [x] Task 7：完成输入防护、取消/失败清理和无网络验证。
  - Acceptance：恶意或损坏输入失败安全，日志不含正文。
  - Verify：安全集成测试和本地网络阻断手工检查。
  - Dependencies：Task 4、Task 5、Task 6。

- [x] Task 8：完成 Windows 打包尖峰与干净环境试运行。
  - Acceptance：可在目标 Windows 环境离线打开并完成一次 DOCX 转换。
  - Verify：打包产物手工验收和安装日志审查。
  - Dependencies：Task 7。
