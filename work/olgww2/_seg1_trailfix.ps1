param([string]$OutDir)
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
$fixed=0
foreach($orig in $names){
    $f = Join-Path $OutDir ($orig + '.utf8.txt')
    if(-not (Test-Path $f)){ continue }
    $s = $enc.GetString([IO.File]::ReadAllBytes((Join-Path $srcDir $orig)))
    $m = [regex]::Match($s, '(\r\n|\n)+$')
    $trailCount = ([regex]::Matches($m.Value, '\n')).Count
    $t = $utf8.GetString([IO.File]::ReadAllBytes($f))
    $t2 = ($t -replace '(\r\n|\n)+$','') + ("`n" * $trailCount)
    if($t2 -cne $t){
        [IO.File]::WriteAllBytes($f, $utf8.GetBytes($t2))
        $fixed++
        "normalized trailing newlines: $orig (src trailing NLs=$trailCount)"
    }
}
"normalized files=$fixed"
