param([string]$OutDir, [switch]$All)
if(-not $OutDir){ throw 'OutDir required' }
$ErrorActionPreference='Stop'
$srcDir='D:\OpenPG2\EFILE_OLGWW2\SCENARIO'
$names=@(
 '18days.txt','18days0.txt','18days0bv.txt','18days0i.txt','18days0l.txt','18days0tv.txt','18days0v.txt',
 '18days1.txt','18days1bv.txt','18days1i.txt','18days1l.txt','18days1tv.txt','18days1v.txt',
 '18days2.txt','18days2bv.txt','18days2i.txt','18days2l.txt','18days2tv.txt','18days2v.txt',
 '18days3.txt','18days3bv.txt','18days3i.txt','18days3l.txt','18days3tv.txt','18days3v.txt',
 '18days10.txt','18days10bv.txt','18days10i.txt','18days10l.txt','18days10tv.txt','18days10v.txt',
 '18days11.txt','18days11bv.txt','18days11i.txt','18days11l.txt','18days11tv.txt','18days11v.txt'
)
$enc=[Text.Encoding]::GetEncoding(1252)
$utf8=New-Object Text.UTF8Encoding($false)
$gbk=[Text.Encoding]::GetEncoding(936)
$rows=@()
foreach($orig in $names){
    $f = Join-Path $OutDir ($orig + '.utf8.txt')
    if(-not (Test-Path $f)){ $rows += [pscustomobject]@{File=$orig;SrcLines=0;OutLines=0;OK=$false;Note='MISSING OUTPUT'}; continue }
    $s = $enc.GetString([IO.File]::ReadAllBytes((Join-Path $srcDir $orig)))
    $b = [IO.File]::ReadAllBytes($f)
    $bom = ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)
    $t = $utf8.GetString($b)
    $sl = $s -split "`r`n|`n"
    $tl = $t -split "`r`n|`n"
    # ignore trailing whitespace-only lines (they are pure formatting)
    while($sl.Count -gt 0 -and $sl[$sl.Count-1] -match '^\s*$'){ $sl = $sl[0..($sl.Count-2)] }
    while($tl.Count -gt 0 -and $tl[$tl.Count-1] -match '^\s*$'){ $tl = $tl[0..($tl.Count-2)] }
    $notes=@()
    if($sl.Count -ne $tl.Count){ $notes += ("LINES src=$($sl.Count) out=$($tl.Count)") }
    if($bom){ $notes += 'BOM' }
    try { [void]$gbk.GetBytes($t) } catch { $notes += 'NOT-GBK' }
    $cjk=([regex]::Matches($t,'[\u4e00-\u9fff]')).Count
    $nonws=($t -replace '\s','').Length
    $ratio = if($nonws -gt 0){[Math]::Round($cjk/$nonws,3)}else{0}
    if($ratio -lt 0.3){ $notes += "LOWCJK=$ratio" }
    $n=[Math]::Min($sl.Count,$tl.Count)
    for($i=0;$i -lt $n;$i++){
        $a=([regex]::Matches($sl[$i],'/')).Count
        $c=([regex]::Matches($tl[$i],'/')).Count
        if($a -ne $c){ $notes += ("L{0} slash {1}->{2} SRC[{3}] OUT[{4}]" -f ($i+1),$a,$c,$sl[$i],$tl[$i]) }
    }
    $rows += [pscustomobject]@{File=$orig;SrcLines=$sl.Count;OutLines=$tl.Count;OK=($notes.Count -eq 0);Note=($notes -join ' | ')}
}
$rows | Format-Table File,SrcLines,OutLines,OK,Note -AutoSize -Wrap
$bad=@($rows | Where-Object { -not $_.OK })
"total=$($rows.Count) ok=$(@($rows | Where-Object {$_.OK}).Count) problems=$($bad.Count)"
if($bad.Count){ ''; 'PROBLEM DETAIL:'; foreach($r in $bad){ "[$($r.File)] $($r.Note)" } }
