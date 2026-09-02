param(
    [string]$Python = ".venv-ui\\Scripts\\python.exe"
)

$ErrorActionPreference = "Stop"

$Base = & $Python -c "import sys; print(sys.base_prefix)"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Base)) {
    throw "Unable to locate the Python runtime used for the Windows build."
}
$AppName = "$([char]0x5EFE)$([char]0x5338)$([char]0x8F6C)$([char]0x6362)"
& $Python -m PyInstaller --noconfirm --clean --windowed --paths src --name OfficeToMarkdown `
    --add-data "$Base\tcl;tcl" `
    --add-data "$Base\Lib\tkinter;tkinter" `
    --add-data "src\office_to_markdown\export_pptx_visuals.ps1;office_to_markdown" `
    --add-data "src\office_to_markdown\export_wps_pptx_visuals.ps1;office_to_markdown" `
    --hidden-import tkinter `
    --collect-all lxml `
    --add-binary "$Base\DLLs\_tkinter.pyd;." `
    --add-binary "$Base\DLLs\tcl86t.dll;." `
    --add-binary "$Base\DLLs\tk86t.dll;." `
    src/launcher.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BuiltPath = Join-Path $ProjectRoot "dist\\OfficeToMarkdown"
$ReleasePath = Join-Path (Join-Path $ProjectRoot "dist") $AppName
if (Test-Path -LiteralPath $ReleasePath) {
    Remove-Item -LiteralPath $ReleasePath -Recurse -Force
}
Move-Item -LiteralPath $BuiltPath -Destination $ReleasePath
Rename-Item -LiteralPath (Join-Path $ReleasePath "OfficeToMarkdown.exe") -NewName "$AppName.exe"
