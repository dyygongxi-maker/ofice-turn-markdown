# 廾匸转换

在 Windows 本机将 Word、PowerPoint 和 Excel 的标准 OOXML 文件转换为适合知识库与 AI 阅读的 Markdown。

项目提供本地 Windows MVP；文件不会上传到网络。

## Quick Start

```powershell
.\.venv-ui\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv-ui\Scripts\python.exe -m office_to_markdown
```

选择一个 `.docx`、`.pptx` 或 `.xlsx` 文件和一个已有的空输出父目录。工具会创建同名的 `-markdown` 输出目录；正文位于 `markdown/<文件名>.md`，报告位于 `reports/<文件名>转换报告.md`。XLSX 还会在 `markdown/sheets/` 下保留逐工作表文件。

处理 PPTX 时，可勾选“PPT 导出每页 PNG”或“PPT 导出版式 PDF”。导出结果分别位于 `visuals/pages/` 和 `visuals/<文件名>.pdf`。程序优先使用本机 WPS 演示，失败时尝试 Microsoft PowerPoint；两者都不可用时 Markdown 仍会生成，报告会记录警告。

## Commands

```powershell
.\.venv-ui\Scripts\python.exe -m pytest --basetemp .\work\pytest -p no:cacheprovider
.\.venv-ui\Scripts\python.exe -m ruff check .
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

## Windows 安装包

在已安装 Inno Setup 6 的 Windows 构建机上运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\package-installer.ps1
```

生成的单文件安装程序位于 `release\廾匸转换-Setup-0.3.0.exe`。安装默认只作用于当前 Windows 用户，安装到 `%LocalAppData%\Programs\廾匸转换`；安装向导会创建开始菜单入口，并可选创建桌面快捷方式，系统“已安装的应用”中可卸载。

## 文档

- [产品设计](docs/product-design.md)
- [技术路线](docs/technical-roadmap.md)
- [目标架构](ARCHITECTURE.md)
- [技术决策](DECISIONS.md)

## 计划中的验证

自动化测试覆盖基础 DOCX、PPTX、XLSX、公式缓存警告、格式伪装、宏包拒绝和输出冲突。复杂版式仍应使用真实或脱敏样本补充回归验证。

样本合同与当前状态见 [样本基准](tests/fixtures/README.md) 和 [验证日志](docs/sample-validation-log.md)。Windows 构建使用已验证的项目 `.venv-ui`（Python 3.13，含 Tcl/Tk）；依赖声明见 `pyproject.toml`，当前验证版本见 `requirements.lock`。
