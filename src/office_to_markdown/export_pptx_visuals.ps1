param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][string]$PdfName,
    [Parameter(Mandatory = $true)][bool]$ExportPng,
    [Parameter(Mandatory = $true)][bool]$ExportPdf
)

$ErrorActionPreference = "Stop"
$application = $null
$presentation = $null

try {
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    $application = New-Object -ComObject PowerPoint.Application
    $application.AutomationSecurity = 3
    $presentation = $application.Presentations.Open($Source, $true, $false, $false)

    if ($ExportPng) {
        $pages = Join-Path $OutputDirectory "pages"
        New-Item -ItemType Directory -Path $pages -Force | Out-Null
        foreach ($slide in $presentation.Slides) {
            $imageName = "slide-{0:D3}.png" -f $slide.SlideIndex
            $slide.Export((Join-Path $pages $imageName), "PNG", 1600, 900)
        }
    }

    if ($ExportPdf) {
        $presentation.ExportAsFixedFormat((Join-Path $OutputDirectory $PdfName), 2)
    }
}
finally {
    if ($presentation) {
        $presentation.Close()
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation)
    }
    if ($application) {
        $application.Quit()
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($application)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
