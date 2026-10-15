# 小片翻译任务口径模板（场景层 · 部队名/单位名 = u 批）

> **用法**：委派时把本文件路径给对方，并告知「本片输入/产出文件名」。对方按本文件执行即可。
> 修订：2026-10-11 v1（含 m 批 5 片实战沉淀的跨片一致性规则）

## 你的角色
你在做一个**个人研究用途**的二战老游戏汉化项目（*People's General* 的二战 MOD「PeG-WW2」）。
工作区 `D:\DSH\军事游戏汉化`。全程只做语言转换，**不改原文的世界观、阵营划分与叙事措辞**。

⚠️ 这是**小批任务**（≤600 行）。请**一次性读完、一次性写完**，**不要**做多余的探索性浏览（宿主要省资源）。
**不要新建任何脚本文件**，直接用读写工具完成。
⚠️ **不要用「分段暂存再拼接」的写法** —— 实测有子代理这样做时丢了 1 行（后经重建才恢复）。
   请**一次性整写**产出文件；写完**逐行核对行数**与第一列。

## 任务
把指定的输入片（形如 `pegww2\research\_scn-todo-u-rN-MM.tsv`）里的**部队名 / 单位名**逐条译成简体中文，
产出 `pegww2\research\_scn-fill-u-rN-MM.tsv`。

### 输入格式（TSV；前 2 行注释 + 1 行表头，其后为数据）
```
原文	译文	类	出现文件数	出现次数
1st Showa Inf		 u 部队名	8	9
captured T-34/76A		 u 部队名	6	6
Equipment		 u 部队名	31	31
```

### 产出格式（**只有两列**，行序与输入**完全一致**，UTF-8 无 BOM，TAB 分隔）
```
原文	译文
1st Showa Inf	昭和步兵第1联队
captured T-34/76A	缴获 T-34/76A
```
- 第一列**逐字照抄**输入「原文」列（**含任何 `\t`/`\xNN` 反斜杠转义序列，一个字符都不能改**）
- **译文内绝不能含 TAB 或换行**；**译文列零空值**

## 译法口径

### ① 部队命名体例（沿用本工作区前作已定稿口径）
```
[称号/地区] [兵种] 第N [团|营]
11th Gangzhou Arty   ⇒ 广州军区炮兵第11团
31st Dragon Hrd Tank ⇒ 龙式重型坦克第31团
Engineer 9th Mao Inf ⇒ 毛式工兵第9营
```
- 本作**作战单位＝团级**；**防空 / 工兵 / 侦察 / 直升机＝营级**
- **日军**部队：团⇒**联队**、营⇒**大队**、侦察/直升机⇒**队**（`1st Showa Inf`⇒`昭和步兵第1联队`）
- **英军** `regiment` 仍作「团」
- 称号统一用「**X式**」（`Dragon`⇒龙式、`Mao`⇒毛式）——**不要**写「X字」

### ② 兵种/编制词对照（必须统一）
`Inf`/`Infantry`⇒步兵 · `Arty`⇒炮兵 · `Tank`/`Pz`⇒装甲 · `Hrd Tank`⇒重型坦克 · `Mot.`⇒摩托化 ·
`Recon`⇒侦察 · `Engineer`⇒工兵 · `AD`/`AA`⇒防空 · `Cav`⇒骑兵 · `Para`/`Airborne`⇒空降/伞兵 ·
`Marine`⇒海军陆战队 · `MG`⇒机枪 · `AT`/`Antitank`⇒反坦克 · `Bde`⇒旅 · `Div`⇒师 · `Corps`⇒军 ·
`Rgt`/`Regiment`⇒团 · `Bn`/`Battalion`⇒营 · `Sqn`⇒中队 · `HQ`⇒司令部/旅部（按层级） · `Korps`⇒军

### ③ 舰名前缀一律保留，舰名译出
`USS Enterprise`⇒`USS 企业号` · `HMS Ark Royal`⇒`HMS 皇家方舟号` · `JN Kirishima`⇒`JN 雾岛号` ·
`RN Kirov`⇒`RN 基洛夫号`（`DDG Luda`/`FFG Krivak` 等**舰级名**维持「前缀+级名」不加「号」）

### ④ 型号 / 番号原样保留
`T-34/76A`、`M4A1`、`SdKfz 251`、`Pz IV`、`B-17`、`Ju-87`、`Me-109`、`SS`、`I/`、`II/`、`A/I/`、`1RTR/22/7`；
`captured`⇒**缴获**（`captured T-34/76A`⇒`缴获 T-34/76A`）；`LL `⇒**租借**

### ⑤ 元数据行 ⇒ **原样保留（译文＝原文）**
整行是 `dummy`/`Dummy` · 以 `Version`/`Gameset`/`Equipment`/`Note`/`Source`/`BTW` 开头的**文件头行** ·
纯符号行 · **无实义词的纯代码**（`KC`、`RSG`、`RF`、`[XX]`、`SM/RM`、`BoB04.scn`、`CreationTime = …`）。
⚠️ **例外**：串里含**真实专名**的（`Washington'46`⇒`华盛顿'46`、`New York '46`⇒`纽约 '46`）**必须译名**，不得整串保留。

### ⑥ 外语普通名词 / 通名 ⇒ 意译；人名地名专名 ⇒ 音译
`Airport`/`Aerodrome`/`Flughafen`/`Lufthavn`⇒机场 · `harbour`⇒港 · `River`⇒河 · `Canal`⇒运河 ·
`Forest`/`Wald`/`Forst`⇒森林 · `Woods`⇒林地 · `Farm`⇒农场 · `Fisheries`⇒渔场 · `Depot`⇒仓库 ·
`Causeway`⇒堤道 · `Refuge`⇒保护区 · `Pocket`⇒包围圈 · `Phase`⇒阶段 · `Invasion`⇒登陆
⚠️ 判据：该词在外语里是**普通名词**（词典有实义）⇒ 意译；是**人名/地名**（专有）⇒ 音译。
⚠️ 若原文是**自造复合名**：**通名后缀意译 + 词干音译**（`Siegerdorf`⇒胜利村、`Herstellungberg`⇒赫尔施泰隆山）。
报告里请列出你据此意译的条目。

### ⑦ 括注与标记
- `_u` 部队名**一律不加** `(原文)` 括号
- 括号/方括号里的**显示标记要译**：`(PORT)`⇒（港口）、`(impassible)`⇒（不可通行）、`(Part 1)`⇒（第1部分）
- **编号类标记原样**：`(#1)`、`(RTB#15)`、`(NN,NN)` 坐标、`[XX]`、`[XXXVIII]`
- ⚠️ 译文里**全角括号前不留空格**：写 `（港口）`，不要 ` （港口）`

### ⑧ 引号体例统一 `「」`；`: Redux`⇒`：重制版`（全角冒号不留空格）

### ⑨ 禁用
`國力`/`佔領`/`光榮勝利`/`前進觀測官`/`改良裝備` 及其简体形式；`声望`（Prestige 统一作「威望」）；一律简体中文。

### ⑩ MOD 原文拼写变体一律按原文音译，不擅自回改史实拼法
⚠️ 例外：若两种拼写差异**仅限变音符号或明显拼写噪声**且指同一实体 ⇒ 可用同一中文名（报告里注明）。
例：`Nizhnyaya Veduga`/`Nizhyaya Veduga`/`Nizn'aja Veduga` ⇒ 均作「下韦杜加」。

## 可参考（**只看你需要的，别大范围浏览**）
- `D:\DSH\军事游戏汉化\peg\research\部队编制译法口径.md` ⭐ 部队命名体例
- `D:\DSH\军事游戏汉化\peg\research\_对照-单位名.tsv`（前作 155 条单位名定稿译例）
- `D:\DSH\军事游戏汉化\pegww2\research\各国军语风格口径.md`（口径总纲）
- `D:\DSH\军事游戏汉化\glossary\standard-glossary.tsv`（译名总库）

## 附录 · 全项目统一口径（u 批已实测沉淀 ⇒ **后续片必须沿用**）

### 编制 / 兵种缩写
军团 `[XXXVIII]`⇒第XXXVIII军 · 师属单位 `N R/M ID`⇒第N团/第M步兵师 ·
`eB`⇒工兵营 · `atB`⇒反坦克营 · `aaB`⇒防空营 · `rB`⇒侦察营 · `aR`⇒炮兵团 · `atR`⇒反坦克团 · `aaR`⇒防空团 ·
`Pion.`/`Pio.Abt.`⇒工兵营 · `PzG(D)`⇒装甲掷弹兵师 · `PzD`⇒装甲师 · `Prcht D`⇒伞兵师 · `MtnD`⇒山地师 · `AirD`⇒空降师 ·
`ErPrGr`⇒试验大队 · `Gruppe`/`KGr`/`KG`⇒战斗群 · `Fighter`⇒战斗机大队 · `Bomber`⇒轰炸机大队 · `Wing`⇒联队 · `Group`⇒大队 ·
`Commando`⇒突击队 · `Coastal Defense`⇒海岸防御师 · `Home Guard`⇒本土防卫队 · `Partisanos`⇒游击队 ·
`Force`/`Task Force`⇒特遣队 · `Command`⇒指挥部 · `Fire Command`⇒火力指挥部 · `Evacuation`⇒撤退 · `Counter Attack`⇒反击战 ·
`Minensuchboot`/`Minenräumboot`⇒扫雷艇 · `Schnellboot`⇒鱼雷艇 · `U-Boot`⇒U 艇 ·
`SS`⇒党卫军（`1SS`⇒党卫军第1装甲师；`SS-Div.[LAH]`⇒警卫旗队师；⚠️ 原文无 `LAH` 就不要写「警卫旗队」）·
`JG-14`⇒第14战斗机联队 ·
⭐ **`F.Korps`/`Feldkorps`/`Luft`（军级）⇒一律写「航空军」**（不要写「航空野战军」）
半字母连/营：`A/I/504th/82nd`⇒A连/I营/第504团/空降第82师 · `2/1/HG/HG`⇒第2营/第1团/赫尔曼·戈林师/赫尔曼·戈林军

### 勋章
`Distinguished Service Cross`⇒优异服务十字勋章 · `Legion of Merit`⇒功绩勋章 · `Silver Star`⇒银星勋章 ·
`Soldiers Medal`⇒士兵勋章 · `Bronze Star`⇒铜星勋章 · `Air Medal`⇒航空勋章

### 其他
日期 `September 8, 1944`⇒1944年9月8日 · 计数 `Distinguished Service Cross: 47`⇒优异服务十字勋章：47 ·
`Redux`⇒`：重制版` · 字母缩写若**无法确证所指**（如 `GH`、`NG`、`KK`）⇒**原样保留**并在报告里列出；
⚠️ 但**能确证的德语军史术语**要译准（如 `SSV`=SS-Verfügungstruppe⇒**党卫队特别机动部队**，不是「特别任务部队」）

### ⚠️ 专名务必「对号」——不要张冠李戴
实测抓到的真实错译：`Minenräumboot Dantzig`（但泽号扫雷艇）与 `Minenräumboot Dresden` **被译成同一个名字**，
而 `Dantzig`(=Danzig) 是**但泽**、`Dresden` 是**德累斯顿**，是两座不同的城市。
⇒ **近似专名必须逐个核对**：`Dresden`⇒德累斯顿 · `Danzig/Dantzig`⇒但泽 · `Königsberg`⇒柯尼斯堡 ·
`Breslau`⇒布雷斯劳 · `Stettin`⇒斯德丁 · `Danzig`≠`Dresden`。

### ⭐ 遇外语编制缩写：**先查术语库先例，有先例必须沿用**
本工作区已有 12.8 万条译名总库，法/意/波/芬等**外语编制缩写多已有定译** —— 不要自己另创：
```
3e DIC      ⇒ 3殖民地步兵师        （DIC = Division d'Infanterie Coloniale）
1 DIC       ⇒ 第1殖民地步兵师
14 RTS      ⇒ 第14塞内加尔狙击兵团
1 DLC       ⇒ 第1轻骑兵师          （DLC = Division Légère de Cavalerie）
DLM         ⇒ 轻机械化师           （Division Légère Mécanique）
LMB         ⇒ 轻机械化旅
GRDI        ⇒ 殖民地步兵侦察团
RIC         ⇒ 殖民地步兵团
```
⚠️ 实测教训：有子代理把 `3rd DIC` 保留成拉丁 `DIC步兵师`，而术语库 10+ 条先例都是「殖民地步兵师」⇒ 已订正 5 行。
⚠️ 同样地，**层级要一致**：`NN/NN DIC/[X]/NN` 末段是**集团军**（不是「师」）。

## 交付前自检
① 行数 == 输入数据行数 ② 译文列零空值 ③ 译文无 TAB/换行 ④ 第一列与输入逐字节一致 ⑤ 无 BOM

## 报告（**简短**）
1. 实填行数 / 输入数据行数 / 产出文件 SHA256
2. 拿不准条目（最多 10 条：`原文 → 你的译法 → 疑点`）
3. 被判定为**元数据行**而原样保留的条数
4. 你据此**意译的外语普通名词/通名**清单（供全项目统一）
