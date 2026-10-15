# ============================================================
#  Apply line-number translation maps onto a single-byte source file
#  Usage:
#    .\apply-maps.ps1 -Source <orig> -Maps a.tsv,b.tsv -Out <result>
#  Map format (UTF-8):   <lineNumber>|<translated text>
#  - Source is read as CP1252 (single byte), result written as GBK (936)
#  - Lines not present in the maps are kept verbatim -> row structure preserved
# ============================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string[]]$Maps,
    [Parameter(Mandatory = $true)][string]$Out
)

$ErrorActionPreference = 'Stop'

$cp        = [Text.Encoding]::GetEncoding(1252)
$gbk       = [Text.Encoding]::GetEncoding(936)
$gbkStrict = [Text.Encoding]::GetEncoding(936, [Text.EncoderFallback]::ExceptionFallback, [Text.DecoderFallback]::ExceptionFallback)
$utf8No    = New-Object Text.UTF8Encoding($false)

if (-not (Test-Path $Source)) { throw "Source not found: $Source" }

$lines = ($cp.GetString([IO.File]::ReadAllBytes($Source))) -split "`r?`n"
$total = $lines.Count
Write-Host ("Source   : {0}" -f $Source)
Write-Host ("Lines    : {0}" -f $total)

# ---------- load maps ----------
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
        if ($no -lt 1 -or $no -gt $total) { $errs.Add("line no out of range: $no (total $total)"); continue }
        if ($map.ContainsKey($no)) { $errs.Add("duplicate line no: $no"); continue }
        $map[$no] = $p[1]
        $n++
    }
    Write-Host ("  loaded {0,5} entries from {1}" -f $n, (Split-Path $m -Leaf))
}
Write-Host ("Map total: {0}" -f $map.Count) -ForegroundColor Cyan

# ---------- apply ----------
$applied = 0
foreach ($no in ($map.Keys | Sort-Object)) {
    $old = $lines[$no - 1]
    if ([string]::IsNullOrWhiteSpace($old)) { $errs.Add("line $no is blank, skipped"); continue }
    if ($old -match '[\u4e00-\u9fff]')      { $errs.Add("line $no already Chinese, skipped"); continue }
    if ($old -match '^VERSION')             { $errs.Add("line $no is VERSION marker, skipped"); continue }
    $lines[$no - 1] = $map[$no]
    $applied++
}
Write-Host ("Applied  : {0} lines" -f $applied) -ForegroundColor Green

# ---------- write ----------
$text = $lines -join "`r`n"
try { [void]$gbkStrict.GetBytes($text) }
catch {
    Write-Host 'ERROR: characters not representable in GBK:' -ForegroundColor Red
    foreach ($ch in $text.ToCharArray() | Select-Object -Unique) {
        try { [void]$gbkStrict.GetBytes([string]$ch) } catch { Write-Host ("   '{0}' U+{1:X4}" -f $ch, [int][char]$ch) -ForegroundColor Red }
    }
    throw 'aborted, nothing written'
}

$outDir = Split-Path -Parent $Out
if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
[IO.File]::WriteAllBytes($Out, $gbk.GetBytes($text))

$chk = ($cp.GetString([IO.File]::ReadAllBytes($Out))) -split "`r?`n"
Write-Host ("Written  : {0} ({1} bytes, {2} lines)" -f $Out, (Get-Item $Out).Length, $chk.Count) -ForegroundColor Green

# ---------- report ----------
if ($chk.Count -ne $total) { $errs.Add("LINE COUNT MISMATCH: source $total vs output $($chk.Count)") }
else { Write-Host 'Line count: identical OK' -ForegroundColor Green }

$cjk = ([regex]::Matches($text, '[\u4e00-\u9fff]')).Count
Write-Host ("CJK chars in output: {0}" -f $cjk)

Write-Host ''
if ($errs.Count -gt 0) {
    Write-Host ("{0} issue(s):" -f $errs.Count) -ForegroundColor Yellow
    $errs | Select-Object -First 30 | ForEach-Object { Write-Host ("  " + $_) -ForegroundColor Yellow }
} else {
    Write-Host 'No issues.' -ForegroundColor Green
}
Write-Host ''
