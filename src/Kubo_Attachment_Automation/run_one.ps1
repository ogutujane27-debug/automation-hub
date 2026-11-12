param([Parameter(Mandatory=$true)][string]$DocNum)
Set-Location $PSScriptRoot
$p = "$PSScriptRoot\.env"
function SetPin($v) { $t = [IO.File]::ReadAllText($p) -replace "(?m)^KUBO_ONLY_DOCNUM=.*", "KUBO_ONLY_DOCNUM='$v'"; [IO.File]::WriteAllText($p, $t, (New-Object Text.UTF8Encoding $false)) }
if ((Get-Content $p -Raw) -notmatch "SL_COMPANY_DB='IAL01_DEV'") { Write-Host "STOP: the company is not IAL01_DEV"; exit 1 }
if ($DocNum -notmatch '^[0-9, ]+$') { Write-Host "STOP: give delivery numbers only, e.g. 25219635 or 25221401,25205409"; exit 1 }
try { SetPin $DocNum; & "$PSScriptRoot\venv\Scripts\python.exe" run_kubo.py } finally { SetPin "" }
