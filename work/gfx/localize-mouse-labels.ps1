param(
  [string]$Root = 'D:\OpenPG2',
  [Parameter(Mandatory=$true)][string]$LabelsFile,
  [Parameter(Mandatory=$true)][string]$BackupDir,
  [string[]]$Include = @(),
  [int]$Pitch = 13,
  [string]$FontName = 'SimHei',
  [switch]$DryRun
)
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference = 'Stop'

# ---- parse label table: section -> ordered array ----
$sets = @{}
$cur = $null
foreach ($ln in [System.IO.File]::ReadAllLines($LabelsFile, [System.Text.Encoding]::UTF8)) {
  $s = $ln.Trim()
  if ($s.Length -eq 0 -or $s.StartsWith('#')) { continue }
  if ($s -match '^\[(.+)\]$') { $cur = $Matches[1]; $sets[$cur] = New-Object System.Collections.ArrayList; continue }
  if ($cur -ne $null) { [void]$sets[$cur].Add($s) }
}

$targets = @(
  @{ rel = 'OPENGUI\mouse_build.png';                  sec = 'build' },
  @{ rel = 'OPENGUI\mouse_missions.png';               sec = 'missions' },
  @{ rel = 'EFILE_AG\OPENGUI\mouse_build.png';         sec = 'build' },
  @{ rel = 'EFILE_KAISER\OPENGUI\mouse_build.png';     sec = 'build' },
  @{ rel = 'EFILE_OPENPEG\OPENGUI\mouse_build.png';    sec = 'build' },
  @{ rel = 'EFILE_OPENPEG\OPENGUI\mouse_missions.png'; sec = 'missions' },
  @{ rel = 'EFILE_SON\OPENGUI\mouse_build.png';        sec = 'build' }
)
if ($Include.Count -gt 0) { $targets = @($targets | Where-Object { $Include -contains $_.rel }) }
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

function RGB([int]$argb) { return ($argb -band 0x00FFFFFF) }
function MkCol([int]$rgb) { return [System.Drawing.Color]::FromArgb(255, ($rgb -shr 16) -band 0xFF, ($rgb -shr 8) -band 0xFF, $rgb -band 0xFF) }
function Lum([System.Drawing.Color]$c) {
  $f = { param($v) if ($v -le 0.03928) { return $v / 12.92 } return [Math]::Pow((($v + 0.055) / 1.055), 2.4) }
  return 0.2126 * (& $f ($c.R / 255.0)) + 0.7152 * (& $f ($c.G / 255.0)) + 0.0722 * (& $f ($c.B / 255.0))
}

foreach ($tg in $targets) {
  $path = Join-Path $Root $tg.rel
  if (-not (Test-Path -LiteralPath $path)) { Write-Host ("MISSING  " + $tg.rel); continue }
  $lbl = @($sets[$tg.sec])

  $src = New-Object System.Drawing.Bitmap($path)
  $W = $src.Width; $H = $src.Height
  $keyRGB = RGB $src.GetPixel(0, 0).ToArgb()
  $keyCol = MkCol $keyRGB
  $cells = [int][Math]::Floor($H / $Pitch)

  # ---- pass 1: per cell -> box colour, text colour, icon start column ----
  $box = @(); $tcol = @(); $iconX = @()
  for ($k = 0; $k -lt $cells; $k++) {
    $y0 = $k * $Pitch
    $hist = @{}
    for ($y = $y0; $y -lt $y0 + $Pitch; $y++) {
      for ($x = 0; $x -lt $W; $x++) {
        $c = RGB $src.GetPixel($x, $y).ToArgb()
        if ($c -eq $keyRGB) { continue }
        if ($hist.ContainsKey($c)) { $hist[$c] = $hist[$c] + 1 } else { $hist[$c] = 1 }
      }
    }
    if ($hist.Count -eq 0) { $box += $null; $tcol += $null; $iconX += 0; continue }
    $sorted = $hist.GetEnumerator() | Sort-Object Value -Descending
    $b = MkCol([int]$sorted[0].Key)
    $tc = $null
    foreach ($e in $sorted) {
      $c = MkCol([int]$e.Key)
      if ($c.ToArgb() -eq $b.ToArgb()) { continue }
      if ((Lum $c) -lt 0.05) { continue }
      $tc = $c; break
    }
    $box += $b; $tcol += $tc
    # icon detection: a >=8px gap of text-coloured columns, last run starting at x>=40
    $ix = 0
    if ($tc -ne $null) {
      $tcRGB = RGB $tc.ToArgb()
      $runs = New-Object System.Collections.ArrayList
      $st = -1
      for ($x = 0; $x -lt $W; $x++) {
        $n = 0
        for ($y = $y0; $y -lt $y0 + $Pitch; $y++) { if ((RGB $src.GetPixel($x, $y).ToArgb()) -eq $tcRGB) { $n++ } }
        if ($n -gt 0 -and $st -lt 0) { $st = $x }
        elseif ($n -eq 0 -and $st -ge 0) { [void]$runs.Add(@($st, ($x - 1))); $st = -1 }
      }
      if ($st -ge 0) { [void]$runs.Add(@($st, ($W - 1))) }
      if ($runs.Count -ge 2) {
        $last = $runs[$runs.Count - 1]; $prev = $runs[$runs.Count - 2]
        $gap = $last[0] - $prev[1] - 1
        if ($gap -ge 6 -and $last[0] -ge 42) { $ix = $last[0] }
      }
    }
    $iconX += $ix
  }

  $report = @()
  for ($k = 0; $k -lt [Math]::Min($cells, $lbl.Count); $k++) {
    if ($box[$k] -eq $null -or $tcol[$k] -eq $null) { $report += ("{0}:skip" -f $k); continue }
    $report += ("{0}:'{1}'(#{2:X6}{3})" -f $k, $lbl[$k], (RGB $tcol[$k].ToArgb()), $(if ($iconX[$k] -gt 0) { "@" + $iconX[$k] } else { '' }))
  }
  Write-Host ("== " + $tg.rel + "  " + $W + "x" + $H + "  cells=" + $cells + "  key=#" + ('{0:X6}' -f $keyRGB))
  Write-Host ("   " + ($report -join '  '))
  if ($DryRun) { $src.Dispose(); continue }

  $bak = Join-Path $BackupDir ($tg.rel.Replace('\', '__'))
  if (-not (Test-Path -LiteralPath $bak)) { Copy-Item -LiteralPath $path -Destination $bak }

  # ---- palette: key at 0, then every colour the original uses, then text ramps ----
  $palList = New-Object System.Collections.Generic.List[System.Drawing.Color]
  $indexOf = @{}
  $palList.Add($keyCol); $indexOf[$keyRGB] = 0
  for ($j = 0; $j -lt $src.Palette.Entries.Count; $j++) {
    $rgb = RGB $src.Palette.Entries[$j].ToArgb()
    if ($indexOf.ContainsKey($rgb)) { continue }
    $indexOf[$rgb] = $palList.Count; $palList.Add((MkCol $rgb))
  }
  for ($k = 0; $k -lt [Math]::Min($cells, $lbl.Count); $k++) {
    if ($tcol[$k] -eq $null -or $box[$k] -eq $null) { continue }
    $b = $box[$k]; $tc = $tcol[$k]
    for ($q = 0; $q -le 8; $q++) {
      $a = $q / 8.0
      $c = [System.Drawing.Color]::FromArgb(255,
        [int][Math]::Round($b.R + ($tc.R - $b.R) * $a),
        [int][Math]::Round($b.G + ($tc.G - $b.G) * $a),
        [int][Math]::Round($b.B + ($tc.B - $b.B) * $a))
      $rgb = RGB $c.ToArgb()
      if (-not $indexOf.ContainsKey($rgb)) { $indexOf[$rgb] = $palList.Count; $palList.Add($c) }
    }
  }

  $out = New-Object System.Drawing.Bitmap($W, $H, [System.Drawing.Imaging.PixelFormat]::Format8bppIndexed)
  $pal = $out.Palette
  for ($j = 0; $j -lt 256; $j++) { if ($j -lt $palList.Count) { $pal.Entries[$j] = $palList[$j] } else { $pal.Entries[$j] = $keyCol } }
  $out.Palette = $pal

  $rect = New-Object System.Drawing.Rectangle(0, 0, $W, $H)
  $bd = $out.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::WriteOnly, [System.Drawing.Imaging.PixelFormat]::Format8bppIndexed)
  $stride = $bd.Stride; $scan0 = $bd.Scan0
  $zero = New-Object byte[] ($stride * $H)
  [System.Runtime.InteropServices.Marshal]::Copy($zero, 0, $scan0, $zero.Length)

  for ($y = 0; $y -lt $H; $y++) {
    $ro = $y * $stride
    for ($x = 0; $x -lt $W; $x++) {
      $rgb = RGB $src.GetPixel($x, $y).ToArgb()
      $ix = $indexOf[$rgb]
      if ($ix -eq $null) { $ix = 0 }
      [System.Runtime.InteropServices.Marshal]::WriteByte($scan0, $ro + $x, [byte]$ix)
    }
  }
  $src.Dispose()

  # ---- erase old text, draw the translated label ----
  $sf = [System.Drawing.StringFormat]::GenericTypographic
  for ($k = 0; $k -lt [Math]::Min($cells, $lbl.Count); $k++) {
    if ($tcol[$k] -eq $null -or $box[$k] -eq $null) { continue }
    $x1 = 2
    $x2 = if ($iconX[$k] -gt 0) { $iconX[$k] - 2 } else { $W - 4 }
    $maxW = $x2 - $x1
    $bx = $indexOf[(RGB $box[$k].ToArgb())]
    for ($y = $k * $Pitch + 2; $y -lt $k * $Pitch + $Pitch - 1; $y++) {
      $ro = $y * $stride
      for ($x = $x1; $x -le $x2; $x++) { [System.Runtime.InteropServices.Marshal]::WriteByte($scan0, $ro + $x, [byte]$bx) }
    }
    $text = $lbl[$k]
    $fs = 12; $fnt = $null
    while ($fs -ge 8) {
      $f = New-Object System.Drawing.Font($FontName, $fs, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
      $tb = New-Object System.Drawing.Bitmap -ArgumentList 160, 24
      $gt = [System.Drawing.Graphics]::FromImage($tb)
      $m = $gt.MeasureString($text, $f, 1000, $sf)
      $gt.Dispose(); $tb.Dispose()
      if ($m.Width -le $maxW) { $fnt = $f; break }
      $f.Dispose(); $fs--
    }
    if ($fnt -eq $null) { $fnt = New-Object System.Drawing.Font($FontName, 8, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel) }
    $tmp = New-Object System.Drawing.Bitmap -ArgumentList $W, $Pitch
    $g = [System.Drawing.Graphics]::FromImage($tmp)
    $g.Clear($box[$k])
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
    $sz = $g.MeasureString($text, $fnt, 1000, $sf)
    $ty = ($Pitch - 1 - $sz.Height) / 2.0
    if ($ty -lt 0) { $ty = 0 }
    $fb = New-Object System.Drawing.SolidBrush($tcol[$k])
    $g.DrawString($text, $fnt, $fb, 0, $ty, $sf)
    $fb.Dispose(); $g.Dispose(); $fnt.Dispose()
    $boxRGB = RGB $box[$k].ToArgb()
    for ($y = 0; $y -lt $Pitch; $y++) {
      $ro = ($k * $Pitch + $y) * $stride
      for ($x = $x1; $x -le $x2; $x++) {
        $rgb = RGB $tmp.GetPixel($x, $y).ToArgb()
        if ($rgb -eq $boxRGB) { continue }
        $ix = $indexOf[$rgb]
        if ($ix -eq $null) {
          $best = [int]::MaxValue; $ix = $bx
          $cr = ($rgb -shr 16) -band 0xFF; $cg = ($rgb -shr 8) -band 0xFF; $cb2 = $rgb -band 0xFF
          foreach ($kv in $indexOf.GetEnumerator()) {
            $c2 = $palList[[int]$kv.Value]
            $dr = $cr - $c2.R; $dg = $cg - $c2.G; $db = $cb2 - $c2.B
            $d = $dr * $dr + $dg * $dg + $db * $db
            if ($d -lt $best) { $best = $d; $ix = [int]$kv.Value }
          }
        }
        [System.Runtime.InteropServices.Marshal]::WriteByte($scan0, $ro + $x, [byte]$ix)
      }
    }
    $tmp.Dispose()
  }

  $out.UnlockBits($bd)
  $out.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
  Write-Host ("   saved -> " + $path + "   palette=" + $palList.Count)
  $out.Dispose()
}
Write-Host 'DONE'
