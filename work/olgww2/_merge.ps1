$ErrorActionPreference='Stop'
$outDir='D:\DSH\军事游戏汉化\work\olgww2'

# --- rebuild my part with the 1178 fix ---
$src=Get-Content "$outDir\_mine-src.txt" -Encoding UTF8
$rangeStarts=@(838,869,900,931,962,1117,1148,1179,1427,1458,1489)
$expected=@(31,31,31,31,31,31,31,31,31,31,31)
if($src.Count -ne 341){ throw "src count $($src.Count)" }
$idx=0; $out=New-Object System.Collections.Generic.List[string]
for($r=0;$r -lt $rangeStarts.Count;$r++){
  for($i=0;$i -lt $expected[$r];$i++){
    $out.Add("$($rangeStarts[$r]+$i)|$($src[$idx])"); $idx++
  }
}
$enc=New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllLines("$outDir\_part-mine.tsv",$out,$enc)

# --- merge all 5 parts ---
$parts=@('_part-mine.tsv','_part-es.tsv','_part-fa.tsv','_part-pt-th.tsv','_part-et.tsv')
$all=@{}
foreach($p in $parts){
  $f=Join-Path $outDir $p
  if(-not (Test-Path $f)){ throw "missing $f" }
  foreach($ln in (Get-Content $f -Encoding UTF8)){
    if($ln -match '^\s*$'){ continue }
    if($ln -notmatch '^(\d+)\|(.+)$'){ throw "bad line in ${p}: $ln" }
    $n=[int]$Matches[1]; $v=$Matches[2]
    if($v -match '\|'){ throw "extra pipe at $n" }
    if($all.ContainsKey($n)){ throw "duplicate line $n ($p)" }
    $all[$n]=$v
  }
}
$keys=$all.Keys | Sort-Object
Write-Output "merged entries: $($keys.Count)  range: $($keys[0]) - $($keys[-1])"

# coverage check: every line in 776-1519 must be covered exactly once
$missing=@()
for($n=776;$n -le 1519;$n++){ if(-not $all.ContainsKey($n)){ $missing+=$n } }
Write-Output "missing lines: $($missing.Count)"
if($missing.Count -gt 0){ Write-Output ($missing -join ',') }

# validate against source
$cp=[Text.Encoding]::GetEncoding(1252)
$lines=($cp.GetString([IO.File]::ReadAllBytes('D:\OpenPG2\EFILE_OLGWW2\names.txt'))) -split "\r?\n"
$emptyOrDup=0
foreach($k in $keys){
  $o=$lines[$k-1]
  if($o.Trim() -eq ''){ Write-Output "EMPTY SOURCE at $k"; $emptyOrDup++ }
  if($all[$k] -eq $o){ Write-Output "UNCHANGED at $k : $o"; $emptyOrDup++ }
}
Write-Output "problems: $emptyOrDup"

$final=$keys | ForEach-Object { "$_|$($all[$_])" }
[IO.File]::WriteAllLines("$outDir\names-map-2.tsv",$final,$enc)
$b=[IO.File]::ReadAllBytes("$outDir\names-map-2.tsv")
Write-Output "final bytes: $($b.Length)  first3: $($b[0..2] -join ',')"
Write-Output "hasBOM: $($b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)"
