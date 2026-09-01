param(
    [string]$Python = ".venv\\Scripts\\python.exe"
)

& $Python -m PyInstaller --noconfirm --clean --windowed --paths src --name OfficeToMarkdown src/office_to_markdown/__main__.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
