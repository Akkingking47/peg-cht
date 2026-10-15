# ---------------------------------------------------------------- run
$results=@{}
$report=@()
foreach($n in $NAMES){
  $src=Join-Path $SRC $n
  if(-not (Test-Path -LiteralPath $src)){ $report+="MISSING $n"; continue }
  $raw=[Text.Encoding]::GetEncoding(1252).GetString([IO.File]::ReadAllBytes($src))
  $nl = if($raw -match "`r`n"){"`r`n"} else {"`n"}
  $lines = $raw -split "`r?`n"
  $out=@()
  foreach($l in $lines){
    $t=$l.Trim()
    if($t -eq ''){ $out+= ''; continue }
    $tr=TLine $l
    $out+=$tr
    $latin=[regex]::Matches($tr,'[A-Za-z]{3,}').Count
    if($latin -ge 2){ $report += ("{0} :: {1} ==> {2}" -f $n,$l.Trim(),$tr) }
  }
  $results[$n]=($out -join $nl)
}
[IO.File]::WriteAllText('D:\DSH\军事游戏汉化\work\olgww2\_seg5_result.json',($results|ConvertTo-Json -Depth 3),(New-Object Text.UTF8Encoding($false)))
$report | Set-Content 'D:\DSH\军事游戏汉化\work\olgww2\_seg5_residual.txt' -Encoding UTF8
"translated=$($results.Count) residual=$($report.Count)"