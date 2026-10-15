param(
  [string]$Root = 'D:\OpenPG2',
  [string]$Efile = 'EFILE_OLGWW2',
  [string]$Pristine,
  [switch]$WhatIf
)
# Restore every .xscn of an efile from a pristine copy of the official efile pack.
#   -Pristine  e.g. D:\DSH\...\backup\ORIGINAL-EFILE_OLGWW2\SCENARIO
if (-not (Test-Path -LiteralPath $Pristine)) { throw ('pristine dir not found: ' + $Pristine) }
$dst = Join-Path (Join-Path $Root $Efile) 'SCENARIO'
$n = 0
foreach ($f in (Get-ChildItem $Pristine -Filter '*.xscn' -File)) {
  $t = Join-Path $dst $f.Name
  if ($WhatIf) { Write-Host ('  would restore ' + $f.Name); $n++; continue }
  Copy-Item -LiteralPath $f.FullName -Destination $t -Force
  $n++
}
Write-Host ("  restored {0} .xscn files into {1}" -f $n, $dst)