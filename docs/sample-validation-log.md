# 样本可行性验证日志

**状态：** 已建立基准；项目环境、基础自动化与 Windows 分发启动已验证
**更新日期：** 2026-09-02

## 运行环境事实

| 项目 | 状态 |
| --- | --- |
| 项目内 DOCX/PPTX/XLSX 样本 | 0 个 |
| Windows 构建 Python 环境 | 已验证：`.venv`，Python 3.12.13，Tcl/Tk 8.6；构建脚本显式分发 Tcl/Tk 资源 |
| 系统 `python` / `py` 命令 | 不可用 |
| Codex 受控 Python 运行时 | 可用，仅作环境探测，不作为项目依赖 |
| 探测到的候选库 | `python-docx 1.2.0`、`python-pptx 1.0.2`、`openpyxl 3.1.5` |
| 样本合同校验 | 通过：12 个计划样本，覆盖 DOCX、PPTX、XLSX |
| Windows 分发启动 | 通过：2026-09-01 实际启动最新 PyInstaller 产物并确认进程持续运行 |
| WPS 演示自动化 | 通过：本机 WPS 演示 COM 可创建并关闭；使用无敏感合成 PPTX 以 `SaveAs(..., 32)` 导出 PDF，并逐页导出 PNG |

## 样本登记

正式清单见 [`tests/fixtures/manifest.json`](../tests/fixtures/manifest.json)。每份样本验证后都必须增加一条记录，至少包含：输入 ID、解析库版本、必需元素结论、实际警告代码、未支持内容和可复现命令。

| 样本 ID | 状态 | 结果 |
| --- | --- | --- |
| 合成 DOCX、PPTX、XLSX 集成样本 | 通过 | 自动化测试验证基础转换、表格和公式缓存警告 |
| 全部 12 个回归样本 | 待扩展 | 当前只覆盖 MVP 基础路径，复杂样式与对象待补充 |

## 已完成的基准检查

- `manifest.json` 可由 Python 标准库解析。
- 清单包含 12 个计划样本，三种格式均被覆盖。
- 现有测试在临时目录生成合成 DOCX、PPTX、XLSX，并已通过基础端到端转换。
- 旧的 YAML 清单与引用已移除，避免引入未声明的 YAML 依赖。
- WPS 演示 COM 不兼容 PowerPoint 的 `ExportAsFixedFormat`；PDF 导出使用 WPS 兼容的 `SaveAs(..., 32)` 路径。该路径已作为默认视觉导出引擎实现，并完成无敏感合成 PPTX 端到端验证。

## 下一步门槛

1. 生成合成样本，或由用户提供已脱敏样本。
2. 对每个样本执行隔离解析尖峰，写入本日志和 `docs/problems.md`。
3. 在干净 Windows 环境继续验证分发目录及安装程序路径。
