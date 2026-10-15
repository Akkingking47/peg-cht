# KAISER `.xscn` 编制番号层口径（子代理必读）

本轮做 `EFILE_KAISER`（一战多国，1850–1926）`.xscn` 里**组 1 的部队编制标签**。
格式形如 `本级/上级/再上级/[所属军]`，各级是「数字或罗马数字 + 兵种/编制缩写」。

输入每行**一个原文串**（`work\kaiser\_unit_todo_partNN.txt`），输出**逐行一一对应的中文**。

---

## 一、总则

- **`/` 与 `[ ]` 的数量、顺序原样保留**；罗马数字转阿拉伯「第N」；标点用**半角**。
- 只译「编制等级/兵种/国别词 + 人名 + 地名」；**型号/舰名/纯编号照抄**。
- 层级串译法：`营/团/旅或师/[军]`，逐级译。

## 二、缩写对照（按语种，只列常见的）

**德语（最多）**
`Div.`→师 · `Res.Div`/`RDiv`→预备师 · `ID`→步兵师 · `bay.`→巴伐利亚 · `Geb.`→山地 ·
`Jäg`/`Jgr`/`JägR`→猎兵 · `BJägR`/`BLeibR`→巴伐利亚猎兵团/近卫团 · `Alp.K.`→阿尔卑斯军 ·
`Mar.Inf.`→海军步兵 · `Mar.Div.Flandern`→佛兰德海军师 · `MIR`→海军步兵团 ·
`Matr.Art.`→海军炮兵 · `FAR`→野战炮兵团 · `RFAR`/`RFeldA`→预备野战炮兵团 · `PiK`/`Pio`→工兵 ·
`Radfahr`→自行车 · `Kav`→骑兵 · `Ldw`→后备军 · `Ldw-Esk`→后备骑兵连 · `Esk`→中队 ·
`Landsturm`→后备军 · `Res.`→预备役 · `Ers.`→补充 · `FeldA`→野战炮兵 · `Fld.`→野战 ·
`KBrig`→骑兵旅 · `HKK`→骑兵军 · `SchK`→快速炮艇(海军) · `SchlaSta`/`Schusta`→护航中队 ·
`Jasta`→战斗机中队 · `JGr.`→战斗机大队 · `Flug`→航空 · `Luftschiffer`→飞艇 · `Luftfahrtruppe`→航空部队 ·
`Abt.`→支队 · `StSchBaon`→山地突击营 · `Geb.Bat.`→山地营 · `GbBrig`/`GbAbt`→山地旅/营 ·
`I.`→第1 · `bay.ID`→巴伐利亚步兵师 · `GB`→山地 · `Cie`→连 · `Kp`/`Komp`→连。

**法语**
`RI`→步兵团 · `RAC`→野战炮兵团 · `RA`→炮兵团 · `RFM`→摩洛哥步兵团 · `RTSM`→塞内加尔轻步兵团 ·
`ChCh`→猎骑兵 · `Chass.d'Afr`→非洲猎骑兵 · `BrDrag`→龙骑兵旅 · `BrCuir`→胸甲骑兵旅 ·
`BrLegere`→轻骑兵旅 · `DC`→骑兵师 · `DI`→步兵师 · `DIT`→领土步兵师 · `DIAfr`→非洲步兵师 ·
`Goum`→古姆(摩洛哥民兵) · `Brig.Ers.B.`→补充旅 · `Gen.Gouv.Belgien`→比利时总督辖区 · `Meiser`→梅泽尔 · `1ere`→第1。

**英语/英联邦**
`Ches`/`Cheshires`→柴郡团 · `Lancs`/`Lancashire`→兰开夏团 · `Worc`/`Worcesters`→伍斯特团 ·
`Surreys`→萨里团 · `Hamps`/`Hampshire`→汉普郡团 · `Sussex`→苏塞克斯团 · `Buffs`→布夫斯团 ·
`Bedfs`→贝德福德团 · `Norf`→诺福克团 · `Leic`→莱斯特团 · `Midx`→米德尔塞克斯团 ·
`Glos`→格洛斯特团 · `Hert`→赫特福德团 · `Camb`→剑桥郡团 · `Cheshires`→柴郡团 ·
`R.IrishRifles`/`R.IrishRifl.`→爱尔兰来复枪团 · `R.Innisk.Fus.`/`InniskillingFus.`→因尼斯基林燧发枪团 ·
`R.DublinFus.`→都柏林燧发枪团 · `R.MunsterFus.`→芒斯特燧发枪团 · `R.IrishFus.`→爱尔兰燧发枪团 ·
`ConnaughtRangers`→康诺特游骑兵团 · `Leinster`→伦斯特团 · `DragoonGuards`→龙骑兵卫队 ·
`Cyclist`→自行车兵 · `Lnd`/`London`→伦敦 · `HousholdCavComp`→王室骑兵连 · `NavalSq`→海军中队 ·
`RNAS`→皇家海军航空队 · `RND`→皇家海军师 · `RMLI`→皇家海军轻步兵 · `ANZAC`→澳新军团 ·
`LoyalN.Lancs`→忠兰开夏团 · `S.Lancashire`→南兰开夏团 · `S.WalesBord.`→南威尔士边境团 ·
`K.O.S.B.`→国王直属苏格兰边境团 · `Hampshire`→汉普郡团 · `King'sOwn`→国王直属团。

**俄语（音译/意译）**
`Kaz.`→哥萨克 · `Sib.`→西伯利亚 · `Zabaikal`→外贝加尔 · `Khopersky`→霍佩尔 ·
`Kizliaro-Grebensky`→基兹利亚尔-格列边 · `Ekaterinodarsky`→叶卡捷琳诺达尔 · `Nizhegorodsky`→下诺夫哥罗德 ·
`Novoarchangel`→新阿尔汉格尔斯克 · `Novomirgorod`→新米尔哥罗德 · `Vitebskaya`→维捷布斯克 ·
`Volzhsky`→伏尔加 · `Pskovsky`→普斯科夫 · `Chudsky`→楚德 · `Vyatsky`→维亚特卡 · `Danilovsky`→丹尼洛夫 ·
`Denikinsky`→邓尼金 · `Smolenski`→斯摩棱斯克 · `Mosk.Zh-D`→莫斯科铁路 · `AG`→集团军 · `D`→师 · `Brig`→旅 ·
`Udar`→突击 · `Kursanty`→学员 · `Bashkirsky`→巴什基尔 · `Balt`→波罗的海 · `LatBrig`→拉脱维亚旅 ·
`Erhardt`→埃尔哈特 · `Lndwr`→民兵 · `Pohjan Poikain`→波赫扬·波伊卡因（芬兰志愿营，可保留）.

**意/西/土/塞/其他**
`Ferrara`→费拉拉 · `Camerana`→卡梅拉纳 · `Raynaldi`→拉伊纳尔迪 · `Giardina`→贾尔迪纳 ·
`Montuori`→蒙图奥里 · `Carpeneto`→卡尔佩内托 · `De Chaurand`→德肖朗 · `d'Amade`→达马德 ·
`De Mitry`→德米特里 · `Conneau`→科诺 · `Mangin`→芒然 · `Halil-Bei`→哈利勒贝伊 ·
`Tum.`→师(土耳其) · `Hucum Tb`→突击营 · `Beog. okrug`→贝尔格莱德军区 · `Dunavska D.`→多瑙师 ·
`Drinska D.`→德里纳师 · `pos.Bt.`→炮兵连 · `KPP`→骑兵团 · `Bran. Odr.`→边防支队 ·
`Marosvásárhely`→毛罗什瓦沙尔海伊 · `Libavsky`→利巴夫 · `Bande di`→班德(利比亚民兵) ·
`Meharisti`→骆驼骑兵 · `Liege`→列日 · `Antwerpen`→安特卫普 · `[Ypres]`→[伊普尔] · `[Vimy]`→[维米] ·
`[Ypern]`→[伊普尔] · `[Elverdinghe]`→[埃尔弗丁厄] · `[Mangin]`→[芒然] · `[d'Amade]`→[达马德]。

## 三、照抄不译

- **舰名/舰级**：`SMS Csepel` `Yavuz Sultan Selim` `Georgios Averof` `Agamemnon` `Fuso` `Naniwa`
  `Pelayo` `Castilla` `Reina Cristina` `Carlos V` `Benedetto Brin` `Cesare Rossarol` `Faraday` `Mosquito` …
  （⚠️ 含 `é á ö ñ ü` 等变音符者**折写 ASCII**，如 `蒫lair`→`Eclair`）
- **纯编号**：`BP #5` `Elms 3LA`（Elms 若确为地名可译，否则保留）`2 LA` `4B` `[IV]` `[III]`。
- **型号**：`Short 184` `E-15` `SM U-14`。
- **德语带变音符已损的原文**照抄（`W黵tt.Geb.Bat.`＝`Württ.Geb.Bat.`→符腾堡山地营）。

## 四、示例

| 原文 | 译 |
|---|---|
| `I/261R/79R [Vimy]` | `第1营/第261团/第79师 [维米]` |
| `III/1MIR/Mar.Inf./Mar.Div.Flandern [IIIR]` | `第3营/第1海军步兵团/海军步兵/佛兰德海军师 [第3预备军]` |
| `Jasta 3` | `第3战斗机中队` |
| `33 fus/2` | `第33燧发枪团/2` |
| `8 jgr/195` | `第8猎兵营/195` |
| `10 gren/11` | `第10掷弹兵团/11` |
| `2Cyclist/-/- [IIANZAC]` | `第2自行车营/-/- [澳新第2军团]` |
| `I/1MIR/Mar.Inf./Mar.Div.Flandern [IIIR]` | `第1营/第1海军步兵团/海军步兵/佛兰德海军师 [第3预备军]` |
| `47/Ferrara/3` | `47/费拉拉/3` |
| `#3 "Tsentrobron'"` | `第3号装甲列车「中央」` |
| `#2 "Pobeda ili Smert'"` | `第2号装甲列车「胜利或死亡」` |
| `GbH von Marno /-/ [AG Yildirim]` | `冯·马尔诺集团军司令部 /-/ [耶尔德勒姆集团军]` |
| `13Cheshires/74/25 [IIANZAC]` | `第13柴郡团/第74旅/第25师 [澳新第2军团]` |

## 五、格式与回报

- UTF-8 **无 BOM**；行间 `\n`；**每行一条，逐行对应**；无序号/原文/表头/空行/代码块。
- 输出行数必须 == 输入行数；GBK 可编码（不得含 `é á ö ñ ü ş ı â ³`）。
- 完成后**只回复一行**：`unit-NN 完成，共 M 行；自检通过`。
