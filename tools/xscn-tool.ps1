param(
  [string]$Root = 'D:\OpenPG2',
  [string]$Efile = 'EFILE_OLGWW2',
  [ValidateSet('list', 'export', 'apply')][string]$Action = 'list',
  [string]$File = '',
  [string]$Map = '',
  [string]$BackupDir = 'D:\DSH\军事游戏汉化\backup\xscn-names-orig',
  [switch]$DryRun
)
# OpenGen .xscn scenario name tables.
# Layout: [scenario data][<N:nnnn>][title][group0][group1]...
#   title : u16 byte-length + bytes
#   group : u16 item-count + items
#   item  : u16 byte-length + bytes        <- VARIABLE length
# The whole string region sits at the END of the file and the file ends with it,
# so changing lengths needs no pointer fix-ups. Strings are written as GBK(936),
# which the engine reads via MultiByteToWideChar(CP_ACP=936).
#
# Map file for -Action apply (5 TAB columns):
#   <xscn name> <group | -1 for title> <index> <expected original> <new text>
# A row is applied only when the text currently in the file equals <expected original>.
$ErrorActionPreference = 'Stop'
$ENC_IN = [Text.Encoding]::GetEncoding(1252)
$ENC_OUT = [Text.Encoding]::GetEncoding(936)

function Parse-Xscn([string]$path) {
  $f = [IO.File]::ReadAllBytes($path)
  $st = -1
  for ($i = 0; $i -le $f.Length - 3; $i++) {
    if ($f[$i] -eq 0x3C -and $f[$i + 1] -eq 0x4E -and $f[$i + 2] -eq 0x3A) { $st = $i; break }
  }
  if ($st -lt 0) { return $null }
  $g = $st; while ($g -lt $f.Length -and $f[$g] -ne 0x3E) { $g++ }
  if ($g -ge $f.Length) { return $null }
  $r = [ordered]@{
    path = $path; bytes = $f; size = $f.Length
    markerOff = $st; marker = [Text.Encoding]::ASCII.GetString($f, $st, $g - $st + 1)
    dataEnd = $g + 1
    title = ''; titleLen = 0
    items = New-Object System.Collections.ArrayList
    groups = New-Object System.Collections.ArrayList
    parsedEnd = $g + 1
  }
  $off = $g + 1
  if ($off + 2 -le $f.Length) {
    $L = [int]$f[$off] + [int]$f[$off + 1] * 256
    if ($L -gt 0 -and ($off + 2 + $L) -le $f.Length) {
      $r.titleLen = $L
      $r.title = $ENC_IN.GetString($f, $off + 2, $L); $off = $off + 2 + $L
    }
  }
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
      [void]$r.items.Add([pscustomobject]@{ group = $gi; idx = $k; len = $L; text = $ENC_IN.GetString($f, $off + 2, $L) })
      $off = $off + 2 + $L
    }
    if (-not $good) { break }
    [void]$r.groups.Add([pscustomobject]@{ group = $gi; count = $cnt })
    $gi++; if ($gi -gt 64) { break }
  }
  $r.parsedEnd = $off
  return [pscustomobject]$r
}

function Get-Targets {
  if ($File -ne '') { return @( Join-Path (Join-Path $Root $Efile) ('SCENARIO\' + $File) ) }
  return (Get-ChildItem (Join-Path (Join-Path $Root $Efile) 'SCENARIO') -Filter '*.xscn' -File | Select-Object -ExpandProperty FullName)
}

function Get-Item2($x, [int]$grp, [int]$ix) {
  foreach ($it in $x.items) { if ($it.group -eq $grp -and $it.idx -eq $ix) { return $it } }
  return $null
}

switch ($Action) {
  'list' {
    $tot = 0; $files = 0; $bad = 0
    foreach ($p in Get-Targets) {
      $x = Parse-Xscn $p
      if ($x -eq $null) { Write-Host ("  UNPARSED " + (Split-Path $p -Leaf)); $bad++; continue }
      $files++; $tot += $x.items.Count
      $al = if ($x.parsedEnd -eq $x.size) { 'EOF' } else { 'leftover=' + ($x.size - $x.parsedEnd) }
      Write-Host ("  {0,-18} items={1,4} groups={2} parsedEnd={3,7} size={4,7} {5}" -f (Split-Path $p -Leaf), $x.items.Count, $x.groups.Count, $x.parsedEnd, $x.size, $al)
    }
    Write-Host ("  TOTAL files={0} items={1} unparsed={2}" -f $files, $tot, $bad)
  }
  'export' {
    $rows = New-Object System.Collections.ArrayList
    foreach ($p in Get-Targets) {
      $x = Parse-Xscn $p
      if ($x -eq $null) { continue }
      $nm = Split-Path $p -Leaf
      [void]$rows.Add(("{0}`t-1`t0`t{1}`t{1}" -f $nm, $x.title))
      foreach ($it in $x.items) {
        [void]$rows.Add(("{0}`t{1}`t{2}`t{3}`t{3}" -f $nm, $it.group, $it.idx, $it.text))
      }
    }
    $out = if ($Map -ne '') { $Map } else { 'D:\DSH\军事游戏汉化\work\xscn-export.tsv' }
    [IO.File]::WriteAllLines($out, $rows, (New-Object Text.UTF8Encoding($false)))
    Write-Host ("  exported {0} rows -> {1}" -f $rows.Count, $out)
  }
  'apply' {
    if ($Map -eq '' -or -not (Test-Path -LiteralPath $Map)) { throw 'apply needs -Map <tsv>' }
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
    $nFiles = 0; $nSet = 0; $nSkip = 0; $nGrow = 0; $nShrink = 0; $nSame = 0
    foreach ($p in Get-Targets) {
      $nm = Split-Path $p -Leaf
      if (-not $want.ContainsKey($nm)) { continue }
      $x = Parse-Xscn $p
      if ($x -eq $null) { Write-Host ("  SKIP unparsed: " + $nm); continue }

      $plan = @{}; $newTitle = $x.title; $titleChanged = $false
      foreach ($w in $want[$nm]) {
        if ($w.group -lt 0) {
          if ($x.title -ne $w.orig) { $nSkip++; continue }
          $newTitle = $w.text; $titleChanged = $true; continue
        }
        $it = Get-Item2 $x $w.group $w.idx
        if ($it -eq $null) { $nSkip++; continue }
        if ($it.text -ne $w.orig) { $nSkip++; continue }
        $plan[($w.group.ToString() + ':' + $w.idx)] = $w.text
      }
      if ($plan.Count -eq 0 -and -not $titleChanged) { Write-Host ("  no-op: " + $nm); continue }

      $ms = New-Object System.IO.MemoryStream
      $bw = New-Object System.IO.BinaryWriter($ms)
      $keep = [byte[]]$x.bytes[0..($x.dataEnd - 1)]
      if ($keep.Length -ne $x.dataEnd) { throw ("prefix slice broken: {0} != {1}" -f $keep.Length, $x.dataEnd) }
      $bw.Write($keep)
      $tb = [byte[]]$ENC_OUT.GetBytes($newTitle)
      if ($tb.Length -gt 65535) { throw 'title too long' }
      $bw.Write([byte]($tb.Length -band 0xFF)); $bw.Write([byte](($tb.Length -shr 8) -band 0xFF))
      $bw.Write($tb)
      foreach ($gp in $x.groups) {
        $bw.Write([byte]($gp.count -band 0xFF)); $bw.Write([byte](($gp.count -shr 8) -band 0xFF))
        for ($k = 0; $k -lt $gp.count; $k++) {
          $it = Get-Item2 $x $gp.group $k
          if ($it -eq $null) { throw ('missing item g{0} i{1} in {2}' -f $gp.group, $k, $nm) }
          $key = $gp.group.ToString() + ':' + $k
          $txt = $it.text
          if ($plan.ContainsKey($key)) {
            $txt = $plan[$key]; $nSet++
            $nb = [byte[]]$ENC_OUT.GetBytes($txt)
            if ($nb.Length -gt $it.len) { $nGrow++ } elseif ($nb.Length -lt $it.len) { $nShrink++ } else { $nSame++ }
          }
          else { $nb = [byte[]]$ENC_OUT.GetBytes($txt) }
          if ($nb.Length -gt 65535) { throw 'string too long' }
          $bw.Write([byte]($nb.Length -band 0xFF)); $bw.Write([byte](($nb.Length -shr 8) -band 0xFF))
          $bw.Write($nb)
        }
      }
      if ($x.parsedEnd -lt $x.size) { $bw.Write([byte[]]$x.bytes[$x.parsedEnd..($x.size - 1)]) }
      $bw.Flush()
      $outBytes = [byte[]]$ms.ToArray()
      $bw.Dispose(); $ms.Dispose()

      # safety assertions: a truncated rebuild must never reach the disk
      if ($outBytes.Length -lt $x.dataEnd) { throw ("REFUSING to write {0}: rebuilt {1} < prefix {2}" -f $nm, $outBytes.Length, $x.dataEnd) }
      $chk = $null
      if (-not $DryRun) {
        $bak = Join-Path $BackupDir $nm
        if (-not (Test-Path -LiteralPath $bak)) { Copy-Item -LiteralPath $p -Destination $bak }
        if (-not (Test-Path -LiteralPath $bak)) { throw ("backup failed for " + $nm) }
        [IO.File]::WriteAllBytes($p, $outBytes)
        $chk = Parse-Xscn $p
        if ($chk -eq $null -or $chk.items.Count -ne $x.items.Count) { throw ("post-write verification FAILED for " + $nm) }
      }
      Write-Host ("  {0} {1}: {2} -> {3} bytes  items={4} set={5}{6}" -f $(if ($DryRun) { 'DRY' } else { 'OK ' }), $nm, $x.size, $outBytes.Length, $x.items.Count, $plan.Count, $(if ($chk) { ' chunk=' + $chk.items.Count } else { '' }))
      $nFiles++
    }
    Write-Host ("  files={0} set={1} read-verify-skipped={2} grew={3} shrunk={4} same={5}" -f $nFiles, $nSet, $nSkip, $nGrow, $nShrink, $nSame)
  }
}
