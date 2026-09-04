param(
    [string]$Python = ".venv-ui\Scripts\python.exe",
    [string]$Compiler = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BuildScript = Join-Path $PSScriptRoot "build.ps1"
$InstallerScript = Join-Path $ProjectRoot "installer\office-to-markdown.iss"

if (-not (Test-Path -LiteralPath $Compiler -PathType Leaf)) {
    throw "Inno Setup compiler was not found: $Compiler"
}

& $BuildScript -Python $Python
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& $Compiler $InstallerScript
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$Installer = Join-Path $ProjectRoot "release\廾匸转换-Setup-0.3.0.exe"
if (-not (Test-Path -LiteralPath $Installer -PathType Leaf)) {
    throw "Installer build completed without producing the expected setup executable."
}

Write-Output "Installer created: $Installer"
