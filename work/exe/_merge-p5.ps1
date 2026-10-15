$ErrorActionPreference = 'Stop'

$dir      = $PSScriptRoot
$srcPath  = Join-Path $dir 'todo-p5.txt'
$zhPath   = Join-Path $dir '_zh-p5.txt'
$outPath  = Join-Path $dir 'dlg-zh-p5.tsv'

$utf8 = New-Object System.Text.UTF8Encoding($false)

$src = [System.IO.File]::ReadAllLines($srcPath, $utf8)
$zh  = [System.IO.File]::ReadAllLines($zhPath, $utf8)

Write-Output ("src lines = " + $src.Count)
Write-Output ("zh  lines = " + $zh.Count)
if ($src.Count -ne 76) { throw "src count mismatch" }
if ($zh.Count -ne 76)  { throw "zh count mismatch" }

$out = New-Object System.Collections.Generic.List[string]
$bad = 0

for ($i = 0; $i -lt 76; $i++) {
    $line = $src[$i]
    $tab  = $line.IndexOf([char]9)
    if ($tab -lt 1) { throw ("line {0} has no tab" -f ($i + 1)) }
    $id = $line.Substring(0, $tab)
    $en = $line.Substring($tab + 1)
    $z  = $zh[$i]

    if ($z.Length -gt $en.Length) {
        $bad++
        Write-Output ("LENGTH-VIOLATION line {0} id={1} en={2} zh={3} : [{4}] -> [{5}]" -f ($i + 1), $id, $en.Length, $z.Length, $en, $z)
    }
    # preserve formatting tokens
    foreach ($tok in @('%s', '%d', '\n', '000,000')) {
        $inEn = $en.Contains($tok)
        $inZh = $z.Contains($tok)
        if ($inEn -ne $inZh) {
            $bad++
            Write-Output ("TOKEN-MISMATCH line {0} token={1} en={2} zh={3}" -f ($i + 1), $tok, $inEn, $inZh)
        }
    }
    $out.Add($line + [char]9 + $z)
}

if ($bad -gt 0) { throw ("validation failed with {0} problem(s); output NOT written" -f $bad) }

[System.IO.File]::WriteAllLines($outPath, $out, $utf8)

# ---- post-write verification ----
$bytes = [System.IO.File]::ReadAllBytes($outPath)
$bom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
Write-Output ("BOM present = " + $bom)

$chk = [System.IO.File]::ReadAllLines($outPath, $utf8)
Write-Output ("out lines = " + $chk.Count)

$maxRatio = 1.0
for ($i = 0; $i -lt $chk.Count; $i++) {
    $p = $chk[$i].Split([char]9)
    if ($p.Count -ne 3) { throw ("out line {0} does not have 3 columns" -f ($i + 1)) }
    if ($p[1] -cne $src[$i].Substring($src[$i].IndexOf([char]9) + 1)) {
        throw ("out line {0} english column not identical: [{1}] vs [{2}]" -f ($i + 1), $p[1], $src[$i])
    }
    $r = $p[2].Length / [double]$p[1].Length
    if ($r -gt $maxRatio) { $maxRatio = $r }
}
Write-Output ("all 76 english columns identical to source = True")
Write-Output ("max zh/en length ratio = " + [math]::Round($maxRatio, 3))
Write-Output ("WROTE " + $outPath)
