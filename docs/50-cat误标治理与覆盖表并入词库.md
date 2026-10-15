# 50 · `cat` 误标治理 与 per-file 覆盖表「并入」词库

- 日期：2026-10-15
- 触发：用户裁定（m01713，逐字）「**1，需要治理。2，并入。**」
  - ①＝`PLACE` 误标（部队番号/舰名被词库判成地名）需要治理
  - ②＝`_scn-file-overrides.tsv` 里「映射表另有中文」的 174 行要**并入**词库
- 范围：`glossary/`（主库 + 层表）与 `glossary/evidence/`；**未改任何游戏文件、未改任何映射表真源**

## 一、处理结论

| # | 事项 | 结论 | 实测 |
|---|---|---|---|
| ① | `PLACE` 误标治理 | ✅ 已落盘 | 主库 `PLACE` **7120 → 6216**（改判 **904** 条：→UNIT 698 · →EQUIP 206） |
| ② | 覆盖表并入 | ✅ 已落盘 | 按场景覆盖**收 109 → 271 键**；证据表 **202 → 28 行**；门 555 条偏离**全部已登记** |

## 二、① `PLACE` 误标治理

### 2.1 根因

`work/glossary/build_glossary.py` 的 `cat` 是**启发式判定**，不是数据：

- `cat_of_name(s)`（:83-91）：命中 `UNIT_HEAD/UNIT_TAIL/ALNUM_UNIT` 才算 `UNIT`，否则**默认 `PLACE`**
- `collect_xscn()`（:181+）：`cat = "PLACE" if ga == 0 else "UNIT"` —— 只按「是否 0 号组」二分
- `collect_txt()` 行号 0 判 `TITLE`，其余仍走 `cat_of_name`

`glossary/README.md:166` 早已登记一行「`cat` 为启发式判定，个别番号会落在 `PLACE`」——实测是 **752 条 / 7120（10.6%）**，且 746 条集中在 `EFILE_OLGWW2`。

判据只看**中文侧后缀**，所以战例：`HG div → 赫尔曼·戈林师`（`cat=PLACE`）、`Gen.Kdo. Gen. Hermann Geyer → 赫尔曼·盖尔将军司令部`（`PLACE`）、`Maxim Gorky II → 马克西姆·高尔基二号`（`PLACE`）。

### 2.2 规则（`work/glossary/cat_fix_rules.py`，两处共用）

`recat(en, zh) -> (cat, reason) | None`。**None ＝ 保持 `PLACE`**（宁可漏判，不可误伤地名）：

| 判据 | 结果 |
|---|---|
| 先 `unwrap()` 剥掉成对包裹的引号/括号（`''Macau''` / `"Dora"` / `（-）营`） | — |
| 中文落在**城市/地貌护栏**（`CITY_GUARD`：市·县·镇·村·区·省·岛·湾·港·河·湖·山·岭·要塞·城堡·教堂·广场·机场·铁路·公路·桥·运河·海峡·海域·平原·高地·阵地…）或**人名地名护栏**（`PERSON_PLACE`：列宁格勒·斯大林格勒·伏尔加格勒·加里宁格勒…） | 保持 |
| 中文以「**号**」收尾、不含数字、长度 ≥3（舰名：`努比亚号`·`马克西姆·高尔基一号`） | **EQUIP** |
| 英文含**海军前缀**（大写且后接大写舰名：`HMS`·`USS`·`IJN`·`KM`·`HMNZS`·`HMCS`·`HMAS`·`HMNoS`·`ORP`·`ARA`·`NRP`·`RMS`·`MN`·`RN`·`SM`） | **EQUIP** |
| 英文命中**具名装备白名单**（`Dora`·`Karl`·`Thor`·`Odin`·`Ziu`·`Loki`·`Maxim Gorky I/II`） | **EQUIP** |
| 中文命中**部队后缀**（营·连·排·班·中队·联队·大队·团·炮兵团·步兵团·骑兵团·旅·师·军·集团军·军团·支队·司令部·指挥部·集群·群·区队·舰队·航空队·卫队·兵团…）+ 任一佐证（中文含数字／英文含数字／英文编制缩写／兵种词／编制词／分支词） | **UNIT** |

### 2.3 实现

- `work/glossary/build_glossary.py`：① 顶部 `from cat_fix_rules import recat as _recat`；② `merge()` **末尾后处理**（只改 `cat` 列，不动 `(en, scope)` 主键、不动 `zh`）；③ 构建报告加「cat 纠正」段；④ 留痕 `work/out/glossary-cat-fix.tsv`
  - 放在后处理而不是 `cat_of_name()`：`merge()` 的分组键是 `(en, scope)`、`cat` 取自胜出记录 ⇒ 只改一列对下游零影响（`build_glossary.py` 全库仅 :165 / :167 两处调用）
- `work/glossary/regen_glossary_catfix.py`（**铁律三**：先重建到临时 → 比对 → 才写正式）：把 `build_glossary.OUTD` 指到 `work/glossary/_regen-catfix`，与现库逐行比

### 2.4 验收

```
临时 23476 行 · 现库 23476 行
仅临时有 0 · 仅现库有 0 · 内容不同 904（其中**只差 cat 列** 904）
cat 迁移:  PLACE→UNIT 698 · PLACE→EQUIP 206
```

落盘后：

| 文件 | 校验 |
|---|---|
| `glossary/standard-glossary.tsv` | md5 `37b6ed1cbe71…` → **`2da049315d0d…`**，与临时产物**逐字节一致** ✅ |
| `glossary-conflicts.tsv` / `-residual.tsv` / `-skip.tsv` / `-occ.tsv` | **全部未变** ✅ |
| `glossary/layers/common-glossary.tsv` | 902 行差异，**仅第 2 列 cat + 第 11 列 note**（note 是 `主库:<cat>` 的回声） |
| `glossary/layers/scope-glossary.tsv` | 2 行差异，仅 cat/note |
| `glossary/layers/common-drift.tsv` | 14 行差异，**仅 cat** |
| 其余 11 张层表 | 未变 ✅ |
| `python work/glossary/layer_gate.py` | **相对基线新增偏离 0 条 · 判定 ✅ 通过** |

库 `cat` 分布：`UNIT 7738 · PLACE 6216 · EQUIP 5063 · LEADER 2701 · TEXT 707 · TITLE 514 · TERM 398 · NATION 139`

### 2.5 两个正则缺陷（都靠抽样发现）

1. `NAVAL_EN` 早期写成不区分大小写的 `…|orp?|…` ⇒ 匹配到散文里的**裸词 `or`**，把 `Efile: OLGWW2 … or higher` 判成 `EQUIP`。修法：前缀必须**大写且后接大写开头舰名**（`(?:^|[\s(（])(HMS|USS|…)\s+[A-Z("“]`）。
2. 源文件里成对包裹的引号使 `zh.endswith("号")` 失效（`"马克西姆·高尔基一号"` 末尾是 `"`）⇒ 加 `unwrap()` 反复剥引号/括号。补上后提案 848 → **904**。

教训：**规则类改动的验收必须抽看命中样本**——只看计数看不出 `or` 这种误伤。

## 三、② per-file 覆盖表「并入」词库

### 3.1 原始设计（当时的排除）

`work/glossary/ingest_layers.py` 的 ②e-bis 块读 `pegww2/research/_scn-file-overrides.tsv`（per-file 行号级覆盖，优先级高于整串映射表）。当时有**两条排除**，命中的行只落证据表、不进层表：

1. `同键多译`：同一英文在不同文件取值不同（28 行 / 12 键）
2. `映射表另有中文`：映射表给的中文与覆盖表不同（**174 行**）

### 3.2 并入做法（用户裁定后）

- **取消「映射表另有中文」这条排除**。同一英文键在映射表（`scope=PEGWW2_SCN`）与 per-file 覆盖表（`scope=PEGWW2_SCN_OVR`）各有一个中文，是**两个优先级层的真实取值**；层表去重键是 `(en, 层, scope)`，**scope 不同即不冲突**，故可并存。
- ⚠️ **必须把两侧的中文都登记到 `override.tsv`**：首版只登记了覆盖表那侧，另一侧的映射表中文立刻变成未登记偏离 ⇒ 门报 `跨层多译 84 + 通用层内多译 74`。补 `ovf_keep_pairs.append((en, MAP_ZH[en]))`（并对登记行去重）后归零。
  - 这正是「**新增一层只在一个入口接线＝静默失效**」的又一次复现：排除规则、登记、写入是三处，必须同时改。

### 3.3 实测

```
按场景覆盖表：收 271 键入库 · 只落证据 28 行（同键多译 12 键/28 行） · 映射表另有中文**已并入** 174 行
原始记录 48517 ⇒ 去重后 48348
COMMON 37471 条 · SERIES 183 条 · SCOPE 10694 条
漂移 196 条（另有散文差异 72 条未计入术语表）
```

门：

```
偏离（同原文多译）共 555 条：已登记 555
⭐ 相对基线**新增**的偏离 0 条
判定：✅ 通过
```

### 3.4 残留：28 行「同键多译」

如 `Avalanche` 在 `SCENARIO/sedan-R_m.txt` 同文件内有 `色当：重制版` 与 `西线-06 色当：重制版` 两值；`Dessau` 在 `windsor-R_m.txt` = `西线-09 德绍`、在 `WINDSOR_m.txt` = `西线-10 德绍`。

层表主键 `(en, 层, scope)` **没有文件维度**，压平必然造假 ⇒ 这 28 行仍只落证据表 `glossary/evidence/ingest-scn-ovr.tsv`（现 28 数据行），文件头已注明。要真表达它们，只能走**按场景定点覆盖层**（`glossary/layers/scn-place-override.tsv`，键含 `场景词干`）——属未决项。

## 四、数据快照（前 → 后）

| 对象 | 前 | 后 |
|---|---|---|
| 主库 `PLACE` / `UNIT` / `EQUIP` | 7120 / 7040 / 4857 | **6216 / 7738 / 5063** |
| `glossary/layers/common-glossary.tsv` | 37395 行 | **37473 行** |
| `glossary/layers/scope-glossary.tsv` | 10612 行 | **10696 行** |
| `glossary/layers/common-drift.tsv` | 107 行 | **198 行** |
| `glossary/layers/override.tsv` | 121 行 | **445 行** |
| `glossary/evidence/ingest-scn-ovr.tsv` | 206 行（202 数据） | **29 行（28 数据）** |
| 门（偏离 / 新增） | 393 / 0 ✅ | **555 / 0 ✅** |

## 五、复算命令

```bash
# ① 只读提案（不写盘）
python work/_sync-audit/plan_place_cat_fix.py

# ① 临时重建 + 逐行比对（不写正式库）
python work/glossary/regen_glossary_catfix.py

# ① 正式重建（先备份 glossary/ 五个产出，见 backup/before-cat-fix/）
python work/glossary/build_glossary.py

# 层表是派生物：改真源后重跑
python work/glossary/ingest_layers.py            # 干跑
python work/glossary/ingest_layers.py --apply    # 落盘

# 门
python work/glossary/layer_gate.py

# 回归：阵营审计仍 0 处不符
python work/glossary/faction_place_audit.py
```

备份：`backup/before-cat-fix/glossary/`（5 个产出）· `backup/before-cat-fix/layers/`（14 张层表）。
留痕：`work/out/glossary-cat-fix.tsv`（904 条改判明细）。

## 六、遗留

1. **28 行「同键多译」**未进层表（§3.4），需按场景定点覆盖层表达或人工裁定。
2. `PLACE` 里仍残留**具名装备/元数据**类（如 `Efile: OLGWW2 v.2.0 or higher`、少数具名炮/舰）——无中文后缀线索，规则判不出，需白名单续补。
3. `glossary/README.md:166` 那句「个别番号会落在 `PLACE`」应更新为「已由 `cat_fix_rules.recat` 后处理治理」。
4. `common-drift.tsv` 因本次并入从 107 涨到 198 行，其中约 91 条是「同一键两个优先级层」的新条目 —— 应复核是否需要在报告里单独分节，避免与「跨项目漂移」混读。
5. 权威核对新增可见的 **11 条 `.xscn` 层标点问题**（§七）——本次只是让它们按正确的层受检，尚未修（如 `(-) Bat.` → `（-）营` 用了全角括号）。

## 七、下游消费方回归（`cat` 变更的影响面）

`PLACE` 是下游判据，改判后必须回归。全仓 `"PLACE"` 消费点：

| 消费点 | 用法 | 本次影响 |
| --- | --- | --- |
| `work/glossary/faction_wire.py:51-52` | `CAT_ALLOW_PLACE = {"PLACE"}` / `CAT_ALLOW_OPS = {"PLACE","TITLE","TERM"}` 准入 | **改善**：904 个番号/舰名/具名装备不再被当地名并入阵营对齐（正是 `Crusader` 那类假命中的根因）。门里该段**只报不判**，不影响判定 |
| `work/glossary/audit_authority.py:176` | **D 编制用语**：`cat not in ('UNIT','PLACE')` 时 `continue` | 改判为 `UNIT` 的行仍命中；改判为 `EQUIP` 的 206 行被排除。D 两轮实测均 **0 条** ⇒ 无实际影响 |
| `work/glossary/audit_authority.py:207` | **E 标点规范**：`lay = 'txt' if cat in ('PLACE','TEXT') else 'xscn'` | **规则换档**：改判行从 `.txt` 层判据切到 `.xscn` 层判据（净 +6 的全部来源） |
| `work/glossary/audit_authority.py:218` | **F 权威偏离**：过滤的是**基准条目**的 `cat`（`authority-baseline.tsv`），不是库行 | 与本次无关（F 两轮均 0 条） |
| `audit_authority.py` 的 **A 未译残留** | 不读 `cat`（按 `locked` ＋ 译文残留英文词判） | **与本次无关** —— 160 → 160 正是因此 |
| `work/glossary/ingest_layers.py:285` | `cat in ('PLACE','LEADER','NATION','UNIT','EQUIP','TITLE')` ⇒ COMMON 层 | 改判行两侧都命中 ⇒ 无影响 |
| `work/glossary/build_glossary.py` | `cat` 的产出方 | 本次治理点 |

### 权威核对的实测差异（探针 `work/_sync-audit/cmp_authority.py`）

同一份 `audit_authority.py`、同一份基准，只把库换成 `backup/before-cat-fix/glossary/standard-glossary.tsv` 重跑：

- 旧库 **问题 300**（A未译残留 160 · B内部不一致 10 · E标点规范 130）
- 新库 **问题 306**（A未译残留 160 · B内部不一致 12 · E标点规范 134）
- **A 未译残留 160 → 160，一条未增未减**

逐条看差异（按 `(kind, cat, en, zh)` 取集合）：新独有 11 · 旧独有 5。忽略 `cat` 列后仍是同样 11/5 —— 全部集中在 `E标点规范` 与 `B内部不一致`，即上面 :207/:218 的**规则换档**，而非译文变化：

- 新进入（原 `PLACE` → 现 `UNIT`/`EQUIP`，改按 `.xscn` 层判据）11 条：`(-) Bat.` · `(-)13 AR` · `(-)26 R` · `(-)72 R` · `(Estado Mayor) [XX]` · `(Estado Mayor) [XXII]` · `(Estado Mayor) [XVIII]` · `(Estado Mayor)[XIII]` · `(Reserve Rgt.)` · `Cossack 哥萨克` · `Cossack 哥萨克号`
- 退出（原 `PLACE`，现不再命中该层判据）5 条：`Canal Albert (I CA)` · `Forces Maritimes du Nord (ex 7 Armée)` · `Forces Maritimes du Nord (ex 7e Armée)` · `HMS Vivacious (V` · `SS-Verfügungs-Division (mot.)`

⇒ 结论：**cat 治理没有制造新问题、也没有掩盖旧问题**；净 +6 全部是「这些行终于按正确的层受检」的可见化。`authority-baseline.tsv` 的 284 条是**权威译名基准**（供 F 权威偏离比对的外部标准名），不是问题数基线，无需随本次更新。

## 八、「残留未译」三类拆解（`work/_sync-audit/explain_residual*.py`）

本工作区有**三份名字相近、含义完全不同**的残留表，混读会误判工作量：

### 8.1 `glossary/glossary-authority-review.tsv` → `A未译残留` **160 条**

含义：**词库单条条目**的中文译文里仍夹着英文（按 `locked` ＋ 译文残留英文词判，**不读 `cat`**）。
按 scope：`EFILE_OLGWW2 130 · EFILE_NASHORNPBEM 26 · EFILE_OPENPG 4`；按 cat：`UNIT 94 · TEXT 38 · EQUIP 16 · PLACE 7 · TITLE 3 · TERM 2`。
按成因分桶：

| 桶 | 数 | 例 | 性质 |
| --- | --- | --- | --- |
| ① `not used` 弃用条目 | 9 | `Deutschland BB (not used)` · `lePzSpWg (not used)` | 游戏内不出现 ⇒ 低优先，可保留 |
| ② 具名装备保留英文 | 7 | `SS Panther D → 党卫军 Panther D` · `Wirbelwind` · `Maultier` · `JagPanther` · `JagNimrod` · `Matilda` · `Churchill` | **真·未译**（应作 黑豹/旋风/骡式/猎豹/猎虎…） |
| ③ 番号/编制单位名 | 28 | `1 B/Habforce/Arab Legion → 第1营/Habforce/阿拉伯军团` · `51 R/1 African D` · `60 RA/[8 Army]` · `Forces Maritimes du Nord` | **真·未译**（番号里的部队名整段没翻） |
| ④ 署名·版本·URL 元数据 | 19 | `Campaign Creator: Santiago Fuertes` · `Jan Hedstrom, 12/2010` · `Map: Dunkerque (3)` · `License: CC BY-NC-ND` · `http://…` | **政策保留**（人名/网址/协议名）；但被误标 `PLACE`，本该是 `TEXT`/`TERM` |
| ⑤ 散文层里夹英文 | 30 | `Nashorn` · `Spitfire VB` · `Panther II` · `Ardense Jagers` · `Corps de Cavalerie` · `Groupement K` | 半政策：型号可留，部队专名应译 |
| ⑥ 其它（外语番号整段） | 67 | `16 ''Mejillones'' R/II Div.` · `2 R/2 Bde./[V Reservas]` · `290 R/Saharian Grouping` · `3 G/Imperiali D/XXX/V` | **真·未译**（西/法/意语番号） |

⇒ 真·未译约 **102 条**（②7＋③28＋⑥67）· 政策保留 **28 条**（①9＋④19）· 混合 **30 条**（⑤）。

### 8.2 `glossary/glossary-residual.tsv` **1380 行**（列 `en|should_be|cat|scope|src|loc|kind`）

含义不同：**逐处出现**的「该译未译」—— 词库**已有**标准译名（`should_be` 1380/1380 全非空），但某个**具体源行**仍是原文。
`kind`：`ABBR 978`（番号缩写，代码按「上下文相关」单列）· `PLAIN 402`。
`scope`：`EFILE_OLGWW2 1325 · EFILE_OPENPG 55`；`src`：`xscn 617 · txt 610 · equip 145 · names 8`。
例：`HMS Comfort → 皇家海军康福特号 @ SCENARIO/18days11.xscn:g1#100` · `Esc AB → 装甲车中队 @ SCENARIO/18days4.txt:12` · `Cie ac → 反坦克连`。
⚠️ **不等于 1380 处真漏译**：番号串（`I-II/19 RACC / CC`）是「按位置定点改写」的对象，词库条目与源行并非一一对应；`ABBR 978` 是代码自己标注的上下文相关类。

### 8.3 `pegww2/research/_未译清单.tsv` **408 行**（列 `子目录|文件|行号|英文原文|拟译`）

含义：**PeG-WW2 场景层**扫出的「该译未译」（已剔除说明书/占位/调试行/内部标识），是最贴近**本项目成品**的一份。

- 散文/简报整行英文：`7Pzrb7147_i.txt:3` · `B701_i.txt:5` · `BoB_BoB04_i.txt:28`（与 `docs\49` 的「`_m.txt`/`_i.txt` 载体」问题同族）
- 元数据行：`B7.txt:11 PeGWW2 conversion: Robert Mary, 08/2006`（3 个文件同款）
- 番号：`BoB18BV.txt:22 1RHA/1` · `BoB_BoB08_u.txt:2 A/I/327th GIR/101st`

按文件最多：`BoB_BoB17_u.txt 16` · `usvsussr7_m.txt 16` · `SL_SLD01_u.txt 13` · `SL_SLD08_u.txt 13` · `SL_SLS07_u.txt 13`

### 8.4 三者的关系

| 表 | 视角 | 量级 | 回答的问题 |
| --- | --- | --- | --- |
| 8.1 `glossary-authority-review.tsv` | **词库**条目级 | 160 | 库里的译名本身是否完整 |
| 8.2 `glossary-residual.tsv` | **前作**（OLGWW2/OPENPG）出现级 | 1380 | 库里的标准译名有没有用上 |
| 8.3 `_未译清单.tsv` | **本作**（PeG-WW2）源行级 | 408 | 成品场景是否该译未译 |

三者**不重叠计数、不可相加**；回答「还有多少没译」必须先说明是哪一层。
