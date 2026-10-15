# ============================================================
#  Deploy translated scenario texts into the efile TEXT-ZH folder
#  Source : work\openpg\scenario\*.utf8.txt   (UTF-8, no BOM)
#  Target : EFILE_OPENPG\TEXT-ZH\SCENARIO\*.txt (GBK, no BOM, CRLF)
#  ASCII-only source on purpose (avoids PowerShell 5.1 encoding pitfalls)
# ============================================================
[CmdletBinding()]
param(
    [string]$Efile = 'D:\OpenPG2\EFILE_OPENPG'
)

$ErrorActionPreference = 'Stop'

$Src  = 'D:\DSH\军事游戏汉化\work\openpg\scenario'
$Orig = Join-Path $Efile 'SCENARIO'
$Dst  = Join-Path $Efile 'TEXT-ZH\SCENARIO'

$utf8No    = New-Object Text.UTF8Encoding($false)
$gbk       = [Text.Encoding]::GetEncoding(936)
$gbkStrict = [Text.Encoding]::GetEncoding(936, [Text.EncoderFallback]::ExceptionFallback, [Text.DecoderFallback]::ExceptionFallback)

if (-not (Test-Path $Dst)) { New-Item -ItemType Directory -Path $Dst -Force | Out-Null }

$files = @(Get-ChildItem $Src -Filter '*.utf8.txt' -ErrorAction SilentlyContinue)
Write-Host ("Found translated drafts : {0}" -f $files.Count)

$ok = 0
$bad = New-Object System.Collections.Generic.List[string]
$empty = New-Object System.Collections.Generic.List[string]

foreach ($f in $files) {
    # Supported draft namings (subagents produced both due to an ambiguous spec):
    #   xxx.utf8.txt        and        xxx.txt.utf8.txt
    $name = $f.Name -replace '\.txt\.utf8\.txt$', '.txt'
    $name = $name   -replace '\.utf8\.txt$', '.txt'
    try {
        $t = $utf8No.GetString([IO.File]::ReadAllBytes($f.FullName))
        $t = ($t -replace "`r`n", "`n") -replace "`n", "`r`n"
        if ([string]::IsNullOrWhiteSpace($t)) { $empty.Add($name); continue }
        [void]$gbkStrict.GetBytes($t)
        [IO.File]::WriteAllBytes((Join-Path $Dst $name), $gbk.GetBytes($t))
        $ok++
    }
    catch {
        $bad.Add(("{0} : {1}" -f $name, $_.Exception.Message))
    }
}

Write-Host ("Deployed                : {0}" -f $ok)
if ($empty.Count -gt 0) { Write-Host ("Empty drafts (skipped)  : {0}" -f $empty.Count); $empty | ForEach-Object { "    " + $_ } }
if ($bad.Count   -gt 0) { Write-Host ("FAILED                  : {0}" -f $bad.Count);   $bad   | ForEach-Object { "    " + $_ } }

# ---------- coverage report ----------
$origNames = @(Get-ChildItem $Orig -Filter '*.txt' | ForEach-Object { $_.Name })
$doneNames = @(Get-ChildItem $Dst  -Filter '*.txt' -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
$missing   = @($origNames | Where-Object { $_ -notin $doneNames })

Write-Host ''
Write-Host ("Originals {0} / translated {1} / missing {2}" -f $origNames.Count, $doneNames.Count, $missing.Count)
if ($missing.Count -gt 0 -and $missing.Count -le 80) {
    Write-Host 'Missing:'
    $missing | ForEach-Object { "    " + $_ }
}

# ---------- sanity: encoding of deployed files ----------
Write-Host ''
Write-Host 'Encoding check (first 5 deployed):'
Get-ChildItem $Dst -Filter '*.txt' -ErrorAction SilentlyContinue | Select-Object -First 5 | ForEach-Object {
    $b = [IO.File]::ReadAllBytes($_.FullName)
    $bom = ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB)
    $cr = @($b | Where-Object { $_ -eq 13 }).Count
    $lf = @($b | Where-Object { $_ -eq 10 }).Count
    $isGbk = $true
    try { [void]$gbkStrict.GetString($b) } catch { $isGbk = $false }
    Write-Host ("    {0,-26} BOM={1,-6} CRLF={2,-6} GBK={3}" -f $_.Name, $bom, ($cr -eq $lf), $isGbk)
}
Write-Host ''
