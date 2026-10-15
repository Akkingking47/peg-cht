$ErrorActionPreference = 'Stop'
$dst = 'D:\DSH\军事游戏汉化\work\olgww2\scenario'
$names = [IO.File]::ReadAllText('D:\DSH\军事游戏汉化\work\olgww2\_seg3_names.json', [Text.Encoding]::UTF8) | ConvertFrom-Json
# frequent traditional-only characters that must not appear in simplified output
$trad = '爾與國學說東車馬鳥魚點後會來時個們為這發實現當經對開關實現產經濟過還進運動員無線電絕對應該貝爾馬龍鳳華麗體國爾資訊網絡執行長總統領隊員'
$tradChars = $trad.ToCharArray() | Select-Object -Unique
$hits = @{}
foreach ($n in $names) {
  $p = Join-Path $dst ($n + '.utf8.txt')
  if (-not (Test-Path -LiteralPath $p)) { continue }
  $t = [IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)
  foreach ($c in $tradChars) {
    if ($t.Contains([string]$c)) {
      if (-not $hits.ContainsKey($n)) { $hits[$n] = @() }
      $hits[$n] += [string]$c
    }
  }
}
if ($hits.Count -eq 0) { "no traditional-only chars found" }
else { $hits.GetEnumerator() | ForEach-Object { "{0} : {1}" -f $_.Key, ($_.Value -join ' ') } }
"---- non-CJK/ASCII residue scan (Latin letters left in output) ----"
foreach ($n in $names) {
  $p = Join-Path $dst ($n + '.utf8.txt')
  if (-not (Test-Path -LiteralPath $p)) { continue }
  $t = [IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)
  $lat = [regex]::Matches($t, '[A-Za-z]{2,}') | ForEach-Object { $_.Value } | Select-Object -Unique
  if ($lat) { "{0} : {1}" -f $n, ($lat -join ', ') }
}
