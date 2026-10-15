$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$out = Join-Path $root '_tm07_report.txt'
$zhDir = Join-Path $root 'zh'
$sb = New-Object System.Text.StringBuilder

# Build translation memory from sibling outputs
$tm = @{}
$conf = New-Object System.Collections.ArrayList
foreach ($f in (Get-ChildItem $zhDir -Filter 'part-*.tsv' | Sort-Object Name)) {
    $t = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
    $lines = $t -split "`r`n|`n"
    foreach ($ln in $lines) {
        if ($ln -eq '') { continue }
        $parts = $ln -split "`t"
        if ($parts.Count -ne 2) { continue }
        $src = $parts[0]; $dst = $parts[1]
        if ($dst -eq '' -or $dst -eq $src) { continue }
        if ($tm.ContainsKey($src)) {
            if ($tm[$src] -ne $dst) { [void]$conf.Add("$src || $($tm[$src]) || $dst") }
        } else {
            $tm[$src] = $dst
        }
    }
}
[void]$sb.AppendLine("TM entries: $($tm.Count)  conflicts: $($conf.Count)")
[void]$sb.AppendLine("=== CONFLICTS ===")
foreach ($c in $conf) { [void]$sb.AppendLine($c) }

$inPath = Join-Path $root 'chunks\chunk-07.tsv'
$txt = [System.IO.File]::ReadAllText($inPath, [System.Text.Encoding]::UTF8)
$inLines = ($txt -split "`n") | ForEach-Object { $_.TrimEnd("`r") }
if ($inLines[-1] -eq '') { $inLines = $inLines[0..($inLines.Count-2)] }
[void]$sb.AppendLine("=== CHUNK-07 TM HITS (input lines: $($inLines.Count)) ===")
$i = 0
foreach ($ln in $inLines) {
    $i++
    if ($tm.ContainsKey($ln)) {
        [void]$sb.AppendLine("$i`t$ln`t=>`t$($tm[$ln])")
    }
}
[void]$sb.AppendLine("=== END ===")
[System.IO.File]::WriteAllText($out, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
"written $out"
