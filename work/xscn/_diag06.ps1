$p = Join-Path $PWD 'work\xscn\chunks\chunk-06.tsv'
$t = [System.IO.File]::ReadAllText($p, [System.Text.Encoding]::UTF8)
$lines = $t -split [string][char]10
"count=$($lines.Count)"
for ($i = 0; $i -lt $lines.Count; $i++) {
    $l = $lines[$i].TrimEnd([char]13)
    if ($l -ne $l.TrimEnd(' ') -or $l.Contains('  ') -or $l -ne $l.TrimStart(' ')) {
        "WS line $($i+1): <$l>"
    }
}
"--- non-ascii lines ---"
for ($i = 0; $i -lt $lines.Count; $i++) {
    $l = $lines[$i].TrimEnd([char]13)
    if ($l -match '[^\x00-\x7F]') {
        "NA line $($i+1): <$l>"
    }
}
