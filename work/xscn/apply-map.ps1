param(
  [Parameter(Mandatory=$true)][string]$MapPath
)
$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$src = Join-Path $root 'work\xscn\chunks\chunk-04.tsv'
$dst = Join-Path $root 'work\xscn\zh\part-04.tsv'
$map = Get-Content -LiteralPath $MapPath -Raw -Encoding UTF8 | ConvertFrom-Json
$props = @{}
foreach ($p in $map.PSObject.Properties) { $props[$p.Name] = $p.Value }
$lines = [System.IO.File]::ReadAllLines($dst, [System.Text.Encoding]::UTF8)
$orig  = [System.IO.File]::ReadAllLines($src, [System.Text.Encoding]::UTF8)
if ($lines.Count -ne $orig.Count) { throw ("line count drift: {0} vs {1}" -f $lines.Count, $orig.Count) }
$applied = 0; $bad = @()
foreach ($k in $props.Keys) {
  $hits = 0
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -ceq $k) {
      $hits++
      if ($lines[$i] -notlike "*`t*") { $lines[$i] = $lines[$i] + "`t" + $props[$k]; $applied++ }
    }
  }
  if ($hits -ne 1) { $bad += ("{0} => hits {1}" -f $k, $hits) }
}
if ($bad.Count -gt 0) { "PROBLEM:"; $bad; exit 1 }
[System.IO.File]::WriteAllLines($dst, $lines, (New-Object System.Text.UTF8Encoding($false)))
$pending = 0
foreach ($l in $lines) { if ($l -notlike "*`t*") { $pending++ } }
"applied=$applied total=$($lines.Count) pending=$pending"
