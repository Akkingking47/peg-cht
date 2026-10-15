# OpenGen `.xscn` 部队番号 / 地名 汉化风格指南（子代理必读）

## 任务
把一批**军事部队番号 / 编成名 / 地名**翻译成简体中文。

## 输入 / 输出
- 输入：`D:\DSH\军事游戏汉化\work\xscn\chunks\chunk-NN.tsv`（**单列纯文本**，每行一条原文，UTF-8）
- 输出：`D:\DSH\军事游戏汉化\work\xscn\zh\part-NN.tsv`（目录若不存在请创建）

## 输出格式（严格，违反即返工）
每行一条：`原文<TAB>译文`。**行数与顺序必须与输入完全一致**。
UTF-8 **无 BOM**，行尾与输入一致。**不要**表头、注释、编号、空行、代码块。

## 内容长什么样
```
333 IR / 225 ID / IX AK / AOK 6
Art.-Reg. 156 / 56 ID / IX AK / AOK 6
I. / Flak-Reg. 14 / XI AK / AOK 6
19 Bn Eng  / 1 DChA / VII CA
22 Li / 12 DI / IV CA
23 R/4 USMC/[III]
12e Cuirassiers / 3 DLM / CC / 1e Armée / GA 1
SS Standarte Deutschland IR / SS-Verfügungs-Division (mot.) / XLI AK / AOK 4
```
也会有少量地名/舰名（`USS Cabot`、`Golubka`、`Sanyo Maru`）与纯编号（`5/6`、`777/6`）。

## 编制名对照表（按输入原语言的术语译，不要张冠李戴）

**德语**：`IR` / `Inf.-Reg.`→步兵团，`ID` / `Inf.-Div.`→步兵师，`Pz.Div.`→装甲师，`Pz.`→装甲，
`AK`→军，`AOK`→集团军，`Art.-Reg.`→炮兵团，`Aufkl.-Abt.`→侦察营，`Pion.-Btl.`→工兵营，
`PzJäg.-Abt.` / `Pzjäg.-Abt.`→反坦克营，`Flak-Reg.`→高射炮团，`SS`→党卫军，
`Kradschützen`→摩托化步兵，`Schützen` / `Schtz.`→步兵，`Btl.` / `Abt.`→营，`Rgt.`→团，
`Brig.`→旅，`Div.`→师，`Korps`→军，`Armee`→集团军，`Standarte`→旗队，`Mot.`→摩托化，
`Leicht`→轻装，`Art.Bde.`→炮兵旅，`Gebirgs`→山地，`Fallschirm`→伞兵

**英 / 美**：`R` / `Rgt`→团，`Div`→师，`Bde` / `Br`→旅，`Corps`→军，`Bn` / `Btn` / `B`→营，
`Cav`→骑兵，`Eng`→工兵，`AR`→炮兵团，`FAR`→野炮兵团，`FHAR`→重炮兵团，`Field AR`→野战炮兵团，
`Tk.`→战车，`Inf`→步兵，`Res.`→预备，`Ind.`→独立，`Garrison`→守备部队，`Yeomanry`→义勇骑兵，
`BEF`→英国远征军，`Arm.`→装甲，`AA`→防空，`MG`→机枪，`Squadron`→中队，`Wing`→联队，
`Column`→纵队，`Detachment`→支队，`Rifle`→步枪，`Flotilla`→航空战队，`Air Army`→空军集团军

**法语**：`RI`→步兵团，`DI`→步兵师，`DIM`→摩托化步兵师，`DLM`→轻机械化师，`CA`→军，
`CC`→骑兵军，`Bon` / `Bn`→营，`Sapeurs`→工兵，`Cuirassiers`→胸甲骑兵，`Armée`→集团军，
`RAD`→防空炮兵团，`RDP`→……

**意大利语**：`DI`→步兵师，`CA`→军

**日语**：`Sentai`→战队，`Datai`→大队，`Chutai`→中队，`SNLF`→特别陆战队，`Maru`→丸

**中国**：`R`→团，`Div`→师，`Corps`→军，`War Area`→战区，`Army`→集团军

**机构/国别缩写（有通行中文名的译中文）**：`USMC`→海军陆战队，`RAF`→皇家空军，`KPA`→朝鲜人民军，
`PLA`→解放军，`KMT`→国民党军，`ROK`→韩国，`KNIL`→荷属东印度军，`BEF`→英国远征军

## 硬规则

1. **序号一律用「第 + 阿拉伯数字」**：番号数字转成阿拉伯数字并加「第」，
   **去掉英文序数后缀**（th/st/nd/rd/e），罗马数字也转阿拉伯数字：
   - `333 IR`→`第333步兵团`　`1340th Reg`→`第1340团`　`137th Br`→`第137旅`
   - `12e Cuirassiers`→`第12胸甲骑兵团`　`IX AK`→`第9军`　`AOK 6`→`第6集团军`
   - `22 Li / 12 DI / IV CA`→`第22Li / 第12步兵师 / 第4军`（未知缩写 `Li` 原样保留）
   - ⚠️ **纯编号**（`5/6`、`777/6`、`1462/462`）**不加「第」**，原样保留
   - ⚠️ **方括号内的代号**（`[XV]`、`[5A]`、`[DAK]`、`[III]`）**原样保留**，不加「第」、
     不做罗马转阿拉伯
   - 括号内若是**完整英文词**才译，且同样用「第N」（`[20 Corps]`→`[第20军]`）
2. **结构与分隔符逐字保留**：`/`、`-`、`[ ]`、`( )` 的数量与顺序不变；原文的空格位置（含双空格、
   行尾空格）尽量保留。
3. **括号 `[ ]` 的处理**：
   - 括号内是**完整英文单词/词组** → **译中文，且同样用「第N」**（`[14 Army]`→`[第14集团军]`、`[20 Corps]`→`[第20军]`、
     `[9 War Area]`→`[第9战区]`、`[Peace Preservation Force]`→`[治安部队]`）
   - 括号内是**纯代号/缩写** → **原样保留**（`[XV]`、`[5A]`、`[DAK]`、`[57SC]`、`[III]`、`[8A]`）
   - 括号内是**人名** → 用通行中文译名（`[Cruewell]`→`[克吕维尔]`、`[Rommel]`→`[隆美尔]`）；
     拿不准则保留原文
4. **装备 / 舰船 / 飞机型号保留原文**（`BA-10`、`M4A1`、`Bf-109`、`USS Cabot`、`Sanyo Maru`）。
5. **地名**：有通行中文名的用通行名；否则音译 + 通名后缀
   （River→河，Sea→海，Canal→运河，Airfield→机场，Station→站，Lake→湖，Bay→湾）。
6. **拿不准一律保留原文，不要猜**。未知缩写（`Li`、`BM`、`FR`、`Gn`、`LC`、`SBAP`…）与纯编号
   （`5/6`、`777/6`、`1462/462`、`14/15M`）**译文 = 原文**。
7. 中文内部不加多余空格；原文的空格保留在对应位置。
8. 不使用禁用旧称、蔑称。

## 交付前自检（必须做，并在回复里报告结果）
1. 输出行数 == 输入行数
2. 每行恰好 1 个 TAB，且 TAB 前 == 输入对应行原文
3. 逐行比对 `/`、`[`、`]`、`(`、`)` 数量与输入一致
4. 无 BOM、无空行、无表头

## 只回复一行
`part-NN.tsv 完成，共 N 行；自检通过`（不要贴译文内容）

---

## 补充口径（易歧义项，务必按此）

1. **`Ind.` 是歧义缩写，按语境判断**：
   - 与国名/地名连用（`4 Ind`、`7 Indian Div`、`3 Ind Div`）→ **印度**
   - 与编制连用表示独立（`2 Tk.Bde.(Ind.)`、`Ind. Engineer R.`）→ **独立**
   - 同一场景内若同时出现 `Indp`，则 `Ind.` 优先取「印度」
   - 判断不了就保留 `Ind.` 原文
2. **德语 `Schützen`**：`Schützen-Regiment`→**摩托化步兵团**；`Schützen-Brigade`→**摩托化步兵旅**；
   缩写 `Schtz.`/`Schütz.` 单用→**步兵**（不译「装甲掷弹兵」这种后期叫法）
3. **方括号里的知名部队代号可以译**（有明确通行中文名的）：`[DAK]`→`[非洲军]`、
   `[Kwantung]`→`[关东军]`；**纯编号/字母代号一律保留**：`[XV]`、`[5A]`、`[8A]`、`[III]`、
   `[57SC]`、`[7MD]`、`[SEF]`、`[SC]`
4. **常见专名对照**（意/德/法）：`Littorio`→利托里奥，`Ariete`→公羊，`Centauro`→半人马，
   `Savona`→萨沃纳，`Spezia`→斯佩齐亚，`Napoli`→那不勒斯，`Trieste`→的里雅斯特，
   `Kleist`→克莱斯特（集群），`Krahe`→克拉赫（集群），`KG`→战斗群，`DAK`→非洲军，
   `Groupe d'Armées`→集团军群，`Tercio`→西班牙军团，`Giov.Fasc`→法西斯青年（保留缩写亦可）
5. **拿不准的缩写清单（原样保留，不要猜）**：`BM` `FR` `MR` `RA` `CR` `Gn` `Li` `LC` `MB`
   `RAA` `SG` `WDD` `LD` `GB` `NLF` `SBAP` `SPAT` `RCT` `KNIL` `EDAC` `RD` `BLM` `DLC` `RDP`
   `GRCA` `RACh` `DC` `Pdr` `ATR` `Habforce` `FF` `SA` `SFB` `TFH` `ER` `eR` `Tercio`
6. **苏联编制**：`ShAD`→强击航空兵师，`IAD`→歼击航空兵师，`BAP`/`SBAP`→轰炸航空兵团，
   `Gv`→近卫，`RKKA`→红军；拿不准保留
7. **不确定的整行**（例如法军航空队那种多段混合）→ **整行保留原文**
8. 交付时若遇到上面没覆盖的歧义，**保留原文**并在回复里点名说明（不要自行发明译法）

