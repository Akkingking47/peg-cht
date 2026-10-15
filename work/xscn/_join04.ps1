$ErrorActionPreference = 'Stop'
$src = 'D:\DSH\军事游戏汉化\work\xscn\chunks\chunk-04.tsv'
$trf = 'D:\DSH\军事游戏汉化\work\xscn\_p4trans.txt'
$out = 'D:\DSH\军事游戏汉化\work\xscn\zh\part-04.tsv'

$s = [System.IO.File]::ReadAllLines($src, [System.Text.UTF8Encoding]::new($false))
$t = [System.IO.File]::ReadAllLines($trf, [System.Text.UTF8Encoding]::new($false))

"src lines : $($s.Count)"
"trans lines: $($t.Count)"
if ($s.Count -ne $t.Count) { throw 'LINE COUNT MISMATCH' }
if ($t.Count -ne 400) { throw 'expected 400' }

$bad = 0
for ($i = 0; $i -lt $s.Count; $i++) {
    $a = $s[$i]
    $b = $t[$i]
    if ($b.Length -eq 0) { "EMPTY TRANS line $($i+1)"; $bad++; continue }
    if ($b.Contains("`t")) { "TAB IN TRANS line $($i+1)"; $bad++; continue }
    foreach ($c in '/', '[', ']', '(', ')') {
        $ca = ([regex]::Matches($a, [regex]::Escape($c))).Count
        $cb = ([regex]::Matches($b, [regex]::Escape($c))).Count
        if ($ca -ne $cb) {
            $bad++
            "DELIM line $($i+1) : '$c' $ca -> $cb"
            "   SRC: $a"
            "   TR : $b"
        }
    }
}
"delimiter problems: $bad"
if ($bad -gt 0) { throw 'DELIMITER MISMATCH - aborting write' }

$sb = [System.Text.StringBuilder]::new()
for ($i = 0; $i -lt $s.Count; $i++) {
    [void]$sb.Append($s[$i]).Append("`t").Append($t[$i]).Append("`r`n")
}
[System.IO.File]::WriteAllText($out, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
"WROTE $out"
