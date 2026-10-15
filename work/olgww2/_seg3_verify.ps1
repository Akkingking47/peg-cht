param([string]$NamesJson)
$ErrorActionPreference = 'Stop'
$src = 'D:\OpenPG2\EFILE_OLGWW2\SCENARIO'
$dst = 'D:\DSH\军事游戏汉化\work\olgww2\scenario'
$enc = [Text.Encoding]::GetEncoding(1252)
$names = [IO.File]::ReadAllText($NamesJson, [Text.Encoding]::UTF8) | ConvertFrom-Json
$rows = @()
foreach ($n in $names) {
  $n = [string]$n
  $sp = Join-Path $src $n
  $dp = Join-Path $dst ($n + '.utf8.txt')
  if (-not (Test-Path -LiteralPath $dp)) { $rows += [pscustomobject]@{file=$n; status='MISSING_OUT'}; continue }
  $sb = [IO.File]::ReadAllBytes($sp)
  $s = $enc.GetString($sb)
  $d = [IO.File]::ReadAllText($dp, [Text.Encoding]::UTF8)
  # strip a single trailing newline (LF or CRLF) for line-count comparison
  $s2 = $s -replace "(\r?\n)$", ''
  $d2 = $d -replace "(\r?\n)$", ''
  $sLines = @($s2 -split "\r?\n")
  $dLines = @($d2 -split "\r?\n")
  $sTrail = if ($s.EndsWith("`r`n")) { 'CRLF' } elseif ($s.EndsWith("`n")) { 'LF' } else { 'none' }
  $dTrail = if ($d.EndsWith("`r`n")) { 'CRLF' } elseif ($d.EndsWith("`n")) { 'LF' } else { 'none' }
  $rows += [pscustomobject]@{
    file = $n
    status = if ($sLines.Count -eq $dLines.Count) { 'OK' } else { 'LINECOUNT' }
    sLines = $sLines.Count
    dLines = $dLines.Count
    srcTrail = $sTrail
    outTrail = $dTrail
    trailOk = ($sTrail -eq $dTrail)
    crlf = ($s -match "`r`n")
  }
}
$rows | ForEach-Object {
  "{0}`t{1}`tsrc={2}`tout={3}`tsrcTrail={4}`toutTrail={5}`ttrailOk={6}`tsrcHasCRLF={7}" -f `
    $_.file, $_.status, $_.sLines, $_.dLines, $_.srcTrail, $_.outTrail, $_.trailOk, $_.crlf
}
"---- summary ----"
"total={0} ok={1} issues={2}" -f $rows.Count, (@($rows | Where-Object {$_.status -eq 'OK'}).Count), (@($rows | Where-Object {$_.status -ne 'OK'}).Count)
