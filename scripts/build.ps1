param(
    [string]$Python = ".venv-tk\\Scripts\\python.exe"
)

& $Python -m PyInstaller --noconfirm --clean --windowed --paths src --name OfficeToMarkdown src/launcher.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
