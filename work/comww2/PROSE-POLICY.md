# COMWW2 `prose` 层（战役说明 / 战斗简报）汉化风格指南（子代理必读）

> efile = `EFILE_COMWW2`（OpenComposite 综合装备文件）。本层是 `TEXT-ZH\SCENARIO\*.txt` 里的**叙事段**
> （战斗简报、历史注记、致谢、说明），**不是**番号/地名短串（那层已由 label 层完成）。

## 一、任务

把自己那份**纯原文清单**逐条译成简体中文，写出**等行数**的 TSV。

## 二、输入 / 输出（严格）

- 输入：`D:\DSH\军事游戏汉化\work\comww2\_prose_rest_partNN.txt`
  格式：每行 `NNN|原文`（`NNN` 是**清单序号**，只用于对齐，**不要抄进译文**）。
- 输出：`D:\DSH\军事游戏汉化\work\comww2\_prose_rest_dst_partNN.txt`
  格式：每行 `NNN|译文`，**序号与输入逐个一致**，行数**严格相等**。
- 编码 UTF-8 **无 BOM**；**不要**表头、注释、空行、代码块、说明文字。译文**单行**（不换行、不含 TAB）。

> ⚠️ 原文里的 ` ⟦T⟧ `（U+27E6/U+27E7）是**制表符占位符**：它代表原文的一个 TAB 分栏，
> 译文必须**原样保留**同样数量的 ` ⟦T⟧ `（游戏里是分栏缩进），其余文字照译。

## 三、文体与口径

### 3.1 称呼（德军/轴心视角的简报常见）

| 原文 | 译文 |
|---|---|
| `Herr General` / `Herr General!` | `将军阁下` |
| `Herr Feldmarschall` / `Herr Feldmarshall`（原文有拼写错） | `元帅阁下` |
| `Herr Oberst` / `Colonel` | `上校阁下` / `上校` |
| `Comrade General` / `Comrade Lieutenant-General` | `将军同志` / `中将同志` |
| `Mein Führer` | `我的元首` |
| `Herr Hauptmann` | `上尉阁下` |

- 称呼后**照原文**加标点（`,`/`:`/`!`）。原文 `Herr General:` → `将军阁下：`（**全角冒号**）。
- 苏军/盟军简报里的 `General` 单独出现 → `将军`；`Comrade X` → `X同志`。

### 3.2 玩家视角

简报是**上级对玩家的训示**，用第二人称「你/你们」；德军视角的 `Herr` 体系保留「阁下」以维持语气，
不要改成「先生」。

### 3.3 胜利等级 / 结果词（全库口径）

`Brilliant Victory`→`辉煌胜利` · `Victory`→`胜利` · `Tactical Victory`→`战术胜利` · `Loss`/`Defeat`→`失败`；
`BV`/`V`/`TV`/`L` 单独出现按此。

### 3.4 标题与战役名

- `Battle of/at/in X` → `X之战`；`YYYY Battle of X` → `YYYY年X之战`；`Operation X` → `X行动`；
  `X Tank Battle` → `X坦克战`；名词性 `Manchurian Operation` → `满洲战役`。
- 散文正文里的 `battle of X` 泛指 → 译「X战役」。

### 3.5 专名

- **地名**用通行中文译名；无通行名则音译（`Rzhev`→勒热夫、`Sevastopol`→塞瓦斯托波尔、
  `Tikhvin`→季赫温、`Brest-Litovsk`→布列斯特-利托夫斯克、`Strasbourg`→斯特拉斯堡）。
- **人名**用通行译名（`Rokossovsky`→罗科索夫斯基、`Manstein`→曼施泰因、`Paulus`→保卢斯、
  `Guderian`→古德里安、`Zhukov`→朱可夫）。
- **装备/舰船/飞机型号保留原文**：`T-34` `KV-1` `IS-2` `Bf-109` `Ju 87` `Tiger`（可作「虎」式，
  但型号串保留原文）`USS Eagle`。
- **部队番号**用「第 + 阿拉伯数字 + 编制」：`6th Army`→第6集团军、`4th Panzer Group`→第4装甲集群、
  `44th Infantry Division`→第44步兵师、`2nd SS Panzer Corps`→党卫军第2装甲军。
- **大写缩写保留**：`OKH` `OKW` `STAVKA` `RAF` `USAAF` `DAK` `LSSAH` `AT` `FlaK` `VH` `BV`。

### 3.6 日期

`Sept 5` → `9月5日`；`July 14` → `7月14日`；`1942` → `1942年`；带年则 `1941年5月14日`（**无空格**）。

### 3.7 编码硬约束

- **GBK 装不下西文变音符**：`ä→a` `ö→o` `ü→u` `é→e` `è→e` `ñ→n` `ç→c` `ß→ss`（人名地名折写 ASCII），
  能译中文的就译中文。
- **不要**在中文里插空格；原文的空格/标点风格尽量保留对应（`...` 保留为 `……`）。
- **不要**使用蔑称、旧称、粗俗语；暴力/处决叙事直译但不渲染。

## 四、交付前自检（必须做，并在回复里报告一行结果）

1. 输出行数 == 输入行数；
2. `NNN|` 序号逐行一致；
3. 每行译文非空、无 TAB、无换行；
4. 原文每行的 ` ⟦T⟧ ` 个数 == 译文同一行的 ` ⟦T⟧ ` 个数；
5. 文件是 UTF-8 **无 BOM**。

## 五、只回复一行

`part-NN 完成，共 N 行；自检通过`（**不要**贴译文内容）
