# EFILE_Clu `.xscn` 补译口径（本批子代理必读）

## 任务
把 `EFILE_Clu`（WW2 efile，**1945 年奥得河—瓦尔塔河前线**为主，另有芬兰拉普兰等场景）
`.xscn` 尾部串区里尚未译的**地名 / 部队番号 / 短句**译成简体中文。

先读这两份既有口径（本文件是它们的合并与补充）：
- `D:\DSH\军事游戏汉化\work\xscn\POLICY.md` —— **部队番号/编制名**对照表 + 硬规则（编号、方括号、缩写）
- `D:\DSH\军事游戏汉化\work\kaiser\PLACE-POLICY.md` —— **地名音译**要点（德/波/俄/芬兰语）

## 输入 / 输出
- 输入：`D:\DSH\军事游戏汉化\work\xscn\residual-chunks-clu\chunk-NN.tsv`（**单列纯文本**，每行一条原文，UTF-8 无 BOM）
- 输出：`D:\DSH\军事游戏汉化\work\xscn\residual-zh-clu\part-NN.tsv`
  每行 `原文<TAB>译文`；**行数与顺序逐行一致**；UTF-8 **无 BOM**；`\n` 行尾；不要表头/注释/编号/空行。

## 题材背景（帮助你判断专名）
- 主战场：**屈斯特林（Küstrin）要塞与奥得河/瓦尔塔河汇流处**、泽洛高地（Seelow）方向、
  `Festungsfront Oder-Warthe-Bogen`（奥得-瓦尔塔弧形筑垒地域）。
- 德军：第9集团军、`Kurmark` 师、`Brigade Langkeit`、各 `Festungs-Inf.-Bat.`（要塞步兵营）、
  `Volkssturm`（人民冲锋队）、`PzPiBat.`（装甲工兵营）、`PzAufkl.Abt.`（装甲侦察营）、`KmK`（Kampfkommandant 城防司令）。
- 苏军：近卫第8集团军、第33/47/69集团军、第3/5突击集团军、第16空军集团军、
  `Gds`=近卫、`RflD`=步兵师、`Mrt Rgt`=迫击炮团、`Ftr AvD`=歼击航空师、`AT Bn`=反坦克营。

## 硬规则（违反即返工）

1. **地名**：有通行中文名的一律用通行名；其余按**源语言音译**（德语为主，另有波兰/捷克/俄/芬兰语）。
   通名译中文：`See`→湖 · `Fluss`/`River`→河 · `Kanal`→运河 · `Stellung`→阵地 · `Sporn`→山嘴 ·
   `Berge`→山地 · `Forst`/`Wald`→森林 · `Bruch`/`Loose`→沼泽 · `Vorwerk`→庄园 · `Bahnhof`→车站 ·
   `Brücke`→桥 · `Insel`→岛 · `Heide`→荒原 · `Mühle`→磨坊 · `Dorf`→村 · `Stadt`→城 · `Neustadt`→新城。
2. **部队番号**：按 `POLICY.md` 的对照表译；序号一律「第+阿拉伯数字」；`/`、`-`、`[ ]`、`( )`、
   空格数量与顺序**逐字保留**；**括号一律半角**。
   - `III/SchlG 2`→第3/第2攻击机联队 · `Festungs-Inf-Bat. 1450`→第1450要塞步兵营 ·
     `Pi-Ers.-u. Ausb.Bat 68`→第68工兵补充与训练营 · `sArt-Ers.Abt. 39`→第39重型炮兵补充营 ·
     `282 Ftr AvD/16 Air Army`→第282歼击航空师/第16空军集团军
3. **短句**（标题/说明）意译：`Most`（捷克城市 Brüx 的捷克名）→莫斯特 ·
   `Running Fight`→追击战 · `Closing The Corridor`→封闭走廊 · `Force Recon`→武装侦察。
4. **照抄不译**（译文＝原文，逐字符不变）：纯字母代号/编号（`PzW 811` 这类无法判定的缩写可保留，
   但在回复里点名）、人名（有通行译名的除外）、舰名、装备/飞机型号、乱码串。
   ⚠️ **拿不准就照抄**，不要猜、不要发明音译；宁可漏，不可错。
5. **绝不允许**在译文里留拉丁字母（照抄项除外）；不留首尾空格；不使用蔑称旧称。

## 已知通行译名（**务必采用**，避免同地异译）

| 原文 | 译文 | 原文 | 译文 |
|---|---|---|---|
| Oder | 奥得河 | Küstrin | 屈斯特林 |
| Alte Oder | 老奥得河 | Frankfurt an der Oder | 奥得河畔法兰克福 |
| Warthe | 瓦尔塔河 | Berlin | 柏林 |
| Spree | 施普雷河 | Kienitz | 基尼茨 |
| Neisse | 尼斯河 | Göritz / Goeritz | 格利茨 |
| Reitwein | 赖特魏因 | Aurith | 奥里特 |
| Lebus | 莱布斯 | Wulkow | 武尔科 |
| Seelow | 泽洛 | Werder | 韦尔德 |
| Beeskow | 贝斯科 | Beelitz | 贝利茨 |
| Fürstenwalde | 菲尔斯滕瓦尔德 | Wittstock | 维茨托克 |
| Tornio | 托尔尼奥 | Most | 莫斯特 |

## 交付前自检（必须做，并在回复里报告）
1. 输出行数 == 输入行数
2. 每行恰好 1 个 TAB，且 TAB 前与输入对应行**逐字符相同**
3. `/`、`[`、`]`、`(`、`)` 数量与输入逐行一致
4. 译文非空、无首尾空格、无 BOM、无空行、无表头、除照抄项外无拉丁字母

## 回复格式（只两行）
`part-NN 完成，共 M 行；自检通过`
`照抄保留 N 条：<逗号分隔的原文列表>`
