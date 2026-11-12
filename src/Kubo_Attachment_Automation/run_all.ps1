param([switch]$RetryRefused)
Set-Location $PSScriptRoot
$p = "$PSScriptRoot\.env"
if ((Get-Content $p -Raw) -notmatch "SL_COMPANY_DB='IAL01_DEV'") { Write-Host "STOP: the company is not IAL01_DEV"; exit 1 }
if ($RetryRefused) { Copy-Item refused_memory.json refused_memory.json.keep -ErrorAction SilentlyContinue; Remove-Item refused_memory.json -ErrorAction SilentlyContinue }
& "$PSScriptRoot\venv\Scripts\python.exe" run_kubo.py
