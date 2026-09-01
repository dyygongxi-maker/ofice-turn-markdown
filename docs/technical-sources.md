# 技术来源

- Qt for Python QFileDialog API：<https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QFileDialog.html>。技术评审曾使用该官方 API 验证原生文件/目录选择路线；最终 MVP 选择功能更小的 Tkinter 标准库壳。
- Python ZIP 文件处理：<https://docs.python.org/3/library/zipfile.html>。输入校验使用 `ZipFile` 检查 OOXML 包条目、总解压大小、路径和必需内部部件，不解压或执行文档活动内容。
- PyInstaller：<https://pyinstaller.org/en/stable/usage.html>。打包脚本使用 `--windowed`、`--paths src` 和独立入口生成 Windows 分发目录。

库的具体行为还由项目自动化测试覆盖；`requirements.lock` 记录本次验证环境的精确版本。
