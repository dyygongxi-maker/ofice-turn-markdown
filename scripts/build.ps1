param(
    [string]$Python = ".venv\\Scripts\\python.exe"
)

$venvRoot = Split-Path -Parent (Split-Path -Parent (Resolve-Path $Python))
$shibokenRuntime = Join-Path $venvRoot "Lib\site-packages\shiboken6\shiboken6.abi3.dll"
if (-not (Test-Path -LiteralPath $shibokenRuntime)) {
    throw "Missing shiboken6 runtime: $shibokenRuntime"
}

& $Python -m PyInstaller --noconfirm --clean --windowed --paths src --name OfficeToMarkdown `
    --add-binary "$shibokenRuntime;PySide6" src/launcher.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
