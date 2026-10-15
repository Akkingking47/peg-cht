$src='D:\DSH\军事游戏汉化\work\xscn\chunks\chunk-13.tsv'
$dst='D:\DSH\军事游戏汉化\work\xscn\zh\part-13.tsv'
$tab=[string][char]9
$si=[System.IO.File]::ReadAllText($src,[System.Text.Encoding]::UTF8) -split "`r`n"; $si=$si[0..($si.Count-2)]

$map=[ordered]@{
 'Aufkl.-Abt.'='侦察营';'Art.-Rgt.'='炮兵团';'Art.-Reg.'='炮兵团';'Art.-Abt.'='炮兵营';'Art.Grp.'='炮兵群'
 'Artillerie-Regiment'='炮兵团';'AR.Btn.'='炮兵团';'Aty.Btn.'='炮兵团';'Aty.Div.'='炮兵师';'AtyBtn'='炮兵营';'AtyBtm'='炮兵营'
 'AtyGrp.'='炮兵群';'AtyGrp'='炮兵群';'Aty.Grp.'='炮兵群';'Aty.Grp'='炮兵群'
 'Pz.Div.'='装甲师';'Cav.Div.'='骑兵师';'Gr. Kleist'='克莱斯特集群';'War Area'='战区'
 'Mechanised'='摩托化';'Regiment'='团';'Squadron'='中队';'Garrison'='守备部队'
 'Aty Bn'='炮兵营';'Aty R'='炮兵团';'Aty G'='炮兵群';'Art Bn'='炮兵营';'Art R'='炮兵团';'At R'='反坦克团'
 'Korps'='军';'Armee'='集团军';'Corps'='军';'Army'='集团军';'Grouping'='集群';'Brigade'='旅'
 'Forces'='部队';'Force'='部队';'ATR'='反坦克团';'AR'='炮兵团';'Aty'='炮兵';'Art'='炮兵';'AT'='反坦克'
 'SS-V'='@@SSV@@'
 'Independent'='独立';'Rifle'='步枪';'Rifle Brigade'='步枪旅';'Wing'='联队'
 'AK'='军';'AOK'='集团军';'ID'='步兵师';'Pz.'='装甲';'Cav.'='骑兵';'Col.'='纵队'
 'Btl.'='营';'Abt.'='营';'Bn'='营';'Rgt.'='团';'Res.'='预备';'Arm.'='装甲';'Bde'='旅';'Br'='旅';'R.'='团';'R'='团'
 'mot.'='摩托化'
}
$keys=@($map.Keys | Sort-Object -Property Length -Descending)

$lit=@{
1='Altafulla';2='Alte Oder';3='Alte Oder河';4='Alvise da Mosto';5='Alytus';6='Amaiur No.19/1 Bda./第1师';7='Amal河';8='Amatsu';9='Amberloop';10='Amfiklia';11='Amorebieta';12='Amphiteatre';13='Amsterdam-Rhine运河';14='Amtissa';15='Amuategi No.35/6 Bda./第2师'
16='Amur';17='Anbyon';18='Andrea Doria';19='Andreevo';20='Andrieseni';21='Andruschki';22='Anfa';23='Angat河';24='Anielin';25='Anju';26='Ankenes';27='Anlu';28='Annamajor';29='Ano';30='Ansong';31='Antelat'
32='Antonio Pigafetta';33='Antoniotto Usodimare';34='Antonovka';35='Antwerp [港口]';36='Antwerp [火车站]';37='Antwerpse Steenweg';38='ANV 2 No.23/1 Bda./第1师';39='ANV 3 No.68/10 Bda./第3师';40='ANV No.6/13 Bda./第2师';41='ANV No.6/第2纵队';42='Anyang';43='乐化';44='Aohima';45='APG';46='Apostag';47='Apostolove';48='Aq运河';49='Aq河';50='Aquila'
53='第185炮兵团/第185Folgore师/[X]';54='第190炮兵团/第90LD师/[非洲军]';55='第617炮兵团';57='Ar Ramadi';58='Ar Rutbah'
68='阿拉伯军团摩托化团';69='Araba No.14/5 Bda./第4师';70='Aramaio';71='Arana Goiri No.39/11 Bda./第2师';72='Arashi';73='Arba';74='Archangelowka';75='Archilla';76='Arciniega';77='Ardennes (K集群)';78='Ardleigh';79='Areta';80='Argecilla';81='Aringay';82='Arki-erdo (森林)';83='武装警察';84='Armentieres';85='Arneke';86='Arrazua';87='Arriondas';88='Arromanches-les-Bains';89="Arsen'evskii"
97="炮兵群/''A''师/[XIV]";98="炮兵群/''B''师/[XIV]";124='Artemissio'
131='Arzew';132='As Salman';133='As Samawah';134='Asagumo/第9驱逐舰';135='Asakaze';136='Ascari';137='Ascidera';138='Ascidera河';139='Asdod';140='Ashford机场';141='Ashingdon';142='Aslag岭';143='Aspeneset';144='AsSalt';145='Astene';146='Astigarraga';147='Asturias';148='Asua';149='反坦克第1P';154='反坦克Cuneense'
161='Atalandi';162='Ataran';163='atB/Habforce/阿拉伯军团';164='atB/HG D';165='atB/撒哈拉集群';166='罗家集';167='Atikara溪';171='配属FEF';172='炮兵第1P'
237='Atzibar';239='Audley End';240='Audun-le-Roman'
271='Aure河';272='Aurith';273='aux Livorno';274='Aveley';275='Avellaneda No.38/12 Bda./第2师';276='Averesti';277='Aviere';278='Avola';279='Aw Dheegle';280='Axel';281='Axelse Kreek';282='轴心国补给点';283='Ayevkur';284='Ayla Konstantinos';285='Ayla Marina';286='Ayla Trias';287='Ayn Taya';288='Azana No.7/5 Bda./第4师'
289='B';290='B连/KAR';291='B Melilla/第4旅/[1Agrp.]';292='B.Soltane';293='BA-10[1]';294='BA-64[4]';295='Bab el Qattara';296='Babonymegyer';297='Babu';298='Bachuan';299='Badgoski运河';300='Badiel河';301='Badka河';302='Badu';303='Baerenthal';304='Bagac';305='Bagac河';306='Bago-hegy (丘陵)';307='Bahlui';308='Bahr of Milh';309='Baie du Mont St. Michel';310='Bain-Tsagan山';311='Baisha'
312='Bakonycsernye';313='Bakonysarkany';314='Bakonyszentkiraly-Csesznek';315='Bakonyszombathely';316='Bakri';317='Balantay河';318='Balaton';319='Balatonalmadi';320='Balatonfoldvar';321='Balatonfured';322='Balatonfuzfo';323='Balatonkenese';324='Balatonszabadi';325='Balatonszarszo';326='Balatonvilagos';327='Balcad';328='Balikpapan船坞 (港口)';329='Balikpapan部队';330='Baliuag';331='Balyka'
332='Bamban';333='Bamban河';334='Bangkalsepula';335='Bani Suhaylah';336='Bania';337='Banina';338='Banino';339='Baodi';340='Baquio';341='Bar河';342='Baracaldo';343='Baracska';344='Baranovicze';345='Barany-cser (森林)';346='Barboeni';347='Barlad';348='Barnova';349='Barnsley';350='Barrages Cointet Ligne KW';351='Barrani简易机场';352="Barten'evka";353='Bartolomeo Colleoni'
354='Basabua';355='Basou';356='Basse Colme运河';357='Basse Come运河';358='Bassenge';359='Bastat al Ajrud';360='Baszkow';361='Bat.M/-/-/第6DO/[Ortiz]';362='Batalan河';363='Batchelor';364='Bathhurst Island传教站';365='炮兵驻防部队 ';366='Batufahat';367='Batugon';368='Baturino';369='Bayambuy';370='Bayiashan';371='Bayrak';372='Bazar';373='BC';374='BD';375='Bda. Vol. Santander/[S.Esteban]';376='Beach';377='滩头阵地'
380='Beda Fomm';381='Beernem';382='Beervelde';383='Beeskow';384='Beijing - Wuhan铁路';385='Beisfjord';386='Beisfjorden';387='Beketowka';388="Bel'bek";389="Bel'bek河";390='Belcesti';391="Bel'dugino";392='Belebelka';393='Belebzika';394='Belsele';395='Belsobarand';396='Belyi';397='Belyi Rast';398='Ben Gardane';399='Benfleet';400='Benghazi港'
}

$rxf=New-Object System.Collections.ArrayList
foreach($k in $keys){ [void]$rxf.Add($k) }
$rxall='(?<![A-Za-z\.\-])(' + (($keys | ForEach-Object { [regex]::Escape($_) }) -join '|') + ')(?![A-Za-z])'

$romanEvaluate=[System.Text.RegularExpressions.MatchEvaluator]{
  param($m)
  $r=$m.Groups[1].Value
  $t=@{I=1;V=5;X=10;L=50;C=100}
  $val=0;$prev=0
  for($q=$r.Length-1;$q -ge 0;$q--){ $cv=$t[[string]$r[$q]]; if($cv -lt $prev){$val-=$cv}else{$val+=$cv;$prev=$cv} }
  [string]$val
}

function ZhLine([string]$s){
  # phrase keys -> placeholders
  $ph=@{}
  $pi=0
  $pre=$s
  foreach($k in $keys){
    $pat='(?<![A-Za-z\.\-])'+[regex]::Escape($k)+'(?![A-Za-z])'
    $guard=0
    while([regex]::IsMatch($pre,$pat) -and $guard -lt 50){
      $tok="@@PH$pi@@"
      $ph[$tok]=$map[$k]
      $pre=[regex]::Replace($pre,$pat,[System.Text.RegularExpressions.MatchEvaluator]{ param($m) $tok },1)
      $pi++; $guard++
    }
  }
  # split into separator runs / content runs (structure preserved exactly)
  $units=[regex]::Matches($pre,'([ \t/\[\]\(\)-]+|[^ \t/\[\]\(\)-]+)')
  $sb=New-Object System.Text.StringBuilder
  foreach($u in $units){
    $t=$u.Value
    if($t -match '^[ \t/\[\]\(\)-]+$'){ [void]$sb.Append($t); continue }
    $v=$t
    # parenthesised roman-numeral designations keep their parentheses
    $v=[regex]::Replace($v,'\(([IVXL]+)\.\)',{ param($m) '(第' + [string](& { $r=$m.Groups[1].Value; $t=@{I=1;V=5;X=10;L=50;C=100}; $val=0;$prev=0; for($q=$r.Length-1;$q -ge 0;$q--){ $cv=$t[[string]$r[$q]]; if($cv -lt $prev){$val-=$cv}else{$val+=$cv;$prev=$cv} }; $val }) + '营)' })
    foreach($kk in $ph.Keys){ $v=$v.Replace($kk,$ph[$kk]) }
    $v=[regex]::Replace($v,'(?<![A-Za-z0-9\.\-])([IVXL]+)(?![A-Za-z0-9IVXL])',$romanEvaluate)
    [void]$sb.Append($v)
  }
  $z=$sb.ToString()
  # insert 第 before arabic numbers that designate formations
  $z=[regex]::Replace($z,'(?<![0-9A-Za-z第])([0-9]+) *(军|集团军|步兵师|装甲师|骑兵师|炮兵师|师|旅|团|营|纵队|战区|集群|部队|联队|中队|守备部队)','第$1$2')
  # number + AOK / ID / AK (German order: number first)
  $z=[regex]::Replace($z,'(?<![0-9A-Za-z\.])([0-9]+) *(AOK|ID|AK)(?![0-9A-Za-z])','第$1$2')
  # second sweep: German terms still present after the number
  $z=[regex]::Replace($z,'第([0-9]+)(AOK|ID|AK)','第$1' + '$2')
  $z=[regex]::Replace($z,'(?<![A-Za-z\.\-])(AOK|ID|AK)(?![A-Za-z])',{ param($m) $map[$m.Groups[1].Value] })
  $z=[regex]::Replace($z,'(?<![0-9第])(集团军|军|步兵师|师) *([0-9]+)(?![0-9])','第$2$1')
  $z=[regex]::Replace($z,'(?<![0-9A-Za-z第])([0-9]+) *(Div|Division|Bde|Brigade|Bn|Rgt|Regiment|Cav)(?![A-Za-z])','第$1$2')
  $z=[regex]::Replace($z,'(?<![A-Za-z\.\-])(Bde|Brigade|Bn|Rgt|Regiment|Cav|Div|Division)(?![A-Za-z])',{ param($m) $map[$m.Groups[1].Value] })
  $z=$z.Replace('[PORT]','[港口]').Replace('[DAK]','[非洲军]').Replace('@@SSV@@','SS-V')
  return $z
}

$out=@()
for($n=1;$n -le 400;$n++){
  $s=$si[$n-1]
  if($lit.ContainsKey($n)){ $out += ($s + $tab + $lit[$n]); continue }
  $out += ($s + $tab + (ZhLine $s))
}
[System.IO.File]::WriteAllText($dst,($out -join "`r`n")+"`r`n",(New-Object System.Text.UTF8Encoding($false)))
"rows=$($out.Count)"
$mm=0;$det=@()
for($i=0;$i -lt 400;$i++){
  $p=$out[$i].Split($tab)[1]
  foreach($ch in @('/','[',']','(',')')){ if(([regex]::Matches($si[$i],[regex]::Escape($ch))).Count -ne ([regex]::Matches($p,[regex]::Escape($ch))).Count){$mm++;$det+=("L$($i+1):$ch")} }
}
"structure mismatches = $mm  $($det -join ' ')"
