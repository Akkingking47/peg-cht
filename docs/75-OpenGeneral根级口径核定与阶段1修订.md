# OpenGeneral 根级口径核定与阶段 1 修订

> 对象：`D:\OpenGeneral`（OpenGen 25.02.26.0，5 个 efile）
> 目的：阶段 1（GUS 家族根级汉化）开工前，把「`equip.txt` / `names.txt` 到底译什么、保留什么」的判据定死。
> 起因：`docs\73` §三 把 `equip.txt` 写成「需先定策略」，估工时**未计入分类成本**。本报告用既有工程的成文口径 + 8 个已汉化 efile 的实测校准，给出修订值。
> 结论：**口径不必新立，既有工程已有成文规则且已被 8 个 efile 验证；阶段 1 估工由 3–5 人·日上修为 6–10 人·日。**

---

## 一、口径汇编（全部来自既有工程成文文档）

### `equip.txt`（装备/单位名表）

| 类别 | 处置 | 来源 |
|---|---|---|
| 装备/武器**型号代码** | **保留原文** | `docs\00:215` · `docs\03:71` · `docs\04:67` · `docs\08:263` |
| 军舰**舰名与舰级** | **保留原文** | `docs\00:216` · `docs\03:73` · `docs\04:68`（316 处）· `docs\08:264` |
| **兵种 / 编制 / 后勤**名 | **译中文** | `docs\03:17` · `docs\04:15` · `docs\04:59` · `docs\30:139` |
| 常见军事**缩写** | **保留不译** | `docs\08:258`（`AT`/`BB`/`MG`/`HMG`/`FlaK`/`AD`/`ZOC`/`LOS`/`VH`/`AAR`）· `docs\27:92` |
| 有**通行译名**的著名装备 | **译中文**（谢尔曼、丘吉尔） | `docs\00:215` · `docs\32:72` |
| 型号 + **绰号** | 型号保留，**绰号意译** | `docs\38:455`（`A-10 Warthog`→`A-10 疣猪`、`F-22 Raptor`→`F-22 猛禽`） |
| 外语**普通名词**（芬/波/德/日） | **译中文** | `docs\03:153`（`Pioneeri`/`Ratsuvaki` 玩家看不懂） |

### `names.txt`（将领人名表）

| 类别 | 处置 | 来源 |
|---|---|---|
| **真人名**（将领） | **音译中文** | `docs\03:77` · `docs\25:57` · `docs\32:284` · `docs\33:104` |
| 历史名将 | **中文圈通行译名**（`Rommel`→隆美尔） | `docs\03:77` |
| 日韩人名 | **优先还原汉字**（`Yamamoto`→山本） | `docs\34:305` · `docs\38:459` |
| 中国朝代年号/帝名 | **用汉字本体，禁音译** | `docs\25:40,48` |
| 开发者**测试者昵称** | **保留原文**（OLGWW2/OPENPG 前 31 行） | `docs\25:38` · `docs\34:279` |
| `???` / `Ant #NNNN` / `#rrggbb` / `Classified` | **保留** | `docs\32:274` · `docs\33:104` |

> ⚠️ **口径演变记录**：`docs\03:159` 早期建议 names 走「A. 保留原文（避免音译不一致）」。该建议**已被推翻** —— 用户裁定「**层内不得中英混排**」（`docs\25:57`），此后 AG/AO/COMWW2 均**全音译**。

### `nations.txt` / `strings_efile.txt`

全译，无保留项（`docs\25`、`docs\32` 实测译率 100%）。

### 变音符专项

**GBK 装不下西文变音符**（`'Légion'.encode('gbk')` 抛异常）。二选一：人名/型号**折写 ASCII**（ä→a、é→e、ü→u、ö→o、ñ→n、ç→c，`glossary-orig-charset-fix.tsv` 已备 `ASCII折写` 列）；兵种/编制**译中文**。（`docs\24:102` · `docs\30:139`）

---

## 二、校准实测：8 个已汉化 efile 的真实保留率

以 PG2 的 `原文件` ↔ `TEXT-ZH\同名文件` **逐行对齐**统计（`x.rstrip()==y.rstrip()` 计为「保留原文」）。

### `equip.txt`

| efile | 总行 | 保留原文 | 有译文 | **译率** |
|---|---:|---:|---:|---:|
| `EFILE_OLGWW2` | 5,081 | 3,630 | 1,450 | 28.5% |
| `EFILE_OPENPG` | 2,143 | 1,811 | 331 | **15.5%** |
| `EFILE_COMWW2` | 4,055 | 2,815 | 1,239 | 30.6% |
| `EFILE_BASEKORP` | 7,999 | 6,959 | 1,040 | 13.0% |
| `EFILE_ATOMIC` | 11,998 | 10,985 | 1,013 | 8.4% |
| `EFILE_PzLIGA` | 4,639 | 2,760 | 1,879 | 40.5% |
| `EFILE_KAISER` ⚠️ | 5,286 | 2,338 | 2,948 | **55.8%** |
| `EFILE_GCE` ⚠️ | 5,000 | 282 | 4,718 | **94.4%** |

⇒ **主流（WW2 装备型 efile）译率 8.4%–40.5%，中位约 28%**。两个离群值成因明确：`KAISER` 是一战德军 mod，作者用**德语普通名词**命名；`GCE` 是**科幻 efile**（`docs\33:103` 记「科幻单位」列入译项）。

### `names.txt` / `nations.txt` / `strings_efile.txt`

| efile | `names.txt` 译率 | `nations.txt` | `strings_efile.txt` |
|---|---:|---:|---:|
| `EFILE_OLGWW2` | 98.6%（2,232/2,263） | 100% | 100% |
| `EFILE_OPENPG` | 96.0%（744/775） | 93.1% | 100% |
| `EFILE_KAISER` | 100%（2,697） | 100% | 100% |
| `EFILE_COMWW2` | 99.8%（990/992） | 100% | 100% |
| `EFILE_AG` ⚠️ | 55.7%（1,364/2,449） | 45.6% | 85.3% |
| `EFILE_ATOMIC` | — | 100% | 100% |

⇒ **`names.txt` 惯例是全译（96%–100%）**。`AG` 的 1,085 行保留是 `Classified` 占位（`docs\15:94` 口径：缺名保留，译了反而掩盖数据问题）。
⇒ `nations.txt` / `strings_efile.txt` **100% 全译**。

---

## 三、GUS / ALBERICH 根级分类实测

### `equip.txt`

按「含数字 → 型号保留」+「`X Class` → 舰级保留」+ 文档规则分类：

| 类别 | `EFILE_GUS` | 占 | `EFILE_ALBERICH` | 占 |
|---|---:|---:|---:|---:|
| **含数字 → 型号保留** | 6,192 | 63.9% | 约 5,970 | 63.3% |
| **纯字母 → 待判**（译 or 保留） | **3,357** | **34.6%** | 约 3,240 | 34.3% |
| `X Class` → 舰级保留 | 140 | 1.4% | 139 | 1.5% |
| 结构/空行 | 1 | 0.0% | 1 | 0.0% |
| **合计** | 9,690 | | 9,436 | |

- 词库（`master-glossary` ∪ `_root_dict` ∪ `master-resolve`）**已命中 984 行（10.2%）**。
- 「纯字母待判」样例（**必须译**）：`Strongpoint`（据点）、`Fortification`（要塞）、`Regular`（正规军）、`Jaeger`（猎兵）、`Truck`（卡车）、`Wagon`（马车）。
- 「纯字母待判」样例（**必须保留**）：`Richelieu`、`Suffren CA`、`La Galoisiere CL`、`Le Fantasque`、`Volvo`、`Brewster Buffalo`。
- ⚠️ **「含数字 → 保留」不是铁律**：`docs\00:215` 与 `docs\38:455` 要求**著名装备用通行译名、绰号意译**（`M4A4 Sherman`→`M4A4 谢尔曼`、`A-10 Warthog`→`A-10 疣猪`）。这些会在 6,192 条里被规则漏掉，需在分类批次里**按词库 `TEXT`/`EQUIP` 类反查补译**。

### `names.txt`

| efile | 总行 | 词库命中 | **待音译** | 样例（待音译） |
|---|---:|---:|---:|---|
| `EFILE_GUS` | 3,007 | 1,209 (40.2%) | **1,798** | `Gustlik` `Zsamot` `Greg` `Czata` `Kowdar` `Criss` `Majerek` `Depet` `Kris` `Marder` `Dolas` `Pelebudka` |
| `EFILE_ALBERICH` | 2,976 | 1,207 (40.6%) | **1,769** | 同上 |

⚠️ **GUS 的 `names.txt` 头部是波兰测试者昵称**（`Gustlik`/`Zsamot`/`Kowdar` 正是 GUS 系列作者群），与 `OLGWW2`/`OPENPG` 保留的前 31 行同源。**必须先定位昵称段结束行**，段的划分决定这 1,798 条里有多少是「保留」而非「音译」。—— 待查项，见 §六。

### `NamesEx.txt`（3,072 行）

`apply_master_root.py` 尚未纳入。词库命中 1,300 ⇒ **约 1,772 待音译**。是否为引擎必需文件**待核**（`docs\73` 未收）。

---

## 四、既有可复用资产（本次新发现）

`work\` 下已有**逐 efile 的决策对照表**（原文件 ↔ TEXT-ZH 的对齐产物），可直接当决策源复用：

| 资产 | 字节 | 内容 |
|---|---:|---|
| `work\ao\_equip-crossmap.json` | 50,310 | AO 的 equip 决策对 |
| `work\ao\_names-crossmap.json` | 70,797 | AO 的 names 决策对 |
| `work\atomic\_equip-crossmap.json` | 67,565 | ATOMIC 的 equip 决策对 |
| `work\atomic\_names-crossmap.json` | 81,530 | ATOMIC 的 names 决策对 |
| `work\atomic\_xscn-crossmap.json` | 609,881 | ATOMIC 的 .xscn 决策对 |
| `work\basekorp\_xscn-crossmap.json` | 905,652 | BASEKORP 的 .xscn 决策对 |
| `work\basekorp\_xscn-crossmap-conflicts.json` | 4,218 | 上者的冲突登记 |
| `work\_scratch\basekorp\build_crossmap.py` | 3,223 | 生成 crossmap 的脚本（可复用） |

⚠️ `docs\32:283` 记 AO 时的做法：交叉核对既有 4 efile 的 line-aligned 中英对建成 `_equip-crossmap.json`（**1,165 键，0 恒等映射**）。本次 GUS 分类应**先查这些 crossmap**，命中者直接沿用既有决策，不重复判断。

---

## 五、阶段 1 修订估工

| 子项 | `EFILE_GUS` 量 | 成本构成 | 人·日 |
|---|---|---|---:|
| `equip.txt` 分类 | 3,357 待判 + 6,192 需反查绰号 | 规则分类（脚本）+ 抽样复核 | 1.0–1.5 |
| `equip.txt` 翻译 | 词库已给 984；预计新增 900–1,800 | 型号/兵种口径 + 绰号意译 | 2.0–3.5 |
| `names.txt` 音译 | **1,798 待音译** | 若含昵称段则实量下降 | 2.0–3.5 |
| `nations.txt` | 107 行 / 29 待译 | 国名，快 | 0.2 |
| `strings_efile.txt` | 121 行 / 8 待译 | 快 | 0.1 |
| 四连 + 校验 + 回填 | — | `build_*` + `lint_zh` | 0.5–1.0 |
| **合计** | | | **6.0–10.0** |

**较 `docs\73` 的「3–5 人·日」上修一倍**，原因是原计划把 `equip.txt` 当「已由词库覆盖」，实测只有 10.2%，且**分类本身就是工作量**。

### 对全局的影响

`docs\73` §四 合计 **36–66 人·日**，其中阶段 1 由 3–5 变为 6–10 ⇒ **上修为 39–71 人·日 ≈ 8–14 周**。
其余阶段暂不修订 —— 但 ⚠️ **阶段 3/4/6 的根级也要按同一套口径与比例重算**（各 efile 的 `equip.txt` 分类成本随行数线性增长），实际值会在各阶段量测后逐段修订，**不一次性调高全部**。

---

## 六、待查项（不猜，登记）

| # | 项 | 影响 | 查法 |
|---|---|---|---|
| 1 | GUS `names.txt` 的**测试者昵称段结束行** | 1,798 条里「保留 vs 音译」的切分 | 与 `OLGWW2`/`OPENPG` 的 `names.txt` 前 31 行逐行比对 |
| 2 | `NamesEx.txt` 是否为引擎必需 | 决定 1,772 条是否入本阶段 | `OpenGen.exe` 串扫描（`namesEx.txt` 已在 exe 中出现过） |
| 3 | `equip.txt` 里 6,192 条「含数字」中**有多少该译**（著名装备/绰号） | 影响 equip 翻译量 ±500 条 | 用 `master-glossary.tsv` 的 `TEXT`/`EQUIP` 类反查 + 既有 crossmap |
| 4 | 纯字母待判 3,357 条的**自动分类精度** | 决定人工复核成本 | 用 8 个已汉化 efile 的 equip 决策做**留出验证**（规则精度目标 ≥95%） |
| 5 | `apply_master_root.py` 的**变音符处理**是否已内置折写 | GBK 编码会抛异常 | 读脚本 + 跑 GUS 的 `names.txt`（波兰变音符密集） |

---

## 七、下一批动作（按序）

1. **查 §六 待查项 1、2、5**（三条都是 10 分钟级的读文件 / 串扫描）。
2. **用 crossmap + 词库做「含数字」反查**，捞出该译的著名装备（§六 3）。
3. **做纯字母自动分类器并用 8 个已汉化 efile 留出验证**（§六 4）；精度 ≥95% 才放行自动分类，否则回退人工。
4. 分类与翻译结果落 `prematch-map.tsv` / `prematch-miss.tsv` 同款产物，走四连。
5. 阶段 1 完成后回填 `docs\73` 与进度表。

---

## 附：本报告证据方法

| 判据 | 方法 |
|---|---|
| 口径汇编 | `grep '型号\|保留原文\|不译\|音译' docs\*.md`（109 命中）+ 逐条读源文档行 |
| 保留率校准 | 逐行对齐 `原文件` ↔ `TEXT-ZH\同名文件`，`rstrip()` 后相等计「保留」 |
| GUS 分类 | `D:\DSH\_probe_equip_policy.py`（只读） |
| 词库命中 | `D:\DSH\_probe_root_classify.py`（只读，复用 `apply_master.py` 的键集合构造） |
| 保留率探针 | `D:\DSH\_probe_root_calib2.py`、`D:\DSH\_probe_keeprule.py`（只读） |
