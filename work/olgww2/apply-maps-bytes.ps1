# ============================================================
#  Byte-level line-number map applier
#  ------------------------------------------------------------
#  Why not the plain apply-maps.ps1: single-byte source files may contain
#  CP1252 accented characters (o-umlaut, e-umlaut, n-tilde ...) which have
#  NO GBK representation. Re-encoding the whole file therefore fails.
#
#  This version works on raw bytes:
#    - lines listed in the maps  -> encoded as GBK (they are Chinese)
#    - all other lines           -> original bytes preserved untouched
#  Result: English/accented lines stay byte-identical to the original.
#
#  Usage: .\apply-maps-bytes.ps1 -Source <orig> -Maps a.tsv,b.tsv -Out <result>
# ============================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string[]]$Maps,
    [Parameter(Mandatory = $true)][string]$Out
)

$ErrorActionPreference = 'Stop'

$gbk    = [Text.Encoding]::GetEncoding(936)
$utf8No = New-Object Text.UTF8Encoding($false)

if (-not (Test-Path $Source)) { throw "Source not found: $Source" }

# ---------- 1. load maps ----------
$map  = @{}
$errs = New-Object System.Collections.Generic.List[string]
foreach ($m in $Maps) {
    if (-not (Test-Path $m)) { Write-Host ("  map missing, skipped: {0}" -f $m) -ForegroundColor Yellow; continue }
    $mr = $utf8No.GetString([IO.File]::ReadAllBytes($m))
    $n = 0
    foreach ($l in ($mr -split "\r?\n")) {
        if ($l.Trim().Length -eq 0) { continue }
        $p = $l.Split('|', 2)
        if ($p.Count -ne 2) { $errs.Add("bad format: $l"); continue }
        $no = 0
        if (-not [int]::TryParse($p[0].Trim(), [ref]$no)) { $errs.Add("bad line no: $l"); continue }
        if ($map.ContainsKey($no)) { $errs.Add("duplicate line no: $no"); continue }
        $map[$no] = $p[1]
        $n++
    }
    Write-Host ("  loaded {0,5} entries from {1}" -f $n, (Split-Path $m -Leaf))
}
Write-Host ("Map total: {0}" -f $map.Count) -ForegroundColor Cyan

# ---------- 2. split source into raw byte-lines ----------
# Split on LF and strip a trailing CR, so BOTH crlf and bare-lf line endings
# are handled (some efile files contain a few bare-LF lines). Output is written
# uniformly with CRLF, which is what the engine documentation requires.
$bytes = [IO.File]::ReadAllBytes($Source)
$lines = New-Object System.Collections.Generic.List[byte[]]
$cur   = New-Object System.Collections.Generic.List[byte]
for ($i = 0; $i -lt $bytes.Length; $i++) {
    if ($bytes[$i] -eq 10) {
        if ($cur.Count -gt 0 -and $cur[$cur.Count - 1] -eq 13) { $cur.RemoveAt($cur.Count - 1) }
        $lines.Add($cur.ToArray()); $cur.Clear()
    }
    else { $cur.Add($bytes[$i]) }
}
$lines.Add($cur.ToArray())          # last line (may be empty)
$total = $lines.Count
Write-Host ("Source   : {0}" -f $Source)
Write-Host ("Lines    : {0}" -f $total)

# ---------- 3. apply ----------
$applied  = 0
$outBytes = New-Object System.Collections.Generic.List[byte]
for ($i = 0; $i -lt $total; $i++) {
    $no = $i + 1
    if ($map.ContainsKey($no)) {
        $outBytes.AddRange($gbk.GetBytes($map[$no]))
        $applied++
    }
    else {
        $outBytes.AddRange($lines[$i])
    }
    if ($i -lt $total - 1) { $outBytes.Add(13); $outBytes.Add(10) }
}
Write-Host ("Applied  : {0} lines" -f $applied) -ForegroundColor Green

foreach ($no in $map.Keys) {
    if ($no -lt 1 -or $no -gt $total) { $errs.Add("line no out of range: $no (total $total)") }
}

# ---------- 4. write ----------
$outDir = Split-Path -Parent $Out
if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
[IO.File]::WriteAllBytes($Out, $outBytes.ToArray())

$outLines = ([Text.Encoding]::GetEncoding(28591).GetString([IO.File]::ReadAllBytes($Out))) -split "`r`n"
Write-Host ("Written  : {0} ({1} bytes, {2} lines)" -f $Out, (Get-Item $Out).Length, $outLines.Count) -ForegroundColor Green
if ($outLines.Count -ne $total) { $errs.Add("LINE COUNT MISMATCH: source $total vs output $($outLines.Count)") }
else { Write-Host 'Line count: identical OK' -ForegroundColor Green }

# CJK count (decode only the mapped lines to avoid noise from accented bytes)
$cjk = 0
foreach ($no in $map.Keys) { $cjk += ([regex]::Matches($map[$no], '[\u4e00-\u9fff]')).Count }
Write-Host ("CJK chars in mapped lines: {0}" -f $cjk)

Write-Host ''
if ($errs.Count -gt 0) {
    Write-Host ("{0} issue(s):" -f $errs.Count) -ForegroundColor Yellow
    $errs | Select-Object -First 30 | ForEach-Object { Write-Host ("  " + $_) -ForegroundColor Yellow }
} else { Write-Host 'No issues.' -ForegroundColor Green }
Write-Host ''
