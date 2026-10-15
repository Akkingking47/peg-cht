# Open LGWW2 补译完成报告 (SEG6 / SEG8 / SEG9)

- 输出目录：D:\DSH\军事游戏汉化\work\olgww2\scenario\
- 输出命名：<原文件名>.utf8.txt
- 编码：UTF-8 无 BOM；行尾与源文件一致（CRLF / LF 各自保持），行数逐行一一对应
- 日期：无空格中文格式（如 1942年11月9日）
- 校验：110/110 存在；BOM/行尾/尾换行/行数/空行 全部与源文件一致；无残留英文句子

## 不确定项（已按最合理方案处理，供复核）

1. n42s15a：`L1` / `L` / `BD` / `SA` / `K/K` 为源码标记，无法判定含义，保留原文未译。
2. sp3、sp4：`[Cairo]` `[8A Remnants]` `[Suez]` `[DAK]` `[2 Luftflotte]` 等中括号标记按部队/地点解读翻译（保留中括号形态）；`[DAK]` 保留代号。
3. sp2：波兰部队 `B` / `A` / `D`（连级代号）保留原文。
4. sp0：`1D` `1H` `3KOMR` `1KOMR` `2KOMR` `2D` `2RWK` `8M` `2R` `4B` `L4` `IA` `SM/RM` 等意大利编制缩写保留原文；`Aquila` 译「鹰号」（未建成航母）。
5. n42s05：`1/1 P` `3/1 P` `4/1 P` `Aty 1P` `AT 1P` 中 `P` 无上下文，按「第1师」处理；`Livorno` 无编号，译「利沃诺师」。
6. n42s04：`AA/2 Tridentina`、`5/2 Tridentina` 等按「3月2日师」（Tridentina）处理；`5th Div. AD` 按「第5师防空部队」；`231st if Brig.` 按「第231步兵旅」（源码 if=inf 之误）。
7. n42s06：`H. u Deutschmeister` 译「维也纳本土防卫团」（第9步兵师 Hoch- und Deutschmeister 传统称谓）。
8. n42s10a/sp1/tu04/tu06：`L` / `L1`（德语 Lehr 教导部队）按「教导部队」或保留原文处理。
9. sp4：`StuIG K/90 LD` 中 `StuIG K` 为装备型号，保留原文。

## 需上级决定的既有不一致

`dak2int/dak3int/dak4int/dak5int/dak6int/dak7int/dak8int/dakint`、`rsusa01int`、`rsusa02int`、`rswes01int`~`rswes05int` 共 15 个**先前已完成**的文件使用带空格日期（如「1941 年 5 月 14 日」），与本次要求及工程内其余绝大多数文件（如「1940年5月10日」）不一致。本次未改动这些文件，建议由上级统一归一化。

## 术语表（本批统一）

- 编制：师/旅/团/营/连；德军 Pz=装甲师、PzR=装甲团、Pzg=装甲掷弹兵团、Schzt=装甲步兵团、Rec/Aufkl=侦察营、Pio=工兵营、Pzjgr=反坦克营、AR=炮兵团、Krad=摩托车营、Mot=摩托化团、Leicht=轻装师、zbV=特种营；`[DAK]`=德意志非洲军
- 意军：Ariete=阿里埃特师、Littorio=利托里奥师、Trieste=的里雅斯特师、Trento=特伦托师、Folgore=福尔戈雷师、Pavia=帕维亚师、Brescia=布雷西亚师、Bologna=博洛尼亚师、Sabratha=萨布拉塔师、Spezia=斯佩齐亚师、Pistoia=皮斯托亚师、Giov.Fasc=青年法西斯师、Superga=苏佩尔加师、Imperiali=帝国师、Centauro=半人马座师、Cuneense=库内奥师；狙击兵=R 中的 Bersaglieri 传统译法（沿用既有译法）
- 英美：`[8 Army]`=[第8集团军]、`Remnants`=残部、Recce=侦察部队、RTR=皇家坦克团、Hussars=骠骑兵团、KRR=国王皇家步枪团、Commando=突击队、TF=战斗群、USAAF=美国陆军航空队、DAF=沙漠航空队
- 德国空军：`[2 Luftflotte]`=[第2航空队]、Luft/Luftwaffe=德国空军；意大利 Reggia=意大利皇家空军
- 舰名：HMS=皇家海军、RM=意海军、USS=美舰；`Duke of York`=约克公爵号、`Warspite`=厌战号、`Illustrious`=光辉号、`Aquila`=鹰号
- 地形标记：FORTIFICATION=[工事]、ROUGH=[崎岖地]、SWAMP=[沼泽]、PORT=[港口]、RIVER=[河流]、CLEAR=[开阔地]、OCEAN=[海洋]
- 立场用词：按所属方视角使用编制名（德军文件用德军编制名，英美方用英美编制名）；无蔑称/旧称

## SEG6  已完成 12 / 12 个

- n42s04.txt.utf8.txt
- n42s05.txt.utf8.txt
- n42s06.txt.utf8.txt
- n42s07.txt.utf8.txt
- n42s08a.txt.utf8.txt
- n42s09.txt.utf8.txt
- n42s10a.txt.utf8.txt
- n42s11a.txt.utf8.txt
- n42s12a.txt.utf8.txt
- n42s13a.txt.utf8.txt
- n42s14.txt.utf8.txt
- n42s15a.txt.utf8.txt

## SEG8  已完成 86 / 86 个

- sp0.txt.utf8.txt
- sp0bv.txt.utf8.txt
- sp0int.txt.utf8.txt
- sp0l.txt.utf8.txt
- sp1.txt.utf8.txt
- sp1int.txt.utf8.txt
- sp1v.txt.utf8.txt
- sp2.txt.utf8.txt
- sp2int.txt.utf8.txt
- sp2v.txt.utf8.txt
- sp3.txt.utf8.txt
- sp3int.txt.utf8.txt
- sp3v.txt.utf8.txt
- sp4.txt.utf8.txt
- sp4int.txt.utf8.txt
- sp4v.txt.utf8.txt
- spchoice.txt.utf8.txt
- spchoicebv.txt.utf8.txt
- spchoiceint.txt.utf8.txt
- spchoicel.txt.utf8.txt
- spchoicev.txt.utf8.txt
- spe01.txt.utf8.txt
- spe01bv.txt.utf8.txt
- spe01int.txt.utf8.txt
- spe01l.txt.utf8.txt
- spe02.txt.utf8.txt
- spe02bv.txt.utf8.txt
- spe02int.txt.utf8.txt
- spe02l.txt.utf8.txt
- spe03.txt.utf8.txt
- spe03bv.txt.utf8.txt
- spe03int.txt.utf8.txt
- spe03l.txt.utf8.txt
- spe04.txt.utf8.txt
- spe04bv.txt.utf8.txt
- spe04int.txt.utf8.txt
- spe04l.txt.utf8.txt
- spe05.txt.utf8.txt
- spe05int.txt.utf8.txt
- spe05v.txt.utf8.txt
- sps01.txt.utf8.txt
- sps01bv.txt.utf8.txt
- sps01int.txt.utf8.txt
- sps01l.txt.utf8.txt
- sps02.txt.utf8.txt
- sps02bv.txt.utf8.txt
- sps02int.txt.utf8.txt
- sps02l.txt.utf8.txt
- sps03.txt.utf8.txt
- sps03bv.txt.utf8.txt
- sps03int.txt.utf8.txt
- sps03l.txt.utf8.txt
- sps04.txt.utf8.txt
- sps04bv.txt.utf8.txt
- sps04int.txt.utf8.txt
- sps04l.txt.utf8.txt
- sptu01.txt.utf8.txt
- sptu01bv.txt.utf8.txt
- sptu01int.txt.utf8.txt
- sptu01l.txt.utf8.txt
- sptu02.txt.utf8.txt
- sptu02bv.txt.utf8.txt
- sptu02int.txt.utf8.txt
- sptu02l.txt.utf8.txt
- sptu03.txt.utf8.txt
- sptu03bv.txt.utf8.txt
- sptu03int.txt.utf8.txt
- sptu03l.txt.utf8.txt
- sptu04.txt.utf8.txt
- sptu04bv.txt.utf8.txt
- sptu04int.txt.utf8.txt
- sptu04l.txt.utf8.txt
- tu01.txt.utf8.txt
- tu01bv.txt.utf8.txt
- tu01int.txt.utf8.txt
- tu01l.txt.utf8.txt
- tu02.txt.utf8.txt
- tu02bv.txt.utf8.txt
- tu02int.txt.utf8.txt
- tu02l.txt.utf8.txt
- tu02v.txt.utf8.txt
- tu03.txt.utf8.txt
- tu03bv.txt.utf8.txt
- tu03int.txt.utf8.txt
- tu03l.txt.utf8.txt
- tu03v.txt.utf8.txt

## SEG9  已完成 12 / 12 个

- tu04.txt.utf8.txt
- tu04bv.txt.utf8.txt
- tu04int.txt.utf8.txt
- tu04l.txt.utf8.txt
- tu05.txt.utf8.txt
- tu05bv.txt.utf8.txt
- tu05int.txt.utf8.txt
- tu05l.txt.utf8.txt
- tu06.txt.utf8.txt
- tu06bv.txt.utf8.txt
- tu06int.txt.utf8.txt
- tu06l.txt.utf8.txt

