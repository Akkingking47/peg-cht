$ErrorActionPreference = 'Stop'
$inPath  = 'D:\DSH\鍐涗簨娓告垙姹夊寲\work\xscn\chunks\chunk-02.tsv'
$outPath = 'D:\DSH\鍐涗簨娓告垙姹夊寲\work\xscn\zh\part-02.tsv'
$map = Import-PowerShellDataFile -Path 'D:\DSH\鍐涗簨娓告垙姹夊寲\work\xscn\_map02.psd1'

$bytes = [System.IO.File]::ReadAllBytes($inPath)
$raw   = [System.Text.Encoding]::GetEncoding(28591).GetString($bytes)
# strip a leading UTF-8 BOM if any were present
if ($raw.Length -gt 0 -and $raw[0] -eq [char]0xFEFF) { $raw = $raw.Substring(1) }

$parts = $raw -split "`n", -1
if ($parts.Count -gt 0 -and $parts[$parts.Count-1] -eq '') { $parts = $parts[0..($parts.Count-2)] }

$latin1 = [System.Text.Encoding]::GetEncoding(28591)
$lines = New-Object System.Collections.Generic.List[string]
$newlines = New-Object System.Collections.Generic.List[string]
$missing = New-Object System.Collections.Generic.List[int]

$i = 0
foreach ($part in $parts) {
    $i++
    $nl = ''
    $core = $part
    if ($core.EndsWith("`r")) { $core = $core.Substring(0, $core.Length-1); $nl = "`r`n" }
    else { $nl = "`n" }
    # reverse the double-encoding: latin1 chars -> bytes -> utf8 text
    $recoded = [System.Text.Encoding]::UTF8.GetString($latin1.GetBytes($core))
    $lines.Add($recoded)
    $newlines.Add($nl)
}

# report lines not covered by the map (after decoding)
$unmapped = @()
for ($k = 0; $k -lt $lines.Count; $k++) {
    if (-not $map.ContainsKey($lines[$k])) { $unmapped += "$($k+1)`t$($lines[$k])" }
}
if ($unmapped.Count -gt 0) {
    "UNMAPPED COUNT = $($unmapped.Count)"
    $unmapped | ForEach-Object { $_ }
} else {
    "UNMAPPED COUNT = 0"
    $sb = New-Object System.Text.StringBuilder
    for ($k = 0; $k -lt $lines.Count; $k++) {
        [void]$sb.Append($map[$lines[$k]]).Append($newlines[$k])
    }
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($outPath, $sb.ToString(), $enc)
    "WROTE $outPath"
}
