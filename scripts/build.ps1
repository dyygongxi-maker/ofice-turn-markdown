param(
    [string]$Python = ".venv-tk\\Scripts\\python.exe"
)

& $Python -m PyInstaller --noconfirm --clean --windowed --paths src --name 廾匸转换 src/launcher.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
