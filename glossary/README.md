# 标准译名库（Glossary）

**唯一真源**：所有已定稿的译名都在这里。以后翻译新 efile、修订旧文件，**先查库、再落笔**，
不要再凭记忆或第三方表，避免再现「地图标签 vs 场景清单译名对不上」的问题。

## 目录内容

| 文件 | 说明 |
|---|---|
| `standard-glossary.tsv` | **主库**，23,476 条（UTF-8 BOM / CRLF，Excel 可直接双击打开） |
| `glossary-conflicts.tsv` | 同名多译冲突 1,882 条（`REAL` 972 条需人工裁定） |
| `glossary-residual.tsv` | 漏译清单：本库已有标准译名，某处仍用原文 |
| `glossary-skip.tsv` | 未纳入的源文件（双语行数不平行等 112 项） |
| `glossary-authority-review.tsv` | **权威核对**问题清单 648 条（六路审计，见下） |
| `glossary-encoding-fix.tsv` | 编码修复清单 15 条（装备名假汉字 → ASCII 等价，附自校验） |
| `glossary-orig-utf8-fix.tsv` | **A 类乱码** 314 行：原文侧混入 UTF-8 ⇒ `BarrÃ³n`，三列对照（乱码/真值/已有中文） |
| `glossary-orig-charset-fix.tsv` | **B 类乱码** 4,433 行：cp1252 被 GBK 读 ⇒ `L間ion`，三列对照 + 语种 + 生效侧 |

生成器与工具在 `../work/glossary/`。

## 主库字段

| 列 | 含义 |
|---|---|
| `en` | 原文（规范键） |
| `zh` | **标准译名**。若等于 `en`，表示按口径保留原文 |
| `cat` | 类别：`PLACE` `UNIT` `EQUIP` `LEADER` `NATION` `TITLE` `TERM` `TEXT` `BRACKET` |
| `scope` | 适用 efile：`EFILE_OLGWW2` / `EFILE_OPENPG` / `EFILE_NASHORNPBEM` / **`PEGWW2_UI`（界面·机制术语）** / **`PEGWW2_DOCS`（面向玩家文档）** / **`PEGWW2_EQP`（PeG-WW2 装备）** |
| `status` | `LOCKED`=有标准中文译名；`POLICY`=按口径保留原文 |
| `src` | 该原文出现在哪些层：`txt` `xscn` `equip` `names` `nations` `strings` `tips` |
| `conf` | 可信度：`HIGH` 唯一无争议 / `MID` 仅表述差异 / `LOW` 有实质冲突 / `ABBR` 番号缩写（同名不同部队，看语境）/ `POLICY` 保留原文 |
| `zh_in` | 哪些层**给出过**中文译名（校验时据此判断层是否适用） |

**查译名一律先看 `conf`**：`HIGH` 可直接用；`MID`/`LOW` 先去 `glossary-conflicts.tsv` 看冲突项。

## 三个关键设计（踩过坑才有的）

1. **分层（`src` / `zh_in`）** —— 同一原文在不同层合法处理不同。
   `Pz IVH` 在 `equip.txt`（装备表）按口径保留型号，在 `.xscn` 里译「四号坦克H型」。
   校验时只跟**同层**比，否则会产出成片误报（实测一次就误报 3,600 处）。
2. **政策层（`POLICY`）** —— 来自 `olgww2-glossary.tsv` 的 `KEEP` 登记（46 条舰名等）
   是**最高权威**，不参与投票。否则「HMNZ Achilles」会被别处的中文译名覆盖，
   反过来把正确的保留判成漏译。
3. **可信度分档** —— 番号类原文（`32 R/132 Ariete/[XX]`）同名在不同场景指不同部队，
   属**上下文相关**而非冲突，单独标 `ABBR`，不混进「必须统一」的清单。

4. ⭐ **按 scope 分列，绝不按 `en` 单键统一**（2026-10-12 补）—— 同一英文在不同项目/层
   **合法地**有不同译名，按单键比会产出成片**假冲突**：

   | 原文 | OLGWW2 | 本作（PeG-WW2） | 谁对 |
   |---|---|---|---|
   | `Air Transport` | 运输机（飞机） | 空运（动作；兵种名另作「空中运输」） | 都对，语境不同 |
   | `Ranger` | 游骑兵（美军） | 突击队（英军编制） | 都对，是两支部队 |
   | `Ferdinand` | 保留原文（POLICY） | 斐迪南（与 `Elefant` 象式 区分） | 都对，口径不同 |
   | `March` | 马奇（地名） | 三月（月份） | 都对，同形异义 |

   ⇒ 查译名**必须带 scope**；`glossary.py --check "X"` 会把各 scope 的结果**并列**给你，别只取第一条。

## 并入本作（PeG / PeG-WW2）术语

```bash
$PY ../work/glossary/make_pegww2_glossary.py --apply   # 由三处真源生成本作术语表
$PY build_glossary.py                                  # 重建主库（并入 PEGWW2_* 三个 scope）
```

- 输入：`work/glossary/pegww2-glossary.tsv`（276 条：界面术语 213 · 文档术语 42 · 装备后缀与订正 21）
- 真源：`peg/research/ui-glossary.tsv`（含逐条**依据**）· `pegww2/docs-zh/_翻译须知与术语.md` ·
  `work/glossary/make_pegww2_glossary.py` 内**手工登记**的后缀族/特性名/战斗记录组/装备名订正
- ⚠️ 重建**只增不动**：既有三个 scope 的行逐条不变（已实测 `EFILE_OLGWW2/OPENPG/NASHORNPBEM` 逐条一致）

## 工具用法

```bash
cd work/glossary
PY=C:/Python314/python.exe        # 系统 Python 3.14

# —— 查询 ——
$PY glossary.py 广州河                 # 模糊查原文
$PY glossary.py --check "Canton"       # 判合规：给标准译名 + 可信度
$PY glossary.py -r 广州                # 反查：这个中文对应哪些原文
$PY glossary.py -c PLACE -e EFILE_OLGWW2 -n 30
$PY glossary.py --stats                # 统计概览

# —— 校验（新 efile 汉化前后都能跑，只需中文侧文件）——
$PY check_glossary.py EFILE_OLGWW2                       # 默认查 txt/xscn 两层
$PY check_glossary.py EFILE_OPENPG --all                 # 含番号缩写类
$PY check_glossary.py EFILE_OPENPG --layers=equip,names  # 指定层
$PY check_glossary.py EFILE_OPENPG --out ../out/x.txt    # 明细落盘

# —— 重建（改了源文件或译名表后）——
$PY build_glossary.py                  # 全量重建主库与三份清单
$PY build_glossary.py --dry            # 只看统计不写文件

# —— 权威核对（对齐通行译名）——
$PY audit_authority.py                 # 六路审计 → ../glossary/glossary-authority-review.tsv
```

## 权威核对（对齐通行译名）

`../work/glossary/authority-baseline.tsv` 是**通行译名基准**（284 条：著名将领/地名/编制术语，
另含 `alt` 列登记可接受别名，如 `Leeb`＝李勃｜里布｜勒布）。`audit_authority.py` 据此六路核对：

| 维度 | 查什么 |
|---|---|
| A 未译残留 | 译文里还夹着该译的英文词（`(not used)` 等） |
| B 内部不一致 | 同一原文多个译名（并区分同 efile / 跨 efile） |
| C 编码乱码 | 原文列 mojibake、译文列假汉字 |
| D 编制用语 | 同一缩写有的译、有的留 |
| E 标点规范 | 层内括号越界、中文间多余空格 |
| F 权威偏离 | 与基准表通行译名不符 |

**两条硬知识**：
① **原文侧 `.xscn` 是 cp1252 单字节，中文侧才是 GBK** —— 一律按 GBK 读原文侧会把
   `Bièvre` 变成 `Bi鑦re`（已修，原文列乱码 227→1）。
② 假汉字 = **变音符单字节 + 后一字母**的 GBK 拼合（`ö`+`b`→`鯾`），
   还原时要带上被吞的字母：`鯾→ob`、`閑→ee`、`鰎→or`、`黶→us`、`雗→en`、`馻→na`、`黷→ut`、`鰊→on`。

## 原文侧编码：判两类乱码（docs23）

原文侧**应为 cp1252 单字节**，但少数条目被写成 **UTF-8** ⇒ 必须逐文件先判编码：

| 判据 | 结论 |
|---|---|
| `data.decode('gbk')` **失败** | **cp1252** ✅ 正常（`hi` 占比仅 0.002~0.014） |
| `decode('utf-8')` 成功，且结果里残留 `Ã`/`Â`/`Å` | 该行是 **UTF-8** ⇒ 引擎按单字节读会显示 `BarrÃ³n` **（A 类，真乱码）** |
| `decode('gbk')` 成功但解出汉字、且英文单词断裂 | 是**用 GBK 打开 cp1252 文件**产生的**假汉字**（B 类，游戏内其实正常） |

- **A 类**（280 行，已全部处理）：`BarrÃ³n`→`Barrón`、`LÃ©opard`→`Léopard`、`Hürtgen`、希腊文段。
  修法：建 `<efile>\TEXT-ZH\`（场景 `.txt` 走 LangDir 优先）。
- **B 类**（4,433 行，德语 1,573 为主）：`L間ion Etrang鑢e`→`Légion Etrangère`、`Panzerj鋑er`→`Panzerjäger`。
  **游戏内显示正常**（引擎按 latin-1 读）；只有汉化时用中文编辑器看文件才见假汉字。
  ⚠️ **待办口径 = 3,737 行**（TSV 的 `有效侧` 列 = `生效`）：
  其中 **696 行已被 `TEXT-ZH` 覆盖**（OLGWW2 693 + OPENPG 3）⇒ 玩家看到的是中文，**不算待办**。
  **推进按既有 efile 优先级分批，不从最集中的 KAISER 开刀** —— 见 `docs\24`。
- ⚠️ **中文侧（GBK）装不下西文变音符**：`'Légion'.encode('gbk')` 直接抛 `UnicodeEncodeError`
  ⇒ 写中文侧前**必须折写（`é`→`e`）或翻译**。

工具：`make_utf8_fix.py`（A 类清单）· `make_orig_charset_fix.py`（B 类清单）·
`scan_orig_charset.py`（全库普查）· `restore_orig_encoding.py`（逐行编码还原）· `make_scenario_zh.py`（场景中文侧）。

## 维护流程

1. **新增译名**：优先改**源文件**（`OpenPG2/<EFILE>/TEXT-ZH/` 或原文），然后 `build_glossary.py` 重建 —— 库永远由源文件派生，不手改。
2. **人工裁定冲突**：审 `glossary-conflicts.tsv` 的 `REAL` 条目 → 改源文件统一 → 重建。
3. **补政策保留**：把「按口径保留原文」的词加进
   `work/efile-nashornpbem/olgww2-glossary.tsv`（`KEEP` 行），重建后即成为政策层。
4. **新 efile 汉化**：先 `check_glossary.py` 扫出全部残留原文 → 查库定名 → 翻译 → 再跑一次确认归零。

## 数据来源

从**原始英文 ↔ 当前中文**两套**逐行平行**的文件派生（`backup/ORIGINAL-<EFILE>/` ↔ `OpenPG2/<EFILE>/TEXT-ZH/`）：

| 源 | 文件数 | 说明 |
|---|---|---|
| 场景清单 `.txt` | 886 行行平行 | 地名 + 部队名（规范本地化，最权威） |
| `.xscn` 组 0/1 | 242 结构一致 | 地图标签 + 番号串 |
| `equip.txt` | 5080+2142 行 | 装备名 |
| `names.txt` | 2263+775 行 | 将领/部队名 |
| `nations.txt` / `strings_efile.txt` / `tips1.txt` | — | 国名 / UI 类别 / 提示 |

## 已知限制

- **多义同名**：同一原文跨场景可能指不同部队（如 `KG` = 各战斗群）。库给**多数票**结果，`conf=LOW/ABBR` 时务必看语境。
- **112 个 `.txt` 未纳入**：双语行数不平行（`anvil_l.txt` 中文侧竟为空、`ge89i.txt` 8 行 vs 2 行）——**这些文件本身需要核查**，见 `glossary-skip.tsv`。
- **`.ply` 简报**不入库（自由文本，无平行英文）。
- `cat` 为启发式判定，个别番号会落在 `PLACE`，不影响 `en→zh` 主用途。

## 跨 efile 统一（B 类）—— 工具与规则栈

裁定工具 `work/glossary/make_b_decide.py` → `glossary/glossary-b-class-decide.tsv`；
执行 `work/glossary/unify_b.py [--apply]`。**当前 B 类 = 0 组（已归零）**。

**规则栈（先命中先赢）**：

```
1) 权威基准 authority-baseline.tsv（284 条，含 alt 别名；查表前剥 von/van/de la/de/…）
2) OLGWW2 .txt 规范名清单（10,747 token；docs19 认证，锁住已定论的标准名）
3) 平票取向 OPENPG（实测内部一致性 0.3% vs OLGWW2 3.0%）
4) 手工例外（`Tienraivaaja`→道路工兵 等，逐条写依据）
```

**三条纪律**：
- **投票源必须排除派生副本**：`EFILE_NASHORNPBEM` 的 TEXT-ZH 取自 OPENPG
  （names.txt 588 同名中 560 一致 = 95%）⇒ 只作对齐目标、不投票，否则 OPENPG 被重复计票。
- **分组键是 `(en, cat)`**，不是 `en` —— 同名跨类别的正确译法本就不同
  （`Cossack` 哥萨克[UNIT]/哥萨克号[PLACE]）。裁定与写盘脚本必须用同一个键。
- **写盘后必做四重复核**：`verify_b_unify.py`（重建 diff）· `verify_xscn_after.py`（`.xscn` 结构+逐条目）·
  重跑 `build_glossary.py`+`make_b_decide.py`（应归零）· `verify_xscn.py`/`bridge_check.py`（层间一致性零新增）。

还原：`work/glossary/restore_b_unify.py`（由备份名反推原路径）。备份 `backup/olgww2-b-unify2-before/`。
