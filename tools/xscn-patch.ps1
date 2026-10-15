param(
  [string]$Root = 'D:\OpenPG2',
  [string]$Efile = 'EFILE_OLGWW2',
  [Parameter(Mandatory=$true)][string]$Map,
  [Parameter(Mandatory=$true)][string]$BackupDir,
  [string]$File = '',
  [switch]$DryRun
)
# Apply a translation map to OpenGen .xscn scenario name tables.
#
# Map format (5 TAB columns):
#   <xscn name> <group | -1 for title> <index> <expected original> <new text>
#
# Safety properties
#  1. A string is re-encoded only when its translation actually contains CJK.
#     Everything else keeps its ORIGINAL BYTES (the source files hold Latin-1
#     accented chars as single bytes; GBK would encode them as two).
#  2. The rebuilt file is first written to a temp file and re-parsed; only when
#     the item count and title match does it touch the real file.
#  3. Every array handed to BinaryWriter is explicitly cast to [byte[]].  A
#     PowerShell array built by an if-expression becomes Object[], and
#     BinaryWriter.Write(Object[]) silently writes only ONE byte.
#  4. This script is pure ASCII (no BOM needed, so PowerShell 5.1 cannot
#     mis-decode it); $BackupDir is a mandatory argument for the same reason.
$ErrorActionPreference = 'Stop'
$ENC_IN = [Text.Encoding]::GetEncoding(1252)
$ENC_OUT = [Text.Encoding]::GetEncoding(936)

function Has-CJK([string]$s) { return ($s -match '[\u2E80-\u9FFF\uF900-\uFAFF\uFF00-\uFFEF]') }

function Fold-Ascii([string]$s) {
  $map = @{
    [char]0x00DF = 'ss'; [char]0x00E6 = 'ae'; [char]0x00C6 = 'AE'
    [char]0x0153 = 'oe'; [char]0x0152 = 'OE'; [char]0x00F8 = 'o'
    [char]0x00D8 = 'O';  [char]0x0142 = 'l';  [char]0x0141 = 'L'
    [char]0x0111 = 'd';  [char]0x0110 = 'D';  [char]0x00F0 = 'd'
    [char]0x00FE = 'th'; [char]0x00DE = 'TH'
  }
  $sb = New-Object System.Text.StringBuilder
  foreach ($ch in $s.ToCharArray()) {
    if ($map.ContainsKey($ch)) { [void]$sb.Append($map[$ch]); continue }
    $d = $ch.ToString().Normalize([Text.NormalizationForm]::FormD)
    foreach ($c2 in $d.ToCharArray()) {
      if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($c2) -ne [Globalization.UnicodeCategory]::NonSpacingMark) { [void]$sb.Append($c2) }
    }
  }
  return $sb.ToString()
}

function Parse-Xscn([string]$path) {
  $f = [IO.File]::ReadAllBytes($path)
  $st = -1
  for ($i = 0; $i -le $f.Length - 3; $i++) {
    if ($f[$i] -eq 0x3C -and $f[$i + 1] -eq 0x4E -and $f[$i + 2] -eq 0x3A) { $st = $i; break }
  }
  if ($st -lt 0) { return $null }
  $g = $st; while ($g -lt $f.Length -and $f[$g] -ne 0x3E) { $g++ }
  if ($g -ge $f.Length) { return $null }
  $dataEnd = $g + 1
  $off = $dataEnd
  $title = ''; $titleOff = 0; $titleLen = 0
  if ($off + 2 -le $f.Length) {
    $L = [int]$f[$off] + [int]$f[$off + 1] * 256
    if ($L -gt 0 -and ($off + 2 + $L) -le $f.Length) {
      $titleLen = $L; $titleOff = $off + 2
      $title = $ENC_IN.GetString($f, $off + 2, $L); $off = $off + 2 + $L
    }
  }
  $items = New-Object System.Collections.ArrayList
  $groups = New-Object System.Collections.ArrayList
  $gi = 0
  while ($off + 2 -le $f.Length) {
    $cnt = [int]$f[$off] + [int]$f[$off + 1] * 256
    if ($cnt -le 0 -or $cnt -gt 4000) { break }
    $off += 2
    $good = $true
    for ($k = 0; $k -lt $cnt; $k++) {
      if ($off + 2 -gt $f.Length) { $good = $false; break }
      $L = [int]$f[$off] + [int]$f[$off + 1] * 256
      if ($L -le 0 -or ($off + 2 + $L) -gt $f.Length) { $good = $false; break }
      [void]$items.Add([pscustomobject]@{ group = $gi; idx = $k; len = $L; off = $off + 2; text = $ENC_IN.GetString($f, $off + 2, $L) })
      $off = $off + 2 + $L
    }
    if (-not $good) { break }
    [void]$groups.Add([pscustomobject]@{ group = $gi; count = $cnt })
    $gi++; if ($gi -gt 64) { break }
  }
  return [pscustomobject]@{ path = $path; bytes = $f; size = $f.Length; dataEnd = $dataEnd; title = $title; titleLen = $titleLen; titleOff = $titleOff; items = $items; groups = $groups; parsedEnd = $off }
}

function Find-Item($x, [int]$grp, [int]$ix) {
  foreach ($it in $x.items) { if ($it.group -eq $grp -and $it.idx -eq $ix) { return $it } }
  return $null
}

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$want = @{}
foreach ($line in [IO.File]::ReadAllLines($Map, [Text.Encoding]::UTF8)) {
  if ($line.Trim().Length -eq 0 -or $line.TrimStart().StartsWith('#')) { continue }
  $c = $line -split "`t"
  if ($c.Count -lt 5) { continue }
  $fn = $c[0].Trim()
  if (-not $want.ContainsKey($fn)) { $want[$fn] = New-Object System.Collections.ArrayList }
  [void]$want[$fn].Add([pscustomobject]@{ group = [int]$c[1]; idx = [int]$c[2]; orig = $c[3]; text = $c[4] })
}

if ($File -ne '') { $listing = @( Join-Path (Join-Path $Root $Efile) ('SCENARIO\' + $File) ) }
else { $listing = (Get-ChildItem (Join-Path (Join-Path $Root $Efile) 'SCENARIO') -Filter '*.xscn' -File | Select-Object -ExpandProperty FullName) }

$nFiles = 0; $nSet = 0; $nKeep = 0; $nSkip = 0; $nFold = 0
foreach ($p in $listing) {
  $nm = Split-Path $p -Leaf
  if (-not $want.ContainsKey($nm)) { continue }
  $x = Parse-Xscn $p
  if ($x -eq $null) { Write-Host ("  SKIP unparsed: " + $nm); continue }

  $plan = @{}
  $newTitle = $x.title
  $titleChanged = $false
  foreach ($w in $want[$nm]) {
    if ($w.group -lt 0) {
      if ($x.title -ne $w.orig) { $nSkip++; continue }
      $newTitle = $w.text; $titleChanged = $true; continue
    }
    $it = Find-Item $x $w.group $w.idx
    if ($it -eq $null) { $nSkip++; continue }
    if ($it.text -ne $w.orig) { $nSkip++; continue }
    $plan[($w.group.ToString() + ':' + $w.idx)] = $w.text
  }
  if ($plan.Count -eq 0 -and -not $titleChanged) { Write-Host ("  no-op: " + $nm); continue }

  $ms = New-Object System.IO.MemoryStream
  $bw = New-Object System.IO.BinaryWriter($ms)
  $keep = [byte[]]$x.bytes[0..($x.dataEnd - 1)]
  if ($keep.Length -ne $x.dataEnd) { throw ("prefix slice broken for " + $nm) }
  $bw.Write([byte[]]$keep)

  # title: assign with statements, never with an if-expression
  $tb = $null
  if ((Has-CJK $newTitle) -and $newTitle -ne $x.title) {
    $foldedT = Fold-Ascii $newTitle
    if ($foldedT -ne $newTitle) { $nFold++ }
    $tb = [byte[]]$ENC_OUT.GetBytes($foldedT)
  }
  else {
    $tb = [byte[]]$x.bytes[$x.titleOff..($x.titleOff + $x.titleLen - 1)]
  }
  if ($tb.Length -gt 65535) { throw 'title too long' }
  $bw.Write([byte]($tb.Length -band 0xFF)); $bw.Write([byte](($tb.Length -shr 8) -band 0xFF))
  $bw.Write([byte[]]$tb)

  foreach ($gp in $x.groups) {
    $bw.Write([byte]($gp.count -band 0xFF)); $bw.Write([byte](($gp.count -shr 8) -band 0xFF))
    for ($k = 0; $k -lt $gp.count; $k++) {
      $it = Find-Item $x $gp.group $k
      if ($it -eq $null) { throw ('missing item g{0} i{1} in {2}' -f $gp.group, $k, $nm) }
      $key = $gp.group.ToString() + ':' + $k
      $txt = $null
      if ($plan.ContainsKey($key)) { $txt = $plan[$key] }
      if ($txt -eq $null -or -not (Has-CJK $txt)) {
        $ob = [byte[]]$x.bytes[$it.off..($it.off + $it.len - 1)]
        if ($plan.ContainsKey($key)) { $nKeep++ }
        $bw.Write([byte]($ob.Length -band 0xFF)); $bw.Write([byte](($ob.Length -shr 8) -band 0xFF))
        $bw.Write([byte[]]$ob)
      }
      else {
        $folded = Fold-Ascii $txt
        if ($folded -ne $txt) { $nFold++ }
        $nb = [byte[]]$ENC_OUT.GetBytes($folded)
        if ($nb.Length -gt 65535) { throw 'string too long' }
        $bw.Write([byte]($nb.Length -band 0xFF)); $bw.Write([byte](($nb.Length -shr 8) -band 0xFF))
        $bw.Write([byte[]]$nb)
        $nSet++
      }
    }
  }
  if ($x.parsedEnd -lt $x.size) { $bw.Write([byte[]]$x.bytes[$x.parsedEnd..($x.size - 1)]) }
  $bw.Flush()
  $outBytes = [byte[]]$ms.ToArray()
  $bw.Dispose(); $ms.Dispose()

  if ($outBytes.Length -lt $x.dataEnd) { throw ("REFUSING {0}: rebuilt {1} < prefix {2}" -f $nm, $outBytes.Length, $x.dataEnd) }

  # preflight: rebuild to a temp file, re-parse, and only then touch the real file
  $tmpf = Join-Path ([IO.Path]::GetTempPath()) ('xscnchk_' + [guid]::NewGuid().ToString('N') + '.xscn')
  [IO.File]::WriteAllBytes($tmpf, $outBytes)
  $chk = Parse-Xscn $tmpf
  $wantTitle = $ENC_IN.GetString([byte[]]$tb)
  $ok = ($chk -ne $null -and $chk.items.Count -eq $x.items.Count -and $chk.title -eq $wantTitle)
  [IO.File]::Delete($tmpf)
  if (-not $ok) {
    throw ("preflight FAILED for {0}: items {1} -> {2}; title '{3}' -> '{4}'" -f $nm, $x.items.Count, $(if ($chk) { $chk.items.Count } else { 'null' }), $x.title, $(if ($chk) { $chk.title } else { 'null' }))
  }

  if ($DryRun) {
    Write-Host ("  DRY {0}: {1} -> {2} bytes  items={3} translated={4}" -f $nm, $x.size, $outBytes.Length, $x.items.Count, $plan.Count)
  }
  else {
    $bak = Join-Path $BackupDir $nm
    if (-not (Test-Path -LiteralPath $bak)) { Copy-Item -LiteralPath $p -Destination $bak }
    if (-not (Test-Path -LiteralPath $bak)) { throw ("backup failed for " + $nm) }
    [IO.File]::WriteAllBytes($p, $outBytes)
    Write-Host ("  OK  {0}: {1} -> {2} bytes  items={3} translated={4}" -f $nm, $x.size, $outBytes.Length, $x.items.Count, $plan.Count)
  }
  $nFiles++
}
Write-Host ("  files={0} written={1} kept-original-bytes={2} accent-folded={3} read-verify-skipped={4}" -f $nFiles, $nSet, $nKeep, $nFold, $nSkip)
