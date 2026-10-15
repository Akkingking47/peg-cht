# ============================================================
#  Deploy translated OLGWW2 scenario texts into the efile TEXT-ZH folder
#  Source : work\olgww2\scenario\*.utf8.txt   (UTF-8, no BOM)
#  Target : EFILE_OLGWW2\TEXT-ZH\SCENARIO\*.txt (GBK, no BOM, CRLF)
#  Handles both draft namings:  xxx.utf8.txt  and  xxx.txt.utf8.txt
# ============================================================
[CmdletBinding()]
param(
    [string]$Efile = 'D:\OpenPG2\EFILE_OLGWW2'
)

$ErrorActionPreference = 'Stop'

$Src  = 'D:\DSH\军事游戏汉化\work\olgww2\scenario'
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
    # both namings -> original name
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
if ($empty.Count -gt 0) { Write-Host ("Empty drafts (skipped)  : {0}" -f $empty.Count); $empty | Select-Object -First 10 | ForEach-Object { "    " + $_ } }
if ($bad.Count   -gt 0) { Write-Host ("FAILED                  : {0}" -f $bad.Count);   $bad   | Select-Object -First 10 | ForEach-Object { "    " + $_ } }

# ---------- coverage ----------
$origNames = @(Get-ChildItem $Orig -Filter '*.txt' | ForEach-Object { $_.Name })
$doneNames = @(Get-ChildItem $Dst  -Filter '*.txt' -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
$missing   = @($origNames | Where-Object { $_ -notin $doneNames })

Write-Host ''
Write-Host ("Originals {0} / translated {1} / missing {2}" -f $origNames.Count, $doneNames.Count, $missing.Count)
if ($missing.Count -gt 0 -and $missing.Count -le 60) { Write-Host 'Missing:'; $missing | ForEach-Object { "    " + $_ } }
elseif ($missing.Count -gt 60) { Write-Host ('Missing (first 60): ' + (($missing | Select-Object -First 60) -join ', ')) }

# ---------- CJK ratio audit ----------
Write-Host ''
Write-Host 'CJK audit (files with <30% CJK):'
$susp = 0
foreach ($f in (Get-ChildItem $Dst -Filter '*.txt' -ErrorAction SilentlyContinue)) {
    $b = [IO.File]::ReadAllBytes($f.FullName)
    $t = $gbk.GetString($b)
    $cjk = ([regex]::Matches($t, '[\u4e00-\u9fff]')).Count
    $tot = ($t -replace '\s', '').Length
    if ($tot -gt 0 -and ($cjk / $tot) -lt 0.3) { $susp++; Write-Host ("    {0,-28} CJK={1} total={2}" -f $f.Name, $cjk, $tot) }
}
if ($susp -eq 0) { Write-Host '    none' -ForegroundColor Green }
Write-Host ''
