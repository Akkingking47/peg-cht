param(
  [Parameter(Mandatory=$true)][string]$JsonPath,
  [string]$SrcDir = 'D:\OpenPG2\EFILE_OLGWW2\SCENARIO',
  [string]$OutDir = 'D:\DSH\军事游戏汉化\work\olgww2\scenario'
)
$ErrorActionPreference = 'Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$cp1252 = [Text.Encoding]::GetEncoding(1252)
$data = [IO.File]::ReadAllText($JsonPath, [Text.Encoding]::UTF8) | ConvertFrom-Json

$written = 0; $fails = @()
foreach ($item in $data) {
  $name = [string]$item.name
  $text = [string]$item.text
  $sp = Join-Path $SrcDir $name
  if (-not (Test-Path -LiteralPath $sp)) { $fails += "$name : source introuvable"; continue }

  # --- source: end-of-line style + trailing newline ---
  $sb = [IO.File]::ReadAllBytes($sp)
  $srctext = $cp1252.GetString($sb)
  $hasCrlf = $srctext.Contains("`r`n")
  if ($srctext.EndsWith("`r`n")) { $trail = "`r`n" }
  elseif ($srctext.EndsWith("`n")) { $trail = "`n" }
  else { $trail = "" }

  # --- translated lines (literal \n in the JSON payload become separators) ---
  $body = $text.Replace('\n', "`n")
  $lines = @($body -split "`n")
  while ($lines.Count -gt 0 -and $lines[-1] -eq '') { $lines = $lines[0..($lines.Count-2)] }

  $eol = if ($hasCrlf) { "`r`n" } else { "`n" }
  $outText = ($lines -join $eol) + $trail

  # --- structural fidelity check ---
  $srcNorm = $srctext -replace "(\r?\n)$", ''
  $outNorm = $outText -replace "(\r?\n)$", ''
  $srcCount = @($srcNorm -split "\r?\n").Count
  $outCount = @($outNorm -split "\r?\n").Count
  if ($srcCount -ne $outCount) {
    $fails += "$name : LINE COUNT src=$srcCount out=$outCount"
    continue
  }

  $dest = Join-Path $OutDir ($name + '.utf8.txt')
  [IO.File]::WriteAllText($dest, $outText, $utf8NoBom)
  $written++
}
"written=$written  fails=$($fails.Count)"
$fails | ForEach-Object { "FAIL: $_" }
