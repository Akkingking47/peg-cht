param(
  [string]$Root = 'D:\OpenPG2',
  [Parameter(Mandatory=$true)][string]$Labels,
  [Parameter(Mandatory=$true)][string]$BackupDir,
  [int]$FontSize = 13,
  [string]$FontName = 'SimHei',
  [string[]]$Include = @(),
  [switch]$DryRun,
  [switch]$Force
)
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference = 'Stop'

$names = [System.IO.File]::ReadAllLines($Labels, [System.Text.Encoding]::UTF8)

$targets = @(
 'OPENGUI\hex_text.png',
 'EFILE_OPENPG\OPENGUI\hex_text.png',
 'EFILE_Clu\OPENGUI\hex_text.png',
 'EFILE_COMWW2\OPENGUI\hex_text.png',
 'EFILE_KAISER\OPENGUI\hex_text.png',
 'EFILE_OPENAK\OPENGUI\hex_text.png',
 'EFILE_OPENPEG\OPENGUI\hex_text.png',
 'EFILE_OoB\OPENGUI\hex_text.png',
 'EFILE_SON\OPENGUI\hex_text.png'
)
if ($Include.Count -gt 0) { $targets = $Include }
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

function Get-Lum([System.Drawing.Color]$c) {
  $f = { param($v) if ($v -le 0.03928) { return $v / 12.92 } return [Math]::Pow((($v + 0.055) / 1.055), 2.4) }
  return 0.2126 * (& $f ($c.R / 255.0)) + 0.7152 * (& $f ($c.G / 255.0)) + 0.0722 * (& $f ($c.B / 255.0))
}
function RGB([int]$argb) { return ($argb -band 0x00FFFFFF) }
function MkCol([int]$rgb) { return [System.Drawing.Color]::FromArgb(255, ($rgb -shr 16) -band 0xFF, ($rgb -shr 8) -band 0xFF, $rgb -band 0xFF) }
function Blend([System.Drawing.Color]$a, [System.Drawing.Color]$b, [double]$t) {
  return [System.Drawing.Color]::FromArgb(255,
    [int][Math]::Round($a.R + ($b.R - $a.R) * $t),
    [int][Math]::Round($a.G + ($b.G - $a.G) * $t),
    [int][Math]::Round($a.B + ($b.B - $a.B) * $t))
}

foreach ($rel in $targets) {
  $path = Join-Path $Root $rel
  if (-not (Test-Path -LiteralPath $path)) { Write-Host ("MISSING  " + $rel); continue }

  $src = New-Object System.Drawing.Bitmap($path)
  $W = $src.Width; $H = $src.Height
  $bgc = $src.GetPixel(0, 0)
  $bgRGB = (RGB $bgc.ToArgb())
  $bgCol = (MkCol $bgRGB)
  $slices = [int][Math]::Floor($H / 50)
  if ($slices -gt $names.Length) { $slices = $names.Length }

  # originals carry a tiny PLTE (8..17 entries); our output always carries 256.
  if ($src.Palette.Entries.Count -gt 64 -and -not $Force) {
    Write-Host ("== " + $rel + "  SKIP: already converted (palette has " + $src.Palette.Entries.Count + " entries).")
    Write-Host "   Restore from the backup first, or pass -Force to redo anyway."
    $src.Dispose(); continue
  }

  $bak = Join-Path $BackupDir ($rel.Replace('\', '__'))
  if (-not $DryRun -and -not (Test-Path -LiteralPath $bak)) { Copy-Item -LiteralPath $path -Destination $bak }

  # ---- 1. analyse ----
  $plans = @(); $report = @(); $widths = @()
  for ($i = 0; $i -lt $slices; $i++) {
    $y0 = $i * 50
    $hist = @{}; $minx = 9999; $maxx = -1; $miny = 9999; $maxy = -1
    for ($y = $y0; $y -lt $y0 + 50; $y++) {
      for ($x = 0; $x -lt $W; $x++) {
        $k = RGB $src.GetPixel($x, $y).ToArgb()
        if ($k -eq $bgRGB) { continue }
        if ($hist.ContainsKey($k)) { $hist[$k] = $hist[$k] + 1 } else { $hist[$k] = 1 }
        if ($x -lt $minx) { $minx = $x }; if ($x -gt $maxx) { $maxx = $x }
        if ($y -lt $miny) { $miny = $y }; if ($y -gt $maxy) { $maxy = $y }
      }
    }
    $kind = 'empty'; $fill = $null; $mark = $null; $outline = $null; $ratio = 0.0
    if ($hist.Count -gt 0) {
      $sorted = $hist.GetEnumerator() | Sort-Object Value -Descending
      $dom = [int]$sorted[0].Key
      $area = ($maxx - $minx + 1) * ($maxy - $miny + 1)
      $ratio = [Math]::Round(([int]$sorted[0].Value) / [double]$area, 2)
      if ($ratio -ge 0.55) {
        $kind = 'plaque'; $fill = (MkCol $dom)
        $lc = Get-Lum $fill
        if ((1.05 / ($lc + 0.05)) -ge (($lc + 0.05) / 0.05)) { $mark = [System.Drawing.Color]::White } else { $mark = [System.Drawing.Color]::Black }
      }
      else {
        $kind = 'text'
        # brightest common colour = glyph fill ; darkest common colour = outline
        foreach ($e in $sorted) {
          $c = MkCol([int]$e.Key)
          if ((Get-Lum $c) -ge 0.04) { $mark = $c; break }
        }
        if ($mark -eq $null) { $mark = (MkCol $dom) }
        foreach ($e in $sorted) {
          $c = MkCol([int]$e.Key)
          if ((Get-Lum $c) -lt 0.04) { $outline = $c; break }
        }
      }
    }
    $plans += , @($kind, $fill, $mark, $outline)
    if ($maxx -lt 0) { $widths += 0 } else { $widths += ($maxx - $minx + 1) }
    $report += ("{0}:{1}#{2:X6} r={3}" -f $i, $kind.Substring(0, 1), $(if ($mark -eq $null) { $bgRGB } else { (RGB $mark.ToArgb()) }), $ratio)
  }
  Write-Host ("== " + $rel + "  " + $W + "x" + $H + "  slices=" + $slices)
  Write-Host ("   " + ($report -join ' '))
  $nz = @($widths | Where-Object { $_ -gt 0 })
  $avgW = 0.0
  if ($nz.Count -gt 0) { $avgW = ($nz | Measure-Object -Average).Average }
  if ($avgW -gt 0 -and $avgW -lt 20) {
    Write-Host ("   SKIP: looks like an ICON atlas (mean bbox width " + [Math]::Round($avgW, 1) + " px) - left untouched")
    $src.Dispose(); continue
  }
  if ($DryRun) { $src.Dispose(); continue }
  $src.Dispose()

  # ---- 2. palette ----
  $palList = New-Object System.Collections.Generic.List[System.Drawing.Color]
  $palList.Add($bgCol)
  $indexOf = @{}; $indexOf[$bgRGB] = 0
  $sliceCols = @()
  for ($i = 0; $i -lt $slices; $i++) {
    $kind = $plans[$i][0]; $fill = $plans[$i][1]; $mark = $plans[$i][2]; $outline = $plans[$i][3]
    $cols = New-Object System.Collections.Generic.List[System.Drawing.Color]
    if ($kind -eq 'plaque') {
      $cols.Add($fill); $cols.Add($mark)
      for ($k = 1; $k -le 10; $k++) { $cols.Add((Blend $fill $mark ($k / 11.0))) }
    }
    elseif ($kind -eq 'text') {
      if ($outline -ne $null) { $cols.Add($outline) }
      $cols.Add($mark)
    }
    $cl = @()
    foreach ($cc in $cols) {
      $key = RGB $cc.ToArgb()
      if ($indexOf.ContainsKey($key)) { $ix = [int]$indexOf[$key] }
      else { if ($palList.Count -ge 256) { throw 'palette overflow' }; $ix = $palList.Count; $palList.Add($cc); $indexOf[$key] = $ix }
      if ($cl -notcontains $ix) { $cl += $ix }
    }
    $sliceCols += , $cl
  }

  $out = New-Object System.Drawing.Bitmap($W, $H, [System.Drawing.Imaging.PixelFormat]::Format8bppIndexed)
  $pal = $out.Palette
  for ($j = 0; $j -lt 256; $j++) { if ($j -lt $palList.Count) { $pal.Entries[$j] = $palList[$j] } else { $pal.Entries[$j] = $bgCol } }
  $out.Palette = $pal

  # ---- 3. draw + write indices ----
  $sf = [System.Drawing.StringFormat]::GenericTypographic
  $rect = New-Object System.Drawing.Rectangle(0, 0, $W, $H)
  $bd = $out.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::WriteOnly, [System.Drawing.Imaging.PixelFormat]::Format8bppIndexed)
  $stride = $bd.Stride; $scan0 = $bd.Scan0
  $zeros = New-Object byte[] ($stride * $H)
  [System.Runtime.InteropServices.Marshal]::Copy($zeros, 0, $scan0, $zeros.Length)

  for ($i = 1; $i -lt $slices; $i++) {
    $kind = $plans[$i][0]
    if ($kind -eq 'empty') { continue }
    $label = $names[$i]
    if ([string]::IsNullOrWhiteSpace($label)) { continue }
    $fill = $plans[$i][1]; $mark = $plans[$i][2]; $outline = $plans[$i][3]
    $cl = $sliceCols[$i]
    $fs = $FontSize
    if ($kind -eq 'text') {
      $fs = [int][Math]::Min(15, [Math]::Floor(56 / [double]$label.Length))
      if ($fs -lt 11) { $fs = 11 }
    }
    $font = New-Object System.Drawing.Font($FontName, $fs, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)

    $tmp = New-Object System.Drawing.Bitmap($W, 50, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $tg = [System.Drawing.Graphics]::FromImage($tmp)
    $tg.Clear($bgCol)
    if ($kind -eq 'text') { $tg.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::SingleBitPerPixelGridFit }
    else { $tg.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias }
    $sz = $tg.MeasureString($label, $font, 1000, $sf)
    $tw = [int][Math]::Ceiling($sz.Width); $th = [int][Math]::Ceiling($sz.Height)
    $pw = $tw + 8; if ($pw -gt $W) { $pw = $W }
    $ph = 16; if (($th + 3) -gt $ph) { $ph = $th + 3 }
    $px = [int](($W - $pw) / 2); $py = 2
    $tx = $px + ($pw - $tw) / 2.0; $ty = $py + ($ph - $th) / 2.0
    if ($kind -eq 'plaque') {
      $tb = New-Object System.Drawing.SolidBrush($fill); $tg.FillRectangle($tb, $px, $py, $pw, $ph); $tb.Dispose()
    }
    if ($kind -eq 'text' -and $outline -ne $null) {
      $ob = New-Object System.Drawing.SolidBrush($outline)
      foreach ($o in @(@(-1, -1), @(-1, 0), @(-1, 1), @(0, -1), @(0, 1), @(1, -1), @(1, 0), @(1, 1))) {
        $tg.DrawString($label, $font, $ob, ($tx + $o[0]), ($ty + $o[1]), $sf)
      }
      $ob.Dispose()
    }
    $fb = New-Object System.Drawing.SolidBrush($mark)
    $tg.DrawString($label, $font, $fb, $tx, $ty, $sf)
    $fb.Dispose(); $tg.Dispose(); $font.Dispose()

    for ($y = 0; $y -lt 50; $y++) {
      $rowOff = ($i * 50 + $y) * $stride
      for ($x = 0; $x -lt $W; $x++) {
        $key = RGB $tmp.GetPixel($x, $y).ToArgb()
        if ($key -eq $bgRGB) { continue }
        if ($indexOf.ContainsKey($key)) { $ix = [int]$indexOf[$key] }
        else {
          $bd2 = [int]::MaxValue; $ix = 0
          $cr = ($key -shr 16) -band 0xFF; $cg = ($key -shr 8) -band 0xFF; $cb = $key -band 0xFF
          for ($q = 0; $q -lt $cl.Count; $q++) {
            $c2 = $palList[$cl[$q]]
            $dr = $cr - $c2.R; $dg = $cg - $c2.G; $db = $cb - $c2.B
            $d = $dr * $dr + $dg * $dg + $db * $db
            if ($d -lt $bd2) { $bd2 = $d; $ix = $cl[$q] }
          }
        }
        [System.Runtime.InteropServices.Marshal]::WriteByte($scan0, $rowOff + $x, [byte]$ix)
      }
    }
    $tmp.Dispose()
  }

  $out.UnlockBits($bd)
  $out.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
  Write-Host ("   saved -> " + $path + "   palette_used=" + $palList.Count)
  $out.Dispose()
}
Write-Host 'DONE'
