# ---------------------------------------------------------------- structure parser
$UWORD=@(
 'Div.','Div','Division','Bde.','Bde','Brigade','Bn.','Bn','Btn.','Btn','Battalion','B/','B.','Rgt.','Rgt','Regiment',
 'R/','R','Column','Corps','Legion','Cav.Div.','Cav.Div','Cav.R','Cav.','Cav','CD','MR','Pz','FLAK','SC','MB',
 'Tk.Btn.','Tk.Btn','Tk.Bn.','Tk.Bn','TkBn','Tk','TkB','AR','At','Art','Aty','Aty.','AtyBtn','AtyBtm','AtyBn',
 'AA','AT','Eng.','Eng','EngBtn','Rec.','Rec','Para.','Para','Ind.','Ind','Mech.','Mech','Sqd.','Sqd',
 'HQ','Tact.','Ftr.','Ftr-Bomb.','Ftr-Escort','Bomb.','AABtn','ABtn','AABtn.','Field','Works','Security',
 'Guerrilla','Militia','Commando','Army','Group','Route','Force','Att.','Attach.','Attachment','Reserves',
 'Defensive','Line','Coastal','Defense','Defenses','Air','Div','Port','EXIT','PLAYER','NOTE','Historically','UN','Task',
 'Airfield','Point','Evacuation','Installation','Radar','Soviet','Support','Weapons','Regular','Guards','Bridging'
)
function Get-UWord([string]$v){
  $x=$v.Trim()
  if($x -eq ''){ return $null }
  foreach($w in $UWORD){ if($x -ieq $w){ return $w } }
  return $null
}
function Conv-Unit([string]$seg){
  $t=$seg.Trim()
  if($t -eq ''){ return '' }
  if($t -eq '-'){ return '' }
  if($t -eq 'n/a'){ return '' }
  # bracketed body: translate inner lexically
  if($t -match '^\[(.+)\]$'){
    $inner=$Matches[1]
    return '['+ (Conv-Lex (Conv-Struct $inner)) +']'
  }
  $parts=@()
  foreach($p in ($t -split '[ /]+')){ if($p.Trim() -ne ''){ $parts+=$p.Trim() } }
  # pure number -> 第N
  if($parts.Count -eq 1 -and $parts[0] -match '^[0-9]+$'){ return '第'+$parts[0] }
  # number + single word (e.g. "22 Pz", "9/5 R", "XIII Army")
  if($parts.Count -eq 2 -and $parts[0] -match '^[0-9XIV]+(/[0-9]+)?$'){
    $w=Get-UWord $parts[1]
    if($w -ne $null){
      $n=$parts[0]
      if($n -match '^[IVX]+$'){ $n=[string](RomanToInt $n) }
      $n=$n -replace '/','/'
      switch -regex ($w){
        '^R/|^R$'  { return '第'+$n+'团' }
        '^Div'     { return '第'+$n+'师' }
        '^Bde|^Brigade' { return '第'+$n+'旅' }
        '^Bn|^Btn|^B$' { return '第'+$n+'营' }
        '^Corps'   { return '第'+$n+'军' }
        '^Army'    { return '第'+$n+'集团军' }
        '^Cav'     { return '第'+$n+'骑兵' }
        '^CD'      { return '第'+$n+'骑兵师' }
        '^MR'      { return '第'+$n+'摩步师' }
        '^Pz'      { return '第'+$n+'装甲' }
        '^Legion'  { return '第'+$n+'军团' }
        '^Column'  { return '第'+$n+'纵队' }
        '^Tk|^TkB' { return '第'+$n+'坦克' }
        '^AR|^Aty|^Art|^At$' { return '第'+$n+'炮兵' }
        '^AA'      { return '第'+$n+'高射炮' }
        '^Eng'     { return '第'+$n+'工兵' }
        '^Rec'     { return '第'+$n+'侦察' }
        '^Para'    { return '第'+$n+'伞兵' }
        '^Ind'     { return '第'+$n+'独立' }
        '^Mech'    { return '第'+$n+'机械化' }
        '^Sqd'     { return '第'+$n+'中队' }
        '^Div'     { return '第'+$n+'师' }
        default    { return '第'+$n+' '+(Conv-Lex $w) }
      }
    }
  }
  # leading number + rest-word
  if($parts.Count -ge 2 -and $parts[0] -match '^[0-9]+(/[0-9]+)?$' -and $parts[1] -notmatch '^[0-9]+$'){
    $n=$parts[0]
    $w=Get-UWord $parts[1]
    if($w -ne $null){
      $rest=($parts[2..($parts.Count-1)] -join ' ')
      $head=''
      switch -regex ($w){
        '^R/|^R$'  { $head='第'+$n+'团' }
        '^Div'     { $head='第'+$n+'师' }
        '^Bde'     { $head='第'+$n+'旅' }
        '^Bn|^Btn' { $head='第'+$n+'营' }
        '^Corps'   { $head='第'+$n+'军' }
        '^Cav'     { $head='第'+$n+'骑兵' }
        '^CD'      { $head='第'+$n+'骑兵师' }
        '^MR'      { $head='第'+$n+'摩步师' }
        '^Pz'      { $head='第'+$n+'装甲' }
        '^Tk'      { $head='第'+$n+'坦克' }
        default    { $head='第'+$n+' '+(Conv-Lex $w) }
      }
      if($rest -ne ''){ $head = $head + (Conv-Unit $rest) }
      return $head
    }
  }
  # standalone unit word
  $w0=Get-UWord $parts[0]
  if($w0 -ne $null){
    $rest=($parts[1..($parts.Count-1)] -join ' ')
    $head=''
    switch -regex ($w0){
      '^R/|^R$'  { $head='团' }
      '^Div'     { $head='师' }
      '^Bde'     { $head='旅' }
      '^Bn|^Btn' { $head='营' }
      '^Corps'   { $head='军' }
      '^Army'    { $head='集团军' }
      '^Cav'     { $head='骑兵' }
      '^CD'      { $head='骑兵师' }
      '^MR'      { $head='摩步师' }
      '^Pz'      { $head='装甲' }
      '^Tk|^TkB' { $head='坦克' }
      '^AR|^Aty|^Art|^At$' { $head='炮兵' }
      '^AA'      { $head='高射炮' }
      '^Eng'     { $head='工兵' }
      '^Rec'     { $head='侦察' }
      '^Para'    { $head='伞兵' }
      '^Ind'     { $head='独立' }
      '^Mech'    { $head='机械化' }
      '^Sqd'     { $head='中队' }
      default    { $head=(Conv-Lex $w0) }
    }
    if($rest -ne ''){ $head = $head + (Conv-Unit $rest) }
    return $head
  }
  # fallback: lexical
  return Conv-Lex ($parts -join ' ')
}
function RomanToInt([string]$rn){
  $v=0;$p=0;$map=@{'I'=1;'V'=5;'X'=10}
  for($i=$rn.Length-1;$i -ge 0;$i--){ $c=$map[$rn[$i].ToString()]; if($c -lt $p){$v-=$c}else{$v+=$c;$p=$c} }
  return $v
}
function Conv-Lex([string]$s){
  if($s -eq ''){ return '' }
  $keys=@($MAP.Keys | Sort-Object { -$_.Length })
  foreach($k in $keys){
    if($k -notmatch '[A-Za-z]'){ continue }
    $pat='(?<![A-Za-z])'+[regex]::Escape($k)+'(?![A-Za-z])'
    $s=[regex]::Replace($s,$pat,$MAP[$k])
  }
  $s=[regex]::Replace($s,'\[([IVX]+)\]',{ param($m) '['+(RomanToInt $m.Groups[1].Value)+'军]' })
  $s=[regex]::Replace($s,'(?<![0-9])([0-9]+)\s*R(?=\s*/)','第$1团')
  # leftover latin words
  $s=[regex]::Replace($s,'[A-Za-z][A-Za-z''\.]*',{ param($m) Tok2 $m.Value })
  $s=$s -replace '\.',''
  $s=$s -replace '\s+',' '
  return $s.Trim()
}
function Tok2([string]$w){
  $raw=$w.Trim()
  $key=$raw.Trim(".'")
  if($key -eq ''){ return '' }
  if($key -match '^[A-Z][A-Z]+$'){ return $key }
  if($key.Length -le 2){ return $key }
  return (translit $key)
}
function Conv-Struct([string]$s){
  $segs=$s -split '/'
  $out=@()
  foreach($x in $segs){ $out += (Conv-Unit $x) }
  $r=($out | Where-Object { $_ -ne '' }) -join '/'
  return $r
}

# ---------------------------------------------------------------- line translate
function TLine([string]$line){
  $t=$line.Trim()
  if($t -eq ''){ return $line }
  if($MAP.ContainsKey($t)){ return $MAP[$t] }
  $lx=Conv-Lex $t
  if($t -match '^[0-9A-Za-z\s\.\-/_\[\]''&]+$'){
    $st=Conv-Struct $t
    if((CjkCount $st) -gt (CjkCount $lx)){ return $st }
  }
  if($lx -ne ''){ return $lx }
  return $t
}
