param([string]$Docx, [string]$Pdf)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $d = $word.Documents.Open((Resolve-Path $Docx).Path, $false, $true)
    $pages = $d.ComputeStatistics(2)
    $d.SaveAs([ref]$Pdf, [ref]17)
    $d.Close([ref]0)
    "pages=$pages"
} finally {
    $word.Quit()
}
