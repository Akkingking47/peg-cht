$ErrorActionPreference='Stop'
$cp=[Text.Encoding]::GetEncoding(1252)
$src='D:\OpenPG2\EFILE_OLGWW2\names.txt'
$lines=($cp.GetString([IO.File]::ReadAllBytes($src))) -split "\r?\n"
$wr='D:\DSH\军事游戏汉化\work\olgww2'

# key helper: source file stores UTF-8 bytes; reading as CP1252 yields mojibake
function K([string]$nm){ $cp.GetString([Text.Encoding]::UTF8.GetBytes($nm)) }

$dict=@{}
# 1) reuse prior translations (first occurrence wins)
foreach($f in @('names-map-1.tsv','names-map-2.tsv')){
  foreach($l in (Get-Content "$wr\$f" -Encoding UTF8)){
    if($l -match '^(\d+)\|(.+)$'){
      $n=[int]$Matches[1]; $zh=$Matches[2]; $s=$lines[$n-1]
      if(-not $dict.ContainsKey($s)){ $dict[$s]=$zh }
    }
  }
}

# 2) new translations (true Unicode source name -> Chinese)
$new=@(
 @('Soares','索亚雷斯'),@('Castro','卡斯特罗'),@('Pinto','平托'),@('López','洛佩斯'),
 @('Vidal','比达尔'),@('Preciado','普雷西亚多'),@('Muñoz','穆尼奥斯'),@('Núñez','努涅斯'),
 @('Pérez','佩雷斯'),@('Sacristán','萨克里斯坦'),@('Berasategui','贝拉萨特吉'),@('Vallina','巴利纳'),
 @('Yáñez','亚涅斯'),@('Caicoya','凯科亚'),@('Argüelles','阿圭列斯'),@('Berciano','贝尔西亚诺'),
 @('Bermúdez','贝尔穆德斯'),@('Velasco','贝拉斯科'),@('Rodríguez','罗德里格斯'),@('Prado','普拉多'),
 @('Sabín','萨宾'),
 @('Jones','琼斯'),
 @('Budi','布迪'),@('Chahaya','查哈亚'),@('Dian','迪安'),@('Guntur','贡图尔'),@('Kersen','克尔森'),
 @('Pramana','普拉马纳'),@('Ramelan','拉梅兰'),@('Santoso','桑托索'),@('Setiawan','塞蒂亚万'),
 @('Anil','阿尼尔'),@('Kamala','卡玛拉'),@('Narayan','纳拉扬'),@('Sonam','索南'),
 @('Jensen','延森'),@('Hansen','汉森'),@('Pedersen','佩德森'),@('Andersen','安德森'),
 @('Christensen','克里斯滕森'),@('Larsen','拉森'),@('Sorensen','索伦森'),@('Rasmussen','拉斯穆森'),
 @('Jorgensen','约根森'),@('Petersen','彼得森'),@('Madsen','马德森'),@('Kristensen','克里斯滕森'),
 @('Olsen','奥尔森'),@('Thomsen','汤姆森'),@('Christiansen','克里斯蒂安森'),@('Poulsen','波尔森'),
 @('Johansen','约翰森'),@('Knudsen','克努森'),@('Mortensen','莫滕森'),@('Moller','默勒'),
 @('Jakobsen','雅各布森'),@('Jacobsen','雅各布森'),@('Olesen','奥勒森'),@('Mikkelsen','米克尔森'),
 @('Frederiksen','弗雷德里克森'),@('Laursen','劳尔森'),@('Henriksen','亨里克森'),@('Lund','伦德'),
 @('Schmidt','施密特'),@('Eriksen','埃里克森'),
 @('Steiner','施泰纳'),@('Krueger','克鲁格'),@('Müller','米勒'),@('Strasser','施特拉瑟'),
 @('Stresseman','施特雷泽曼'),@('Kronfuss','克龙富斯'),@('Küntz','金茨'),@('Heinrich','海因里希'),
 @('Köhler','克勒'),@('Festung','费斯通'),@('Kohl','科尔'),@('Polster','波尔斯特'),@('Cerni','切尔尼'),
 @('Klos','克洛斯'),@('Plattner','普拉特纳'),@('Herzog','赫尔佐格'),@('Bauer','鲍尔'),@('Brunn','布伦'),
 @('Buchleitner','布赫莱特纳'),@('Dorfmeister','多夫迈斯特'),@('Dreher','德雷尔'),@('Eckhel','埃克尔'),
 @('Dorner','德尔纳'),@('Eigner','艾格纳'),@('Friedjung','弗里德容'),@('Gandler','甘德勒'),@('Happ','哈普'),
 @('Zweig','茨威格'),@('Zeiler','蔡勒'),@('Windischgraetz','温迪施格雷茨'),@('Werberg','韦尔贝格'),
 @('Da Souza','达索萨'),@('Alves','阿尔维斯'),@('Dos Santos','多斯桑托斯'),@('Gomes','戈麦斯'),
 @('Oliveira','奥利维拉'),@('Parreira','帕雷拉'),@('Souza','索萨'),@('Pereira','佩雷拉'),
 @('Do Nascimento','多纳西门托'),@('Farias','法里亚斯'),
 @('Sükür','苏库尔'),@('Terim','特里姆'),@('Abdullah','阿卜杜拉'),@('Abas','阿巴斯'),
 @('Baykurt','拜库尔特'),@('Çelebi','切莱比'),@('Behramoglu','贝赫拉莫卢'),@('Birdal','比尔达尔'),
 @('Ertegum','埃尔泰古姆'),@('Hoca','霍贾'),@('Kuneralp','库内拉尔普'),@('Inönü','伊诺努'),
 @('Ipekçi','伊佩克奇'),@('Kemal','凯末尔'),@('Küçük','屈奇克'),@('Sahin','沙欣'),@('Bastürk','巴斯图尔克'),
 @('Ökte','厄克特'),@('Pamuk','帕慕克'),@('Sevim','塞维姆'),@('Zorlum','佐尔卢姆'),@('Nihat','尼哈特'),
 @('Tural','图拉尔'),
 @('Collins','柯林斯'),@('Mulcahy','马尔卡希'),@('Daly','戴利'),@('Ennis','恩尼斯'),@('Deasy','迪西'),
 @('Aiken','艾肯'),@('Bairéad','巴雷亚德'),@('Barrett','巴雷特'),@('Behan','贝汉'),@('Brugha','布鲁加'),
 @("O'Malley",'奥马利'),@('Doyle','多伊尔'),@('Duggan','杜根'),@('Hogan','霍根'),@('Kearney','卡尼'),
 @('MacBride','麦克布莱德'),@('Maguire','马圭尔'),@('MacEoin','麦克约恩'),@("O'Connor",'奥康纳'),
 @('Quinn','奎因'),@('Russell','拉塞尔'),@("O'Sullivan",'奥沙利文'),@('Ryan','瑞安'),
 @('Ó Fathaigh','奥法希'),@('Whelan','惠兰'),@('Coughlin','库格林'),@('Twomey','图米'),
 @("O'Donovan",'奥多诺万'),@('Murphy','墨菲'),@('MacSwiney','麦克斯威尼'),
 @('Aristideas','阿里斯蒂德斯'),@('Manolas','马诺拉斯'),@('Minou','米努')
)
foreach($p in $new){
  $k=K $p[0]
  if(-not $dict.ContainsKey($k)){ $dict[$k]=$p[1] }
}

$out=New-Object System.Collections.Generic.List[string]
$missing=New-Object System.Collections.Generic.List[string]
for($i=1520;$i -le 2263;$i++){
  $s=$lines[$i-1]
  if($s.Trim() -eq 'Leader'){ $out.Add("$i|领袖"); continue }
  if($dict.ContainsKey($s)){ $out.Add("$i|$($dict[$s])") }
  else { $missing.Add("$i|$s") }
}
if($missing.Count -gt 0){ Write-Output "MISSING:"; $missing | ForEach-Object { Write-Output $_ }; exit 1 }
$enc=New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText("$wr\names-map-3.tsv",(($out -join "`n")+"`n"),$enc)
Write-Output "wrote $($out.Count) entries"
$srcs=@(); for($i=1520;$i -le 2263;$i++){ if($lines[$i-1].Trim() -ne 'Leader'){ $srcs+=$lines[$i-1] } }
Write-Output "non-Leader lines: $($srcs.Count); unique: $(($srcs | Select-Object -Unique).Count)"
