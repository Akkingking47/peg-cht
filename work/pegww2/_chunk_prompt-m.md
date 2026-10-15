# 小片翻译任务口径模板（场景层 · 地图格名/场名/地名 = m 批）

> **用法**：委派时把本文件路径给对方，并告知「本片编号 NN」。对方按本文件执行即可。
> 修订：2026-10-11 v2（补 3 条裁定：引号体例 / 类型标记保守不译 / Encirclement 分工）

## 你的角色
你在做一个**个人研究用途**的二战老游戏汉化项目（*People's General* 的二战 MOD「PeG-WW2」）。
工作区 `D:\DSH\军事游戏汉化`。全程只做语言转换，**不改原文的世界观、阵营划分与叙事措辞**。

⚠️ 这是**小批任务**（≤600 行）。请**一次性读完、一次性写完**，**不要**做多余的探索性浏览（宿主要省资源）。

## 任务
把 `D:\DSH\军事游戏汉化\pegww2\research\_scn-todo-m-NN.tsv`（NN = 本片编号）
里的**地图格名 / 场名 / 地名**逐条译成简体中文。

### 输入格式（TSV；前 2 行注释 + 1 行表头，其后为数据）
```
# 场景层待填批次: m（原文 / 译文(留空待填) / 类 / 出现文件数 / 出现次数）
# ⚠️ 只改「译文」列；不得增删行；UTF-8 无 BOM；TAB 分隔；译文内不得含 TAB/换行
原文	译文	类	出现文件数	出现次数
Kalatsch (#1)		 m 地图格名	71	445
Don River		 m 地图格名	30	120
```

### 产出（**新建，不要改输入文件**）
`D:\DSH\军事游戏汉化\pegww2\research\_scn-fill-m-NN.tsv`
**只有两列**，行序与输入**完全一致**：
```
原文	译文
Kalatsch (#1)	卡拉奇 (#1)
Don River	顿河
```
- 第一列**逐字照抄**输入「原文」列（**含任何 `\t`/`\xNN` 反斜杠转义序列，一个字符都不能改**）
- UTF-8 **无 BOM**；TAB 分隔；**译文内绝不能含 TAB 或换行**；**译文列零空值**

## 译法口径
1. **纯译，绝不加原文括号**（`_m` 一律不加 `(原文)`）。
2. **地名用中国通行译名**：
   `Stalingrad`⇒斯大林格勒 · `Warsaw`⇒华沙 · `Kharkov`⇒哈尔科夫 · `Kursk`⇒库尔斯克 ·
   `Kalatsch`⇒卡拉奇 · `Breslau`⇒布雷斯劳 · `Koenigsberg`⇒柯尼斯堡 · `Brest-Litovsk`⇒布列斯特-立托夫斯克 ·
   `Don River`⇒顿河 · `Volga`⇒伏尔加河 · `Dnieper`⇒第聂伯河 · `Oder`⇒奥得河 · `Warta`⇒瓦尔塔河 ·
   `Caucasus`⇒高加索 · `Crete`⇒克里特岛 · `Sicily`⇒西西里岛 · `Normandy`⇒诺曼底 · `Ardennes`⇒阿登 ·
   `Bastogne`⇒巴斯托涅 · `Carentan`⇒卡朗唐 · `St Vith`⇒圣维特 · `Viipuri`⇒维堡 · `Seelow Heights`⇒塞洛高地
   通名要译出（River/Sea/Lake/Mount/Island/Peninsula/Canal/Forest/Airfield/Flughafen/See 等）。
   `XXXwald`（德语「林」）⇒「XX林」；`XXX Flughafen`⇒「XX机场」；`XXX See`⇒「XX湖」。
3. **编号/标记原样保留**（数据不动）：`(#1)`、`(#7d10)`、`(7d#9)`、`RTB#15`、`7d#11`、`PeG:WW2`、坐标 `(05,23)`、拉丁番号。
   `The Battle for Berlin (#7d10)`⇒`柏林之战 (#7d10)` · `Invasion Salerno PeG:WW2`⇒`萨莱诺登陆 PeG:WW2`
4. **行动名/战役名**用军事通名：`Operation Torch`⇒火炬行动 · `Operation Shingle`⇒鹅卵石行动 ·
   `Operation Zitadelle`⇒堡垒行动 · `Operation Nordwind`⇒北风行动 · `Operation Charnwood`⇒查恩伍德行动 ·
   `Operation Goodwood`⇒古德伍德行动 · `Market Garden`⇒市场花园行动 · `Overlord`⇒霸王行动 ·
   `Barbarossa`⇒巴巴罗萨行动 · `Wacht Am Rhein`⇒莱茵守望 · `Unternehmen Sonnenblume II`⇒向日葵行动 II ·
   `Battle of the Bulge`⇒突出部之战 · `The Battle for X`⇒X 之战 · `Invasion X`⇒X 登陆
5. **元数据行原样保留（译文＝原文）**：`Dummy`/`dummy` · 以 `Version`/`Gameset`/`Equipment`/`Note`/`Source`/`BTW` 开头的文件头行 ·
   纯符号行（`---------`）· 纯拉丁字母数字串（无实义词的番号/代码，如 `KC`、`RSG`、`RF`、`[XX]`、`SM/RM`、`10 Pz Div`、
   `A/I/501st/101st`、`2/8/19/6th Australian`、`Recon/16`、`1RTR/22/7`、`7/2/Luft I`）
6. **型号/番号里的拉丁字母数字保留**：`T-34/76`、`M4A1`、`SdKfz 251`、`Pz IV`、`ErPrGr210` 等不翻。
7. ⭐ **类型标记（`: XXX` / `#XXX` / `(XXX)`）**：
   - `#` 后的自然物通名照译：`#LAKE`⇒`#湖` · `#Supply`⇒`#补给点` · `#Xxx River`⇒`#xx河` · `#Xxx Wald`⇒`#xx林`
   - ⭐ **括号里的类型标记也要译**（实测它只是地图格名的显示注记，引擎无按关键字解析的证据；中文界面不该留英文）：
     `Calais (PORT)`⇒`加来（港口）` · `Copenhague (OCEAN)`⇒`哥本哈根（海洋）` ·
     `Aube River (impassible)`⇒`奥布河（不可通行）`（原文 `impassible` 系 `impassable` 拼写误，按语义译）
     ⚠️ **编号类标记一律原样**：`(#NN)`、`(#NN Lower)`、`(RTB#NN)`、坐标 `(NN,NN)`、`[XX]`、`[XXXVIII]`
   - ⚠️ **冒号后全大写标记（`: RIVER`）**：若遇到，译作「：河流」并在报告里列一条（注明无先例）
   - ⚠️ 译文里**全角括号前不要留空格**：写 `加来（港口）`，**不要**写 `加来 （港口）`
8. **禁用**：`國力`/`佔領`/`光榮勝利`/`前進觀測官`/`改良裝備` 及其简体形式；`声望`（Prestige 统一作「威望」）。
9. ⭐ **引号体例统一用 `「」`**（不用弯引号 “ ”）：`"Hold Bastogne"`⇒`「守住巴斯托涅」`
10. 一律**简体中文**，不用生僻字；同一地名在不同场景必须同一译法（本表按原文串键控）。
11. ⭐ **Encirclement 分工**：作为**战役/场名**时作「**包围战**」（`Uman Encirclement`⇒乌曼包围战）；
    作为**叙事描述**时作「**合围**」。`Kessel`/`Cauldron` 意作「包围圈」。
12. **MOD 原文拼写变体一律按原文音译，不擅自回改成史实拼法**（如 `Liepzigwald`⇒莱比锡林、`Giescin`⇒吉耶钦）。
    ⚠️ 例外：若两种拼写差异**仅限变音符号或明显拼写噪声**且指同一实体，可用同一中文名（并在报告里注明）。
13. ⭐⭐ **外语普通名词 ⇒ 意译；只有人名/地名专名才音译**（本作地图名里有大量德/波/芬/俄语**通用区域标签**）：
    `Vorstadt`⇒郊区 · `Provinz`⇒省区 · `Gutshof`⇒庄园 · `Bordellviertel`⇒红灯区 · `Nirgends`⇒无处 ·
    `Flughafen`⇒机场 · `See`⇒湖 · `Wald`⇒林 · `Bahnhof`⇒车站 · `Rathaus`⇒市政厅
    ⚠️ 判据：该词在德/波/芬/俄语里是**普通名词**（词典里有实义） ⇒ 意译；是**人名/地名**（仅此一处专有） ⇒ 音译。
    报告里请列出你据此规则**意译**的条目（便于全项目统一）。
14. ⭐ **冒号后全大写类型标记（`: RIVER`/`: PORT`）译出**：`Wadi Kbir : RIVER`⇒`克比尔干河 : 河流`。
    （工作区词库已有先例：`Alexandria : PORT`⇒`亚历山大 : 港口`；保留「空格+半角冒号+空格」原格式）
15. **无括号的地名 + 通名大写**（如 `Queenstown PORT`、`Annapolis PORT`）⇒ 通名照译：`皇后镇港`／`安纳波利斯港`
    （⚠️ 与 `(PORT)` 同义；不要留英文 `PORT`）

16. ⭐ **`: Redux` ⇒ `：重制版`**（半角冒号+空格一律改全角冒号、不留空格）：
    `Kishinev: Redux`⇒`基什尼奥夫：重制版` · `Lillehammer:  Redux`⇒`利勒哈默尔：重制版`
17. ⭐ **外语通名务必意译**（第 13 条的具体通名，已实测出现过，请照此）：
    `Mare`⇒海（`Mare Piccolo`⇒小海 · `Mare Grande`⇒大海）· `Forst`⇒森林（`Forst Sammtholz`⇒萨姆霍尔茨林）·
    `Kolpos`⇒湾 · `vatn`⇒湖 · `fjorden/fjord`⇒峡湾 · `hegy`⇒山 · `ko`⇒峰 · `Til`⇒至 ·
    `Air Field`⇒机场 · `Ft.`⇒堡 · `Fisheries`⇒渔场 · `Farm`⇒农场 · `Wildlife Refuge`⇒野生动物保护区 ·
    `Woods`⇒林地 · `Causeway`⇒堤道 · `Observation Point`⇒观测点 · `harbour`⇒港 · `Highway/Hwy.`⇒公路
18. ⚠️ **第 5 条（原样保留）只适用于「无实义词的纯代码」**：若串里含**真实专名**
    （如 `Washington'46`、`New York '46`）⇒ **名要译出**（`华盛顿'46` / `纽约 '46`），不得整串保留。
    `CreationTime = 786816768 29211467`、`BoB04.scn`、`4CLY/22/7`、`II/JG27` 这类才是「原样保留」。

## 可参考（**只看你需要的，别大范围浏览**）
- `D:\DSH\军事游戏汉化\pegww2\research\各国军语风格口径.md`（口径总纲）
- `D:\DSH\军事游戏汉化\glossary\standard-glossary.tsv`（译名总库，含大量地名）

## 交付前自检
① 行数 == 输入数据行数 ② 译文列零空值 ③ 译文无 TAB/换行 ④ 第一列与输入逐字节一致 ⑤ 无 BOM

## 报告（**简短**）
1. 实填行数 / 输入数据行数 / 产出文件 SHA256
2. 拿不准条目（最多 10 条：`原文 → 你的译法 → 疑点`）
3. 你判为「类型标记原样保留」的条目（若有）
