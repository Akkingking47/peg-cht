$ErrorActionPreference = 'Stop'
$dst = 'D:\DSH\军事游戏汉化\work\olgww2\scenario'
$names = [IO.File]::ReadAllText('D:\DSH\军事游戏汉化\work\olgww2\_seg3_names.json', [Text.Encoding]::UTF8) | ConvertFrom-Json
# a plausible English word of >=3 letters that survived translation
$stop = 'the|and|your|you|with|for|will|must|have|are|our|his|her|its|from|this|that|they|their|there|here|not|but|all|any|can|may|should|would|could|been|were|was|has|had|does|did|into|over|under|out|off|upon|men|enemy|force|forces|army|attack|capture|take|hold|advance|victory|defeat|position|positions|line|lines|north|south|east|west|river|city|town|road|bridge|near|during|after|before|against|through|between|these|those|which|who|what|when|where|while|about|only|also|more|most|some|such|very|well|make|made|get|got|see|saw|come|came|go|went|give|gave|know|knew|think|thought|good|great|best|better|new|old|first|last|next|other|another|each|every|both|few|many|much|own|same|so|than|then|them|us|it'
$hits = @()
foreach ($n in $names) {
  $t = [IO.File]::ReadAllText((Join-Path $dst ($n + '.utf8.txt')), [Text.Encoding]::UTF8)
  foreach ($m in [regex]::Matches($t, '\b([A-Za-z]{3,})\b')) {
    $w = $m.Groups[1].Value.ToLower()
    if ($w -match "^($stop)$") { $hits += "{0} : {1}" -f $n, $m.Value }
  }
}
"english-word hits: $($hits.Count)"
$hits | Select-Object -Unique | ForEach-Object { $_ }
