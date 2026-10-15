foreach ($n in @('part-02','part-04','part-05','part-10')) {
    $p = Join-Path $PWD "work\xscn\zh\$n.tsv"
    $b = [System.IO.File]::ReadAllBytes($p)
    $t = [System.Text.Encoding]::UTF8.GetString($b)
    $lines = $t -split [string][char]10
    $nonEmpty = @($lines | Where-Object { $_ -ne '' })
    $tabCounts = @{}
    foreach ($l in $nonEmpty) {
        $c = ([regex]::Matches($l, [char]9)).Count
        if ($tabCounts.ContainsKey($c)) { $tabCounts[$c]++ } else { $tabCounts[$c] = 1 }
    }
    $bom = ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)
    $crlf = ([regex]::Matches($t, [char]13 + [char]10)).Count
    "$n : bytes=$($b.Length) lines=$($lines.Count) nonEmpty=$($nonEmpty.Count) bom=$bom crlf=$crlf"
    "   tabHist: " + (($tabCounts.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Key)x$($_.Value)" }) -join ', ')
}
