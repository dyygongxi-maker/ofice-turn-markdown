# Office to Markdown

在 Windows 本机将 Word、PowerPoint 和 Excel 的标准 OOXML 文件转换为知识库与 AI 可读的 Markdown。

项目提供本地 Windows MVP；文件不会上传到网络。

## Quick Start

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m office_to_markdown
```

选择一个 `.docx`、`.pptx` 或 `.xlsx` 文件和一个已有的空输出父目录。工具会创建同名的 `-markdown` 输出目录。

## Commands

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

## 文档

- [产品设计](docs/product-design.md)
- [技术路线](docs/technical-roadmap.md)
- [目标架构](ARCHITECTURE.md)
- [技术决策](DECISIONS.md)

## 计划中的验证

自动化测试覆盖基础 DOCX、PPTX、XLSX、公式缓存警告、格式伪装、宏包拒绝和输出冲突。复杂版式仍应使用真实或脱敏样本补充回归验证。

样本合同与当前状态见 [样本基准](tests/fixtures/README.md) 和 [验证日志](docs/sample-validation-log.md)。项目已包含独立 `.venv`；依赖声明见 `pyproject.toml`，当前验证版本见 `requirements.lock`。
