$ErrorActionPreference = 'Stop'
$base = [string]([char]0x44 + [char]0x3A + [char]0x5C + [char]0x44 + [char]0x53 + [char]0x48 + [char]0x5C + [char]0x519B + [char]0x4E8B + [char]0x6E38 + [char]0x620F + [char]0x6C49 + [char]0x5316)
$inPath  = $base + '\work\xscn\chunks\chunk-02.tsv'
$outPath = $base + '\work\xscn\zh\part-02.tsv'
$mapPath = $base + '\work\xscn\_map02.psd1'

$map = Import-PowerShellDataFile -Path $mapPath
$bytes = [System.IO.File]::ReadAllBytes($inPath)
$raw   = [System.Text.Encoding]::GetEncoding(28591).GetString($bytes)
if ($raw.Length -gt 0 -and $raw[0] -eq [char]0xFEFF) { $raw = $raw.Substring(1) }

$parts = $raw -split "`n", -1
if ($parts.Count -gt 0 -and $parts[$parts.Count-1] -eq '') { $parts = $parts[0..($parts.Count-2)] }

$latin1 = [System.Text.Encoding]::GetEncoding(28591)
$lines = New-Object System.Collections.Generic.List[string]
$newlines = New-Object System.Collections.Generic.List[string]

foreach ($part in $parts) {
    $nl = "`n"
    $core = $part
    if ($core.EndsWith("`r")) { $core = $core.Substring(0, $core.Length-1); $nl = "`r`n" }
    $recoded = [System.Text.Encoding]::UTF8.GetString($latin1.GetBytes($core))
    $lines.Add($recoded)
    $newlines.Add($nl)
}

$unmapped = @()
for ($k = 0; $k -lt $lines.Count; $k++) {
    if (-not $map.ContainsKey($lines[$k])) { $unmapped += "$($k+1): $($lines[$k])" }
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
    "INLINES=$($lines.Count)"
}
