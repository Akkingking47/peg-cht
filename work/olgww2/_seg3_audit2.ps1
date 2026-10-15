$ErrorActionPreference = 'Stop'
$dst = 'D:\DSH\军事游戏汉化\work\olgww2\scenario'
$names = [IO.File]::ReadAllText('D:\DSH\军事游戏汉化\work\olgww2\_seg3_names.json', [Text.Encoding]::UTF8) | ConvertFrom-Json
$problems = @()
$totalBytes = 0
foreach ($n in $names) {
  $p = Join-Path $dst ($n + '.utf8.txt')
  if (-not (Test-Path -LiteralPath $p)) { $problems += "$n : MISSING"; continue }
  $bytes = [IO.File]::ReadAllBytes($p)
  $totalBytes += $bytes.Length
  $t = [IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)
  $issues = @()
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $issues += 'BOM' }
  if ($t.Contains([char]0xFFFD)) { $issues += 'REPLACEMENT_CHAR' }
  if ($t.Contains('\n')) { $issues += 'LITERAL_BACKSLASH_N' }
  if ($t -match '\?\?\?') { $issues += 'TRIPLE_QUESTION' }
  if ($t.Length -eq 0) { $issues += 'EMPTY' }
  if ($issues.Count) { $problems += ("{0} : {1}" -f $n, ($issues -join ',')) }
}
"checked={0}  totalBytes={1}  problems={2}" -f $names.Count, $totalBytes, $problems.Count
$problems | ForEach-Object { "PROBLEM: $_" }

"`n---- residual English sentence scan (files where >25% of chars are Latin) ----"
foreach ($n in $names) {
  $p = Join-Path $dst ($n + '.utf8.txt')
  $t = [IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)
  $cjk = ([regex]::Matches($t, '[\u4e00-\u9fff]')).Count
  $lat = ([regex]::Matches($t, '[A-Za-z]')).Count
  if ($cjk -eq 0 -and $lat -gt 0) { "ALL-LATIN: $n" }
}
