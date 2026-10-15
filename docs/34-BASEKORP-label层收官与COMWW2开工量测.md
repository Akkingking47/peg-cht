# 34 · BASEKORP `label` 层收官 · `.xscn` 复核 · COMWW2 开工量测

> 本轮按 `docs\30` 三项依序执行：① BASEKORP `label` 层补齐 → ② `.xscn` 疑似漏译 35 条复核 + `efile.xml`/`efile.txt` 提案 → ③ 转入下一个 efile（COMWW2）并完成开工量测。
> 所有数字均为**脚本实测**（`work\audit\progress.py`、`work\basekorp\gen_label_zh.py`），非文档自述。

---

## 一、① BASEKORP `label` 层：78 文件全部部署

### 1.1 层定位（此前被结构性漏掉）

`rep-list.tsv` 的 `kind` 分布是 `prose 1860 / label 78 / empty 2`。散文流程 `translate_prose.py` **按设计只处理 `prose`**，因此 78 个 `label` 文件从未进入工作流 —— 这就是 BASEKORP `.txt` 覆盖率长期卡在 94.4% 的原因。**不是漏译，是分层遗漏。**

`label` 层内容（`EFILE_BASEKORP\SCENARIO\*.txt`）：

| 内容 | 例 |
|---|---|
| 场景名 | `Guadalajara` `Zitadelle` `Crossing the Dnipr` |
| 河名 / 地名 | `Dnepr River` `Volga` `Boulay-Moselle` `Stassfurt` |
| 部队番号链 | `125/21` `M731/711` `2/8 FldRAA/-/9Aus [XXX]` `1,2./II/190/-/90Le [DAK]` |
| 地图设施标记 | `State Farm` `Harbour` `Blown Bridge - repair crew needed` |
| 战役说明 / 简报头 | `ROMANIAN CAMPAIGN 1941-1945` `Kustrin` `Herr General` |

### 1.2 规模与结果

| 指标 | 值 |
|---|---|
| `label` 文件 | **78** |
| 非空行（实例） | **6,589** |
| 唯一行 | **3,153** |
| 其中「含字母 或 纯数字番号」需处理 | **3,153**（全部） |
| 唯一行有 `.xscn` 译法可直接复用 | **2,955（93.7%）** |
| 需人工精译的缺口 | **200 条** |
| 输出汉字 | **27,402** |
| 字节 | 75,679 → 83,712 |

**关键做法：复用 `.xscn` 既有译文。** `.xscn` 尾部串区**组 0 就是本 `.txt` 名单的镜像**（组 1 是部队番号链）。因此 `bk-xscn-map.tsv`（31,741 条 `src→dst`）天然覆盖本层 93.7% 的唯一行 —— **复用即自动满足跨层一致性铁律**，无需另起译法。

实例验证（`ac821salern.xscn` 组 1 ↔ `ac821salern.txt`）：`第1/第36`、`第3/第36`、`第1/第22`、`第41`、`第751`、`美国陆军航空队`……逐条对应 `.txt` 的番号行。

### 1.3 覆盖率变化

| 指标 | 起点 | 终点 |
|---|---|---|
| BASEKORP `.txt`（`progress.py` 口径） | 2,266（94.6%） | **2,338（97.7%）** |
| BASEKORP `.txt`（实际部署数） | 2,266 | **2,344（97.9%）** |
| 未部署 `.txt` | 128（78 label + 50 空壳） | **50（全部空壳）** |

⇒ `.txt` 侧**已无未译内容**：剩余 50 个文件 `strip()` 后为空，无可译文本。

### 1.4 两个必须记住的坑

1. ⚠️ **`bk-xscn-map.tsv` 是三列** `src \t dst \t note`（note ∈ `det/llm/cross/det-resid/title`，共 31,742 行全部带 note）。
   用 `line.split("\t", 1)` 读会把 note 并进译文 → **静默往标签行里塞进制表符**（本层会污染 6,236 个实例）。
   正确读法＝`split("\t")` 取 `c[1]`，与 `xscn.py::load_map` 一致。本层生成器已加「译文含 `\t/\r/\n` 即报错」守卫。
2. ⚠️ **`¯`(U+00AF) 在 GBK 无编码** —— `dragrom.txt` 第 2 行是 29 个 `¯` 构成的标题下划线。裸写会落在 cp1252 高字节区间（正是「假汉字」陷阱）。
   已按视觉等价替换为 `─`(U+2500, GBK `A9A4`)，生成器内置 `¯→─` 兜底 + 逐行 GBK 前置校验。

### 1.5 残留（41 个唯一行 / 130 实例，均**按口径保留**）

`L1 L4 L5 L FC NG FA ELAS DG CSIR BC TNG GM L D/SSV G/SSV DF/SSV SSV E AASC 1H N T RF RM DG3 DG4 RSG PC PA 25H 2H SM/RM IA Z P SST SM 1N 2LC 5LC 1P`

全部是 `.xscn` 侧**恒等映射**（有意保留的大写缩写/单字母标记，符合 `RULES.md` §三「单字母标记吃不准时原样保留」）。本层与 `.xscn` 完全一致，**不改**。

---

## 二、② BASEKORP `.xscn` 疑似漏译 35 条 —— 复核结论：**全部为口径保留，无需补译**

判据：`work\basekorp\_dump_xscn_leak.py`（直接复用 `progress.py` 的 `is_zh`/`kept_style`，导出清单 `_xscn_leak_basekorp.tsv`）。

| 类 | 条数 | 例 | 判决 |
|---|---:|---|---|
| 潜艇番号 + 指挥官 | 4 | `U-185 Ezne` `U-69 Manfred Von Egge` | 口径「舰名/番号保留原文」 |
| 舰名（`'` 昵称前缀） | 25 | `'Nagato` `'Akagi` `'Yamato` `'Musashi` `'Puppyhouse` | `RULES.md` §二.7「引号昵称音译即可，或保留原文」；且与本工程散文层对 `'Frau-Z` `'Batt` `'Kondor` 的处理**一致** |
| 架空自造名 | 5 | `Ways Merkso` `Fanelli Oilks` `'Yuree Licthgrossweich` `'Ronett Refrestkoft` | ssbdm 架空战役的德式伪造词，译出即毁梗；保留 |
| **解析假象（非文本）** | 1 | `bc_it_teu.xscn` = `\x04q~\xde\x90\x0c` | 串区里的二进制槽（占 `u16 len + L 字节`）；原字节 `06 00 04 71 7E DE 90 0C`，前后邻居均为正常 GBK 中文 ⇒ **不是翻译缺口** |

35 / 48,491 = **0.07%**，远低于 0.5% 的「完成」阈值；且逐条可归入口径。**结论：不补译、不改 `.xscn`。**

> 备注（不建议本轮改）：`kept_style()` 启发式**不认识** `'Xxx` 昵称前缀与 `U-\d+` 潜艇号，故把它们计入 leak。可在后续「指标卫生」一轮里补这两个模式，使 leak 读数与实际口径对齐 —— 这属于改真源脚本，**先报不改**。

> ⚠️ **更强的一条**：35 条里唯一那条「非文本」之所以会**出现在审计的 leak 计数里**，根因是
> **`progress.py::parse_xscn` 没有同步 `MECHANICS.md` §18 的 `_printable` 守卫**。
> §18（2026-09-28）把「跳过登记、仍推进 `off`」的修复只做进了 `work\xscn\xscn.py::parse`，
> 而 `progress.py` 是**另一份独立实现**，它把每个 `u16 长度 + L 字节` 槽**无条件登记为可译条目**。
> 实测全库有 **16 个非文本槽**被当条目计数（BASEKORP 5 / KAISER 5 / OPENAK 5 / LXF 1），
> 其中 BASEKORP 有 1 个落进了 leak。⇒ 条目数偏大 + leak 虚高。
> **修法**：把 §18 的守卫照搬进 `progress.py`。属真源脚本变更，**先报不改**。同一实现分叉，值得后续一轮「指标卫生」一并处理（与该文档 §19.1 的 `kind` 启发式、§20 一起）。

---

## 三、② `efile.xml` / `efile.txt` —— 机制已定位，交付机制待批

### 3.1 机制（exe 实据）

exe `.text` FO `0x4F6480` 附近字符串表：

```
... %sefile.txt \0 SCENARIO \0 USERSCEN \0
    "No efile.txt nor .xml found" \0  %sefile.xml \0
    "No efile.txt nor .xml found" \0
    \n\r \0 \n\r \0  Efile\xa3\xba \0  "Author: " \0  <author> \0  "Version: " \0
```

- 引擎**先找 `efile.txt`，回退 `efile.xml`**（错误串顺序 + 两条模板）；
- 解析方式＝**按标签行取文本**（字面量 `<author>`、`Version: `、`Efile：` 都在表里）；
- ⚠️ `Efile\xa3\xba` = **GBK「Efile：」** —— 本工程早前插入的中文，说明该处显示链**能出中文**。

### 3.2 `efile.txt` 是行式格式（GBK 安全）

`EFILE_AG\efile.txt` 样例：

```
* This is an Efile description file
* Please don't change the number and order of the lines.
<title>Antique General
<description>Historical and fictional Battlefields of the Antique
<version>3.4."Britannia"
<author>S. de Mont Tonnerre
<url>http://antique-general.jimdo.com/
```

⇒ **行数与行序固定**（文件自述），只需替换标签后的文本。**行式解析 ⇒ GBK 字节安全**（与已交付的 `*.txt` 同构）。

### 3.3 BASEKORP 现状与三个候选交付机制

BASEKORP **只有 `efile.xml`**（无 `efile.txt`），且**全库 15 个 `efile.xml` 非 ASCII 字节均为 0** ⇒ XML 解析器的编码行为**无先例可依**。真 XML 里裸写 GBK 有乱码/解析失败风险。

| 机制 | 做法 | 风险 | 备注 |
|---|---|---|---|
| **A** `TEXT-ZH\efile.txt` | 新建语言目录下的 `efile.txt` | 低（不动原文） | 依赖「LangDir 前缀也适用于 `%sefile.txt`」这一**假设**（`strings_efile.txt` 已实证走 LangDir，但 `efile.txt` 未实证） |
| **B** 根级新建 `efile.txt` | 放在 efile 根，靠「.txt 优先于 .xml」覆盖 | 中（新增根级文件） | 优先级未实证 |
| **C** 原地改 `efile.xml` | 加 `<?xml version="1.0" encoding="GBK"?>` + GBK 中文 | 中高（覆盖原文） | 违反「绝不覆盖改原文」纪律，需先备份 |

**草案（未部署）**：`work\comww2\efile.txt.draft`

```
* This is an Efile description file
* Please don't change the number and order of the lines.
<title>OpenComposite（联合战争2）
<description>为 Open General 改编的合成装备文件。
<version>1.02F
<author>MG43
```

**⇒ 待批项**：机制选 A / B / C（推荐 **A**，再退 B；C 需原文备份）。

---

## 四、③ COMWW2 开工量测（`docs\24` B5）

`EFILE_COMWW2` 当前 **0%**，无 `TEXT-ZH` 目录。实测：

| 层 | 量 | 备注 |
|---|---:|---|
| `.xscn` | **182 文件 / 18,030 串 / 唯一 9,252（含字母 7,913）** | 与 BASEKORP 同结构；`L9` |
| `.txt`（SCENARIO） | **1,032 文件 / 21,870 非空行 / 唯一 11,474（含字母 9,884）/ 327,712 字符** | 需先建 `rep-list` 分层（prose/label） |
| `.tmsg` | **20** | 原地改（无覆盖层） |
| `.front` | **199** | 待判（疑似阵线数据，可能非文本） |
| `.xcam` | **10** | 战役标题 |
| `.doc` | 1 | 待判 |
| 根级 | `equip.txt` 4,054 行 · `names.txt` 992 · `fronts.txt` 679 · `weather.txt` 140 · `strings_efile.txt` 113 · `nations.txt` 42 · `colors.txt` 13 · `efile.txt` 6 | 四件套 + `efile.txt` |
| `OPENGUI` | 36 个（含 `hex_text.png` 需重绘、`dlg_*.png` 面板） | `L8` |
| `OPENDAT` | 9 个 png | 待判 |
| `TEXT-ZH` | **不存在** | 从零建 |

### 建议开工顺序（依 AO/ATOMIC 已验证的次序）

1. **根级四件套 + `efile.txt`**（`equip` / `names` / `nations` / `strings_efile`）—— 有 AG/AO 现成工作台可套，风险最低；
2. **`strings_efile.txt` 覆盖层**（每 efile 必写，缺则回退 exe 英文表）；
3. **`.xscn` 全量导出 → 建 `bk-xscn-map` 式映射表 → 分批译**（18,030 串，最大块）；
4. **`.txt` 分层**（先 `txt_workbench.py` 出 `rep-list` / `blocks`，再散文 + `label` 两层分别走）；
5. `.tmsg`（20 个，结构已知）；
6. `L8` 位图（`hex_text` 重绘）。
7. `.front` / `.xcam` / `.doc` 性质判定后再定。

---

## 五、附带发现（未改，待批）

⚠️ **`progress.py` 的 `.txt` 判据漏计短标签文件。**
判据是 `zh_score(中文侧) >= 3`（最长**连续**汉字段 ≥3）。但 `bberlin.txt`＝「柏林」、`bchannel.txt`＝「海峡」、`bdenmark.txt`＝「丹麦」、`bdover.txt`＝「多佛」、`bnether.txt`＝「荷兰」、`cm4don.txt`＝「顿河」这 6 个文件的中文段只有 2 字 ⇒ **被判为「未中文化」**。

⇒ BASEKORP `.txt` 实际 **2,344**，报表为 **2,338**（差 6）。该偏差**对全库所有短标签文件成立**（不只 BASEKORP）。
建议改为 `zh_score >= 3` **或**（`zh_score >= 2` 且无残留拉丁字母），但**这是改真源脚本，先报不改**。

---

## 六、本轮产出文件

| 文件 | 说明 |
|---|---|
| `work\basekorp\gen_label_zh.py` | `label` 层生成器（两阶段：全算完→无缺口才落盘；`--dry` 干跑） |
| `work\basekorp\label-zh.tsv` | 缺口人工译表 200 条 |
| `work\basekorp\_dump_xscn_leak.py` · `_xscn_leak_basekorp.tsv` | `.xscn` 疑似漏译导出器与清单 |
| `work\comww2\_measure_comww2.py` | COMWW2 全层量测脚本 |
| `work\comww2\efile.txt.draft` | `efile.txt` 中文草案（**未部署**） |
| 部署产物 | `EFILE_BASEKORP\TEXT-ZH\SCENARIO\*.txt` ×78（GBK / 无 BOM / CRLF） |

---

## 七、续办：三条按推荐执行（2026-09-29 下午）

> 用户批复「三条都按你推荐的来，主旨不能影响游戏运行」。
> 硬约束落地方式：**所有写入都不触碰任何原文侧文件**；失败模式一律设计为「不显示中文」而非「崩/改坏」。

### 7.1 ① `efile.xml` —— 机制 A 已交付，原文零改动

先取证，再落盘：

| 证据 | 内容 |
|---|---|
| exe `.text` FO `0x4F6480` | `%sefile.txt`（唯一 `push imm32` 引用）、`%sefile.xml`、`"No efile.txt nor .xml found"`、`<author>`、`Version: `、**`Efile\xa3\xba`＝GBK「Efile：」**（本工程早前插入） |
| `%sefile.txt` 的唯一 `%s` | 是**文件名前缀**（`strings_`）—— `MECHANICS.md` §15.1 明确 `strings_efile.txt` 就是这条模板拼出的 |
| ⇒ 推论 | `efile.txt` 与 `strings_efile.txt` **同函数、同目录解析**；而 `TEXT-ZH\strings_efile.txt` 已在 6 个 efile 上验证生效 ⇒ `TEXT-ZH\efile.txt` 走同一目录 |
| 反证检查 | 全库 15 个 `efile.xml` 非 ASCII 字节 **均为 0**（XML 编码行为无先例）；6 个根级 `efile.txt` 亦全 ASCII ⇒ 这是一层**尚未开过的新层** |

交付：`EFILE_BASEKORP\TEXT-ZH\efile.txt`（362 B，GBK / 无 BOM / CRLF / 7 行，与 `efile.txt` 规范行序严格一致）

```
* This is an Efile description file
* Please don't change the number and order of the lines.
<title>Open BaseKorp 装备文件
<description>Basekorps 二战装备文件的开放化版本。BKefile 与 AdlerKorp 大多兼容，但包含一些额外单位，并加入了本人的构想。
<version>Aug 2019
<author>Brian Gosley
<url>http://www.panzercentral.com/forum/viewtopic.php?f=132&amp;t=46498
```

**内容口径（保守）**：只译 `<title>`（显示名）与 `<description>`（自由文本）；
`<version>` 保持原文 —— `Settings.cfg` 有 `EVersion` 键，版本串可能与存档兼容性判断相关；
`<author>` / `<url>` 按既有 5 个 efile 惯例保留原文。

校验：`EFILE_BASEKORP\efile.xml` 仍为 **461 B / 非 ASCII 0** ⇒ 原文未动。
备份：`work\basekorp\_bak_efile.xml.before-meta`。生成器 `work\basekorp\gen_efile_meta.py`。
**状态：待实机确认**（若引擎不读该层，则回落显示英文，游戏不受影响）。

### 7.2 ② `progress.py` 三处判据已修（真源）

见 `MECHANICS.md` §20（订正）/ §21。要点：

| 修正 | 效果 |
|---|---|
| `parse_xscn` 补 `_printable` 守卫（§18） | 全库条目 298,433 → **298,430**（−3）；leak −3；**已交付 6 个 efile 逐格不变** |
| `.txt` 加「≤2 字短标签」分支 | `.txt` 已中文化 5,071 → **5,078** |
| `.txt` 分母剔空壳（同 `.ply` 口径） | BASEKORP `2,338/2,394(97.7%)` → **`2,344/2,344(100.0%)`**，进入「完成」列表 |

⚠️ **订正我上一轮报告中的一处夸大**：上轮称「全库 16 个非文本槽被当条目计」——
那是用了一个**偏严的**试探判据（把 0x7F/0x80/0xFF 也算非文本）。按 §18 的真实判据复测，
**全库实为 3 个**（BASEKORP / OPENAK / LXF 各 1；KAISER 实为 0）。

`docs\00` §三 生成区块已重跑覆盖；「其余 efile 工作量」手写投影重算为 **15 个 efile**：
`.xscn` 223,964 条 / 111,067 唯一、根级四件套唯一串 37,331、场景 `.txt` 11,221 个 / 7,249 KB、`.ply` 有正文 14。

### 7.3 ⚠️ 附带暴露：`ATOMIC` 并未真正收官（未修，待决）

新矩阵下 `ATOMIC` `.xscn` 含汉字 16,545/17,576（94.1%）、**疑似漏译 761**（4.3%）⇒ 不在「完成」列表。
抽样确认是 **cp1252 原文残留**（`F黵stenwalde`=Fürstenwalde、`7. Fallschirmj鋑er-Division`、
`K鋠linge River (L鰀de River)`），不是舰名。独立探针（`work\audit\_xscn_untranslated_probe.py`）复核 **324 条**；
同探针下 AG/AO/NASHORNPBEM/OPENPG **均为 0** ⇒ 探针有效、ATOMIC 确有条目未译。
**与 `MEMORY.md`「ATOMIC 全译」的记载冲突，需按 `docs\24` 决定是否补一批。**

---

## 八、③ COMWW2 根级四件套：2/4 已交付

工作台：`work\comww2\`（`measure_root.py` 量测 · `gen_root_zh.py` 生成器）。

### 8.1 生成器的填译优先级（全部**证据驱动**）

1. **donor 精确译文** —— 同名文件在已交付 efile 里的「原文行 → 译文行」（行对齐，`MECHANICS.md` §16）
2. **donor 恒等保留** —— 同名原文行在 donor 的 `TEXT-ZH` 里**与原文完全相同** ⇒ 既有口径就是「保留原文」
3. **词级映射** —— 从 donor 对齐对里自动学「拉丁词 → 中文」，⚠️ **只收军事编制/装备类别型**
   （含 兵/军/师/团/旅/营/连/队/炮/卫/预备/迫击/登陆）；否则会把专名学进来
   （donor 里 `Alaska`→阿拉斯加、`Elephant`→战象），用在 COMWW2 的**舰名/机型行**上即误译
4. **保留原文** —— 仍无依据者保持原文（口径：装备型号 / 舰名 / 编号保留）

⚠️ **方法学要点**：「donor 恒等保留」**只对 `equip.txt` / `strings_efile.txt` 算证据**。
`names.txt` 是人名表，口径是「音译 / 通行译名」，donor 里的恒等行更可能是 **donor 自己的漏译**
⇒ 若当口径继承，缺口会被静默传染。

### 8.2 实测与产出

| 文件 | 原文 | 处理 | 状态 |
|---|---:|---|---|
| `nations.txt` | 44 行 | donor 译文 30 · 人工 4 · 保留 7（`*` 注释） | ✅ **已发布** |
| `strings_efile.txt` | 122 行 | donor 保留 42 · donor 译文 65 · 人工 4 · 保留 1（`FlaK` 按口径） | ✅ **已发布** |
| `equip.txt` | 4,055 行 | donor 保留 2,342 · donor 译文 757 · 词级 160 · 待译 ~794 ⬜ | ⬜ 未发布 |
| `names.txt` | 993 行 | donor 译文 823 · 待译 **169** ⬜ | ⬜ 未发布 |

发布校验：行数逐行一致 ✅ · 无 BOM ✅ · 无裸 LF ✅ · GBK ✅ · 原文侧非 ASCII **0**（未改动）✅

两处人工修正（词级替换会留下英文残块）：
`Waffen SS`→`武装党卫军`（避免 `Waffen 武装党卫军`）、`U.S. Marines`→`美国海军陆战队`（避免 `U.S. 海军陆战队`）。

### 8.3 为什么 `equip.txt` / `names.txt` **本轮不发布**

- **`equip.txt`**：954 行无 donor 证据，其中约 **500+ 行明确需要翻译**而非保留 ——
  `Light Infantry`／`Pionier`／`BrueckenPionier`／`Grenzwacht`／`FallschirmJaeger`／`Lastpferde`／
  `Civil Defence`／`Sturmtruppen`／`Aufklaerer`／`Kevyt Osasto`／`Command Train`／`Dragons Teeth`，
  以及**罗马化中文** `Gong Bing`(=工兵)、`Qiao Jie`(=架桥)、`Chang Gon`(=长江)、`Shuiyun`(=水运)、`Jijun`…
  （与 `docs\25` AG 批「拼音实为年号/帝名，必须用汉字本体」同型）⇒ 需专门一遍，不能「看着差不多」就发。
- **`names.txt`**：169 条人名未译。若只发 823 条会形成**中英混排**，违反 AG 批已确立的
  「层内不得中英混排」用户裁定 ⇒ **不发**。
  口径先例：日文姓氏用**汉字**（donor 实证 `Yamamoto→山本`、`Sakai→酒井`、`Nishimura→西村`、`Ishii→石井`、`Shimada→岛田`、`Kanai→金井`），西文音译。

### 8.4 下一步（COMWW2）

1. `equip.txt`：扩词表 + 人工表（罗马化中文还原汉字、各语种编制词），过一遍再发；
2. `names.txt`：译 169 条（日文用汉字姓氏，西文音译），整层一次性发布；
3. 然后按 §四 次序推进 COMWW2 其余层（`strings_efile.txt` 覆盖层已完成 → `.xscn` 18,030 串 → `.txt` 1,032 文件 → `.tmsg` 20 → `L8` 位图）。

---

## 九、③ COMWW2 根级四件套：4/4 已交付（2026-09-29 续）

### 9.1 结果

| 文件 | 原字节 / 行 | 已译/改写行 | 保留原文行 | 说明 |
|---|---:|---:|---:|---|
| `equip.txt` | 43,044 / 4,055 | **1,186** | 2,867 | 保留中含 **2,354 行有 donor 证据**、**275 行型号/舰名/舰级**（口径）、**43 行待考** |
| `names.txt` | 10,036 / 993 | **990** | 2 | 仅 `Monkeyboy` / `Super64`（测试者昵称，AG 批已立「昵称保留」先例）⇒ **全层无中英混排** |
| `nations.txt` | 729 / 44 | **34** | 7 | 保留＝7 行 `*` 注释（引擎跳过） |
| `strings_efile.txt` | 1,805 / 122 | **70** | 42 | 保留＝42 行 `*_Xxx` 注释（引擎跳过） |
| **合计** | — | **2,280** | 2,918 | |

**校验（四文件全过）**：逐行对齐 ✅ · 无 BOM ✅ · 无裸 LF ✅ · GBK ✅ · **原文侧仅 4 个非 ASCII 字节且全部未改**（`equip.txt` 自带 `Ingénieur`×2 / `Montaña` / `Yìyinji` 的 cp1252 变音符）。

### 9.2 本轮新增的两个生成器档位

1. **归一化档**（`NORM` = 折叠空白 + 小写）：专治大小写/空白差异，多捞回 **28 行**（`Atelaj Greu`→重型马车、`Field Hospital`→野战医院、`FlaK`→高射炮…）。
2. **外部人工表** `root-manual.tsv`（`file \t src \t dst`，按 `strip()` 匹配，容 names 的尾部空格填充）+ **键命中校验**：
   任何人工键在原文中找不到就**报错中止**。本轮据此抓出并删除 3 条多余项（`SS Sturmpionier`/`SS Aufklaerer`/`Horses`）。

### 9.3 三个必须记住的口径判断

1. **`X Class` 按「保留原文」**。donor 里 246 条 `X Class` **绝大多数保留**（`Akagi Class`/`Bismarck Class`/`Alaska Class`），只有少数译（`Barracuda Class`→梭鱼级）。
   ⇒ 必须**从学得词表里剔除 `Class`**，否则会造成少口径不一致（本层仍出现的 `O 级`/`兹奈姆级` 是**某 donor 的原译**，属"跟随上游"，予以保留）。
2. **`FlaK` 在本层译 `高射炮`**。口径「大写缩写保留」指的是 `.xscn`/`.txt` 番号串里的 `FlaK`；`strings_efile.txt` 里的 `Flak` 是**装备类别标签**，ATOMIC 与 BASEKORP 两个 donor 都译了 `高射炮` ⇒ 跟随上游。
3. **`donor 恒等保留` 只能当「装备/结构型」文件的证据**。`names.txt` 是人名表，donor 的恒等行更可能是 **donor 自己的漏译** ⇒ 本层对 `names.txt` **禁用该档**，改为要求实际译文；否则 169 条的缺口会被静默传染（本轮已避免）。

### 9.4 残留登记：43 行「待考」`_todo_uncertain.txt`

罗马字来源不明、按「拿不准就登记，别猜」保留原文，**不发散猜测**：

- **拼音疑云**：`Bao Mai`、`Biao Chema`、`Gao Chema`、`Guang Chema`、`Jiaotache`、`Jijun`、`Kuaiban`、`Shi-Ke`（同 AG 批「拼音实为年号/帝名」那一类，但此处无法确证原字）
- **日文训令/机材名**：`Awai Bahitsu`、`Bahitsu`、`Kabu Bahitsu`、`Soukou Bahitsu`、`Dowa`、`Hara Kamei`、`Keishu`、`Ko-Hi`、`Ko-on Pon`、`Shin Hoto`、`Shiro Rokoku`
- **泰文转写**：`Dtam-ruat`、`Maak ho Mai`、`Mai`、`Paan Pon`、`Pak Naa-wik`、`Pon Maa`、`Raat Jot-mat`、`Reua`、`Sa-mak`、`Saai pan Mai`
- **其它单发词**：`Drushinizi`、`Hadimernok`、`Jakrayaan`、`Mutuski`、`Ossa`、`Oszver`、`Ozzowiachimzen`、`Raba`、`Ratnakosindra`、`T-Truppen`、`Tahun`、`Viuchny`、`Voro`

已确证并译出的罗马化中文：`Gong Bing`→工兵、`Min Bing`→民兵、`Qiao Jie`→架桥、`Chang Gon`→长江、`Shuiyun`→水运、`Zongzhihui`→总指挥、`Shaotan`→哨探、`Yìyinji`→印刷机。

### 9.5 未纳入 `progress.py` 的原因

`work\audit\progress.py` 的矩阵只统计 **`SCENARIO` 下的 `.xscn`/`.txt`/`.ply`**，**不覆盖根级四件套与 `efile.txt`**。
⇒ COMWW2 根级这 2,280 行的进度**不会体现在总表里**，需靠 `MEMORY.md` §一 的 L2–L6 行跟踪。（是否把根级纳入真源统计属独立议题，先报不改。）

### 9.6 COMWW2 下一步

根级四件套 ✅ ＋ `efile.txt` ✅ ⇒ 按 `docs\24` 继续：
**`strings_efile.txt` 覆盖层已含在四件套内** → 下一块是 `.xscn`（182 文件 / 18,030 串 / 唯一 9,252）→ `.txt`（1,032 文件，需先建 `rep-list` 分层）→ `.tmsg`（20）→ `L8` 位图。

---

## 十、追查 43 行「待考」：**部分是日语，但日语只占约 1/4**（2026-09-29 用户提问）

用户问「这 43 行是不是日语的罗马化读音」。用**邻域上下文 + 音系特征**双证据逐条判，答案是：
**是，但不全是** —— 42 条里日语约 1/4，其余是泰语 / 匈牙利语 / 俄语 / 汉语拼音 / 其它。

### 10.1 判据

`equip.txt` 是扁平列表（每行一个装备名），但**同类装备会成簇**：马匹段（`Cavallo`/`Konie`/`Caballos`/`Paarden`/`Hevonen`）、
舰艇段（`Gunboat`/`MTB`/`Kagero`/`Akagi`）、工兵段（`Sapper`/`Utasz`/`Sapeur`）、驮畜段（`Mule`/`Mulas`/`Maulesel`）
—— **邻域即国别/品类证据**。叠加音系特征：泰语 RTGS 的 `aa`/`dt`/`eua`、日语无闭音节（除 `n`）、
匈牙利语 `sz`/`gy`、俄语 `vya`/`zh`。

### 10.2 结论：10 条已确证并译出

| 原文 | 语种 | 依据 | 译 |
|---|---|---|---|
| `Bahitsu` | 日语 | 馬匹 读 **ばひつ**＝bahitsu；邻域为马匹段 | 马匹 |
| `Dtam-ruat` | 泰语 | ตำรวจ＝警察（泰式转写惯用 `dt-`） | 警察 |
| `Jakrayaan` | 泰语 | จักรยาน＝自行车；邻域为车辆段 | 自行车 |
| `Reua` | 泰语 | เรือ＝船；邻域为舰艇段 | 舰艇 |
| `Pon Maa` | 泰语 | พล(兵力)＋ม้า(马)＝骑兵；与 `Ta-haan`/`Sa-mak` 同属兵员段 | 骑兵 |
| `Sa-mak` | 泰语 | สมัคร＝志愿 | 志愿兵 |
| `Hadimernok` | 匈牙利语 | hadmérnök＝军事工程师；紧邻 `Sapper`×N/`Utasz` 工兵段 | 军事工程师 |
| `Oszver` | 匈牙利语 | őszvér＝骡；紧邻 `Mule`×3/`Mulas` | 骡 |
| `Viuchny` | 俄语 | вьючный＝驮载的；紧邻 `Maulesel`×2 | 驮畜 |
| `Drushinizi` | 俄语 | дружинники＝义勇兵；紧邻 `Udarnye Voiska`/`Kommissar` 苏军段 | 义勇兵 |

### 10.3 ⚠️ 由此挖出的一处**上轮错译**（已修）

`Ta-haan` 我上轮译成「登陆」——**错**。泰语 ทหาร (thahǎn) = **士兵**。
已改 `Ta-haan`→士兵、`43 Ta-haan`→`43 士兵`；复查全文件「登陆」用法已清零（仅 `Landing Barge`→登陆驳船 正确）。

### 10.4 ⚠️ 更重要的连带发现：`donor保留` 档吞掉了一批**普通名词**

追查 `Ta-haan` 时排查「原文＝译文且含字母」的行，发现 **534 行**属此类，其中夹着**明显该译的词**——
它们既不在待办清单、也不是型号，而是被 `donor 恒等保留` 档（"某 donor 也这么留着"）**当成口径继承了**：

| 类 | 例 | 已修 |
|---|---|---|
| 地图/设施 | `Building` / `Tower` / `Hangar` / `Ocean Liner` / `MG Emplacement` | 建筑 / 塔楼 / 机库 / 远洋客轮 / 机枪阵地 |
| 编制/职名 | `Milice` / `Politi` / `Design Playtester` / `Pezikon` / `Rhodesian` / `Ustase` | 民兵 / 警察 / 设计测试员 / 步兵 / 罗得西亚 / 乌斯塔沙 |
| 车辆 | `Camion` / `Tung Vogn` / `Csapatszallito` / `Overvalwagen` / `Corvette` | 卡车 / 重型马车 / 运兵车 / 突击车 / 护卫舰 |
| **马匹词**（各国同段并列） | `Trekpaarden` / `Paarden` / `Pferde` / `Chevaux` / `Caballos` / `Konie` / `Konjska` / `Hevonen` / `Ippilaton` / `Herak` / `Bezny Herak` | 挽马 / 马 ×9 / 普通马 |

⇒ 本轮共 **39 行**修正（含 `Ta-haan` 2 处）。**这也再次印证 §9.3 第 3 条**：
`donor 恒等保留` 只能当"装备/结构型"的弱证据 —— 它同样会**把 donor 自己的漏译当口径继承**。
（已交付 efile 里 `Zware Paarden`→重马 而裸 `Paarden` 被留着，就是这种不一致的痕迹。）

### 10.5 剩余 32 条：2 条归「口径保留」+ 30 条仍待考

- **归口径保留**：`Mutuski`（日语**睦月**，罗马字缺 `s` —— 但邻域全是**日舰名**且整段保留原文 ⇒ 一并保留，不为它破例）、`Ratnakosindra`（泰舰名）。
- **仍待考 30 条**（明细与逐条理由见 `work\comww2\TODO-UNCERTAIN.md`）：
  日语 10（`Awai/Kabu/Soukou Bahitsu`、`Dowa`、`Hara Kamei`、`Keishu`、`Ko-Hi`、`Ko-on Pon`、`Shin Hoto`、`Shiro Rokoku`）·
  泰语 6（`Maak ho Mai`、`Mai`、`Paan Pon`、`Pak Naa-wik`、`Raat Jot-mat`、`Saai pan Mai`）·
  汉语拼音 8（`Bao Mai`、`Biao/Gao/Guang Chema`、`Jiaotache`、`Jijun`、`Kuaiban`、`Shi-Ke`）·
  其它 6（`Ossa`、`Ozzowiachimzen`、`Raba`、`T-Truppen`、`Tahun`、`Voro`）。

  其中 `Chema` 已确证为「**车马**」（chē+mǎ，且位于马车型段）⇒ `X Chema` **后缀已明、首字不明**（骠／高／广 皆可能），
  同 AG 批「拼音实为年号/帝名」那类 —— **但此处无原文可反查，不能瞎填**。

---

## 十一、追查「日式古国名／舰级名」假说：**证否**，并新增一条可机械化判据（2026-09-29）

用户问：`Keishu` / `Ko-on Pon` / `Dowa` / `Shin Hoto` / `Shiro Rokoku` / `Awai·Kabu·Soukou Bahitsu`
**是不是日本的古国名，或日本海军军舰的舰级名？**

### 11.1 结论：不是。且 `Mutuski` 是唯一落在舰名簇里的

1. 本文件的**舰级簇是独立的一簇**：L1931–1946
   `Kagero`·`Nagara`·**`Mutuski`**·`Yugumo`·`Akagi`·`Unryu`·`Zuiho`·`Taiyo`·`Shokaku`·**`Ise Class`**·`Furutaka`·`Tone`·`Mogami`·**`Nagato`**·`Kongo`·**`Fuso`**。
   ⇒ 用户假说的**前半成立**：古国名确实是 IJN 战列舰命名法（`Ise`=伊勢、`Nagato`=長門、`Fuso`=扶桑 皆为令制国名），
   但它们**只出现在这一簇**，且形如 `X Class` 或单名。
2. 六个目标里**只有 `Mutuski` 在该簇内**（L1933，紧邻 `Kagero`/`Nagara`）
   ⇒ 它是 **IJN 驱逐舰「睦月」**（罗马字缺 `s`）。驱逐舰用**月名**而非国名 ⇒ 属**舰名**，
   按「军舰舰名／舰级保留原文」口径**保留原文**（当前处理正确）。
3. 其余五条全在**陆上单位批**（L1676–1691，与 `Afghan`/`Moroccan`/`Egyptian`/`Brazilian EF` 国籍条目、
   以及 `Kouhei`(工兵)/`Sento Kouhei`(战斗工兵)/`Keisatsu`(警察)/`Kihei`(骑兵)/`Sukauto`(侦察) 交错），
   图标类别分别为 **日军步兵／指挥部步兵／装甲车／畜力车／马拉炮兵／坦克** ⇒ **不是舰级名**。

### 11.2 ⭐ 本轮新判据：**装备名的图标码反查**（唯一可完全机械化的判据）

`equip.txt` 行号 → `equip.xeqp`（4B 头 + 4054×120B，图标槽在相对 72/80/88/96）
→ **`OpenIcons.keep`（2,723 条 `假码;真码` 回落表）** → `OpenIcons.csv`（17,908 条，含 `Description`/`IconClass`）。

**关键**：本 efile 大量引用「假码」（`WDF77`/`H41P`/`SBC22`/`TD79`…），它们在 `OpenIcons.csv` 里**查不到**，
乍看像悬空引用；**先过 `OpenIcons.keep` 才能还原**。
⚠️ 图标是「最接近可用」而非精确对应 ⇒ 只能给**类别**，不能当词义。

**据此确证并译出 3 条**：

| 原文 | 图标证据 | 译 |
|---|---|---|
| `Shin Hoto` | `FZ150` = **Type 97-Kai Shinhoto Chi-Ha**（同文件另有 `T97 Chi-Ha` = `FZ149`）| **新炮塔**（用户猜的「新砲塔」正确）|
| `Hara Kamei` | `JK331` = Sanbo Honbu (HQ Command Infantry) ＋ **KAISER 自带对照表 L226 明写 `Hara Kamei: Field Command`** | **战地指挥部** |
| `Jiaotache` | `JKS93` = **Jiaotache (Bicycle x3)** / WW2 China Nationalist | **自行车** |

**其余 27 条只拿到类别**（畜力车 3 · 马拉机枪车 3 · 马拉炮兵 4 · 骑兵类 2 · 驮骡 1 · 步兵类 7 · 架桥工兵 1 · 摩托车 1 · 装甲车 1 · 牵引车 3）
⇒ 按「**类别 ≠ 词义**」登记不落笔（详见 `work\comww2\TODO-UNCERTAIN.md`）。

### 11.3 顺手确认的两条事实

- **`Osaka` 不是地名泛指**，而是 `WDG06` = **Type 92 HoKoKu-Go Osaka 装甲车**；
  `SNLF` → `WDG05` = **Type 93 Sumida**（上海海军特别陆战队确用过九三式装甲车 ⇒ 图标分配是有意为之）。
- 三条**假说**有旁证但未达落笔标准，已登记：`Ko-on Pon`≈泰语 กองพล(师) · `Shiro Rokoku`≈「白露国」＝白俄部队 · `Mai`≈ม้า(马)。

### 11.4 对后续 15 个 efile 的价值

`OpenIcons.csv`／`OpenIcons.keep` 是**游戏根级共享**、每个 efile 都有 `equip.xeqp`
⇒ 这套反查对**其余 15 个 efile 根级 `equip.txt`（4 万余行装备名）同样适用**，是装备名汉化的第一判据。
机制已写入 `MECHANICS.md` §23；工具已落地 **`work\comww2\probe_equip_icons.py`**
（`--lines A-B` / `--grep 串` / `--todo 文件`；COMWW2 实测 30/30 有解、0 悬空）。

### 11.5 COMWW2 根级当前读数（本轮后）

`equip.txt`：**1,239 行**已译/改写（本轮 +3，另 2 行 `Hara Kamei` 计为 1 个唯一串）· 汉字 4,006 · 待办唯一串 **304**。
四件套校验：逐行对齐 ✅ · 无 BOM ✅ · 无裸 LF ✅ · 原文侧 4 个 cp1252 字节未改 ✅。
⚠️ **订正一处过头断言**：本轮终检原写「无制表符 ✅」，实测 `strings_efile.txt` **含 3 个 TAB** ——
但**原文就有**（L33 `*_Deep Naval`＋3×TAB，属 `*` 注释行、引擎跳过），原文/中文侧 TAB 数相等（3=3）⇒ 非我方引入。
生成器只对**改动行**做制表符守卫，此处设计正确。

---

## 十二、COMWW2 `.xscn` 收官 + **两处历史误译的追查与修复**（2026-09-29 续）

> 用户要求「用 LLM 能力尽量信达雅翻译后续批次，并回顾前批次有没有误译」。
> 结果：**译完 98.0%**，同时挖出并修复了**两处已写入游戏文件的静默错译**。

### 12.1 起点与终值

| 指标 | 起点 | 终值 |
|---|---:|---:|
| `.xscn` 含汉字条目 | 15,147（84.0%） | **17,678（98.0%）** |
| 唯一非中文串 | 2,265 | **282** |
| 映射表条目 | 6,805 | **8,802** |
| 结构偏差 / 尾部残留 | 0 | **0 / 0** |
| 配对校验（17,267 条改动） | — | **0 错位** |

### 12.2 ⛔ 误译回顾之一：**跨 efile 词典被「待译清单」污染**

`measure_xscn_cov.py::load_maps()` 的 glob 含 `*/*xscn*.tsv`，命中了
`work\efile-nashornpbem\xscn-todo.tsv`（格式 `序号 \t 原文`），
于是 **`104 → Labinski  Jewish Quarter`** 被当成「已交付件实证译法」载入，
**优先级高于人工批次**，写入了 15 个场景文件。

⚠️ 危险点：`104`/`135` 在 `.xscn` 的**组 1（部队番号链）**里是**师级番号**，正确译法是 `第104`/`第135`；
错位映射把它换成**看起来完全正常的中文地名**，行数/编码/结构校验全过 ⇒ **只有语义体检能发现**。

**处置**：收窄 glob（只认 `*-xscn-map.tsv`）+ **内容守卫**（`dst 含汉字` 或恒等，否则拒收，实测拒收 510 条）
+ 从备份恢复文件 + 重建链路重 apply。
新增体检工具 `audit_map_quality.py` / `audit_pollution.py` / `verify_pollution_hits.py`。

### 12.3 ⛔ 误译回顾之二：**BASEKORP 把纯数字当罗马数字**（`100 → 连`）

追查中发现 BASEKORP 的 map 表有 **20 条**把纯数字段译成了「连」
（`100/25 → 连/第25`、`397/100 → 第397/连`、`100 → 连`），
根因是 **`C`(Company=连) 的正确译法与纯数字 `100` 被当成罗马数字 `C`** 混在一起。
全库体检确认**只有 BASEKORP 受影响**（26 处实例 / 17 个文件），并已按位置精确修复（复扫 0 处）。

⇒ 这与 `.xscn` 规则引擎那条「单字母 `L`/`C`/`D`/`M`/`X` 不是罗马数字」是**同一类错误的两面**。

### 12.4 「信达雅」怎么做：批次 6 的人工精译（2,065 条）

| 批次 | 条数 | 内容 | 做法 |
|---|---:|---|---|
| 6a1/6a2 | 248 | 高频专名（`Baltic Fleet`→波罗的海舰队、`Wintergewitter`→冬季风暴、`Sicherheit Batt.`→警戒营） | 逐条定译，先查标准译名库与既有交付件 |
| 6b1 | 203 | **通名可拆**（`X Airfield`→X机场、`Lake X`→X湖、`X River`→X河） | 顺序配对 + **通名一致性校验**（不通过即中止） |
| 6b2 | 243 | 多词（`Operation Baytown`→贝敦行动、`Through Hell's Gate`→穿越地狱之门、`Mamayev Kurban`→马马耶夫岗） | 逐条译，含战役标题/编成名/舰名 |
| 6b3 | 103 | 含数字（番号链 `PzJgAbt/106.ID`→反坦克营/第106步兵师、`Hill 274`→274高地） | 逐条译，口径照既有交付件 |
| 6b4/6b5/6b6 | 867 | 单词地名（俄/乌/匈/罗/芬/波/德/荷/立/爱沙尼亚） | 逐条音译，写「纯译文列表」再脚本配对 |

**舰名口径**（查库实证）：`HMS X` → `HMS X号`（库里主流），故 `HMS Eagle`→`HMS 鹰号`。

### 12.5 批次 7：规则引擎**末轮红利**（343 条）

残量里还有约 340 条是「数字 + 英文编制」型，只因**后缀词表不全**被跳过
（`6th Bomber Grp.`、`92nd Infantry Brig.`、`213th Sicherungs Div.`、`41st Royal Marine Comm.`…）。
⇒ 把后缀词表**分级**（整段 → 逐词 → 长度守卫）后一次性拿下 343 条：

| 原文 | 译 |
|---|---|
| `6th Bomber Grp.` | 第6轰炸机群 |
| `3rd Carpathian Div.` | 第3喀尔巴阡师 |
| `213th Sicherungs Div.` | 第213警卫师 |
| `41st Royal Marine Comm.` | 第41皇家海军陆战突击队 |
| `1. Kav.Reg./40. Kav.Div.` | 第1骑兵团/第40骑兵师 |
| `11ID` / `31CavD` | 第11步兵师 / 第31骑兵师 |
| `9th Batt./Royal Scots` | 第9营/皇家苏格兰团 |

### 12.6 三个新坑（已修）

1. **`strip()` 制造伪译文**：`I.R. 136/ 46. I.D.` → `I.R. 136/46. I.D.`（只去空格、无翻译），
   逃过 `d == s` 判定混入批次表 13 条 ⇒ 改为「至少一段真被改动」。
2. **方括号失守**：`54A]` 被译成「第54集团军」**丢掉 `]`** ⇒ 含 `[`/`]` 一律口径保留。
3. **单词后缀会被独译**：逐词翻译必须带长度守卫（`len>=4` 或多词），否则 `X/Div`→`第10/师`。

### 12.7 残留 282 条：**全部为口径保留**

方括号代号（`[55A]`/`[44A]`/`[51A]`/`[8A]`/`[4A]`/`[54A]`/`[38A]`，62 实例）·
未知大写缩写（`FC`/`NG`/`BC`/`FA`/`GM`/`RF`/`X`/`L`/`P`/`Z`/`CF`/`FF`/`TNG`/`DG`/`RSG`/`SWF`/`FNAF`/`SM/RM`/`RomAF`）·
未知编号缩写（`LLv.24`/`LLv.10`/`1Ft/4AF`/`2Ft/4AF`/`4GDNO`/`77STG/2AF`/`1CavD`/`1BL`/`9CavD`/`210SKG/2AF`/`13E/14P/4P`）·
标高标记（`H 125.6`/`H 238.8`/`H 240.3`）。

### 12.8 COMWW2 下一步

`.xscn` ✅（98.0%）⇒ 按 `docs\24` 转 **`.txt`（1,032 文件）**：先 `txt_workbench` 出 `rep-list` 分层，
再 prose + `label` 两层 → `.tmsg`(20) → `L8` 位图 → `.front`/`.xcam`(10)。
