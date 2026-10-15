$ErrorActionPreference = 'Stop'
$src = 'D:\OpenPG2\EFILE_OLGWW2\SCENARIO'
$dst = 'D:\DSH\军事游戏汉化\work\olgww2\scenario'
$cp = [Text.Encoding]::GetEncoding(1252)
$names = [IO.File]::ReadAllText('D:\DSH\军事游戏汉化\work\olgww2\_seg3_names.json', [Text.Encoding]::UTF8) | ConvertFrom-Json
$report = @()
foreach ($n in $names) {
  $s = $cp.GetString([IO.File]::ReadAllBytes((Join-Path $src $n)))
  $d = [IO.File]::ReadAllText((Join-Path $dst ($n + '.utf8.txt')), [Text.Encoding]::UTF8)
  $sl = @(($s -replace "(\r?\n)$",'') -split "\r?\n")
  $dl = @(($d -replace "(\r?\n)$",'') -split "\r?\n")
  for ($i = 0; $i -lt $sl.Count; $i++) {
    $a = $sl[$i]; $b = $dl[$i]
    if ([string]::IsNullOrWhiteSpace($a)) { continue }
    # identical non-blank line (not pure numbers/symbols) => untranslated
    if ($a -eq $b) {
      if ($a -notmatch '^[\s\d\.\-\*/\[\]\\]+$') {
        $report += [pscustomobject]@{ file = $n; line = ($i + 1); text = $a }
      }
    }
  }
}
"identical non-blank lines: $($report.Count)"
$report | ForEach-Object { "{0}:{1}  {2}" -f $_.file, $_.line, $_.text }
