# 52 · 把词库更新铺设到 PeG 及 PeG-WW2

> 用户指令（逐字）
> - `m02541`：「很好，把这些词库更新后的内容更新到Peg」
> - `m02542`（完整版，本次依据）：「很好，把这些词库更新后的内容更新到Peg及peg-ww2中」
>
> 承接：`docs\51`（残留专名定名 · 95 条候选 / 146 处落盘）。本次把定名后的词库内容**铺到两个工程的实际交付面**，
> 并顺手查清「除了 OLGWW2 还有谁带着这些残留」。

---

## 一、先摸清范围：全仓扫描

新建只读扫描器 **`work\_sync-audit\scan_residue_all.py`**：把 `naming.tsv` 的 93 个 `old` 串合成一条
alternation 正则，扫

- `D:\OpenPG2\EFILE_*`（根文件 · `SCENARIO\*.txt`（中文侧）· `TEXT-ZH\SCENARIO\*.txt` · `SCENARIO\*.xscn`）
- `D:\Program Files\PeG`（递归 `.txt`）
- 整个工作区（跳过 `backup` / `_ref` / `.git` / `__pycache__` / `.workbuddy` / 图形音声目录）

明细 → `work\_sync-audit\residue-all-hits.tsv`（5,296 行）。命中汇总（中文侧）：

| 工程 | 命中 | 说明 |
|---|---|---|
| `EFILE_OLGWW2` | 31 | 本次铺设对象（另有假汉字 4 处，见 §二） |
| `EFILE_PzLIGA` | 85 | 日舰名 6×7 ＋ `Balikpapan部队` 8 ＋ `[14 Army]` 12 ＋ `[Okinawa]` 10 ＋ `第2/第9驱逐舰` 12 … **真命中** |
| `EFILE_GCE` | 78 | 西班牙内战营名（`Amuategi No.35`/`S.Miguel`/`Zumalac.`/`Mehal-la` 5 …）**真命中** |
| `EFILE_KAISER` | 16 | `Auckland` 14 ＋ `Mehal-la` 2 |
| `EFILE_LXF` / `EFILE_ROI` / `EFILE_BASEKORP` / `EFILE_OPENAK` | 3 / 2 / 2 / 1 | `Flandes` · `FET` · `[V/XV Reservas]` |
| `D:\Program Files\PeG`（PeG 产品目录） | **0** | — |
| `peg\research`（PeG 研究表） | **0** | — |
| `EFILE_OPENPEG` | **0** | — |

**结论：PeG 侧（产品目录 ＋ PeG 研究表 ＋ OPENPEG efile）对这 95 条**一次都不命中**——
它们全是二战期术语，铺到 PeG 无对象可铺。真正还有对象的是**另外 7 个 efile**（详见 §六-2）。**

## 二、判据修正：从「连续 ≥2 汉字」到「含词库汉字」

执行器 **`work\_sync-audit\apply_naming_peg.py`**（默认 dry-run，`--apply` 落盘）首版把「中文侧」定义为
**文本里存在连续 ≥2 个汉字**，理由是 cp1252 重音字母被 GBK 误解出的汉字是孤立怪字
（`Caballería→Caballer韆`、`Bailén→Bail閚`），只有真中文才成串。

干跑立刻暴露漏判：**9 行**词库值里汉字被数字/字母隔开 ⇒ 凑不出连续两字被跳过，例如

```
ww2-scn-map.tsv:L3101  第3G/Imperiali师/第30军/第5军      (第|5|2|营 … 全被数字隔开)
ww2-scn-map.tsv:L8738  第52营/第1 African D
ww2-scn-map.tsv:L4780  第290团/Saharian Grouping
```

改成 **`ZH_SET` 判据**：`glossary\standard-glossary.tsv` 的 zh 列用到的**全部汉字**做成字集，
文本只要含其中**任意一个**就算中文侧。这样：

- `第52营/第1 African D` ✓ 命中（`第`/`营` 在词库字集里）
- `Caballer韆 FET` ✗ 不命中（`韆` 不在词库字集里）——**避免把中文塞进未翻译的西班牙文行**

命中而行内**没有**连续汉字的，明细里标 **`LOOSE-`** 供人工复核（本次 9 处，逐行核对后全部正确）。
修正后干跑：`tsv 行 24 · txt 行 4 · xscn 槽 10`，无新增假命中。

## 三、铺设落点与结果

`apply_naming_peg.py --apply` → 改动 **10 个文件**（备份 `backup\before-naming-peg\`，逐文件）：

| 落点 | 处数 | 例 |
|---|---|---|
| `pegww2\research\ww2-scn-map.tsv`（列 ≥1，en 列不动） | 24 行 | `Huebner/第Raemcke旅/[非洲军]→许布纳/第拉姆克旅/[非洲军]` · `第1营/Habforce/阿拉伯军团→第1营/哈巴尼亚部队/阿拉伯军团` · `第185炮兵团/第185Folgore师→…/第185“闪电”师` |
| `pegww2\research\_scn-fill-prose-r13-01.tsv` | — | 该表的 `雷姆克(Raemcke)旅` 属**双语注保护**，跳过未改（8 处） |
| `EFILE_OLGWW2` `SCENARIO` ＋ `TEXT-ZH\SCENARIO` 的 `.txt` | 4 行 | `18days0l.txt:5` `“friterie/frituur”→“薯条店”`（两层各 1）· `TEXT-ZH\equip.txt:2396/2397` `FET 骑兵/步兵→长枪党骑兵/步兵` |
| `EFILE_OLGWW2\SCENARIO\*.xscn`（字节级，同步 2 字节长度前缀） | 10 槽 | `18days11:g1#153 Forces Maritimes du Nord→北方海上部队` · `:g1#333 SS-Verfugungs-Division→党卫军特别机动师` · `DAKTU02/TU03/TU06 g1#45/46 第30军/第5军→第30军/第5集团军` · `GCN0:g1#10 [Col. Diaz Dunabeitia…]` · `GCN3:g1#7 [Col. Iglesias…]` |

⚠️ `TEXT-ZH\SCENARIO\*.xscn` 是**英文原文死镜像**（引擎只读 `SCENARIO\`，证据 `work\efile-nashornpbem\scan_xscn_latin.py:42`）⇒ 一律不动。
⚠️ 双语注保护：`译名(原文)` / `译名（原文）` 形态跳过（否则 `雷姆克(Raemcke)旅` 会变成 `雷姆克(拉姆克)旅`）。
⚠️ 多趟应用（≤5 趟）以覆盖连锁规则（如 `Mehal-la→梅哈利拉` 后还需 `塔博尔 梅哈利拉→梅哈利拉塔博尔`）。

## 四、词库重建与差异核对

`build_glossary.py` → `standard-glossary.tsv` **23,475 条**（较铺设前 **-1**）。
逐键对比铺设前快照 `backup\post-naming\glossary\standard-glossary.tsv`（脚本 `work\_sync-audit\cmp_gloss_postnaming.py`）：

- **-1 行已解释**：`You better resign and open a "friterie/frituur".` 原被 `split_pair` 按 `/` 拆成
  **两行**（`…"friterie` / `frituur".`，因为当时中文侧也含 `/`）；本次中文侧变成整句 `…“薯条店”。`（无 `/`），
  段数不等 ⇒ 不再拆 ⇒ 合并为 1 行。**属正确收敛**。
- 同键差异 **13 条**：5 条为本次铺设（Imperiali 两条键 ＋ `Caballería/Infantería FET`），
  8 条为上一轮定名的二轮空格收紧（`第76营 丹尼尔·塞卡德斯`→`第76营丹尼尔·塞卡德斯` 等）。
- 派生表：`glossary-conflicts 1889`（不变）· `glossary-residual 1380`（不变）· `glossary-skip 112`（不变）。

## 五、验收数据（全部实测）

| 项 | 值 |
|---|---|
| 层表 | `COMMON 37470` · `SERIES 183` · `SCOPE 10694`（原始记录 48516 ⇒ 去重 48347） |
| 漂移 | **218 → 196 条**（另有散文差异 72 条未计入术语表）——铺设让「词库值 vs 交付值」的分歧减少 22 条 |
| 槽位超限 | `scn20B`（20 bytes）**0 条** · `ui5`（5 汉字）73 条（既有） |
| 门 `layer_gate.py` | 偏离 555 条**全部已登记** · **⭐ 新增偏离 0 条 · 判定 ✅ 通过** |
| 权威核对 `audit_authority.py` | 问题 **212 → 211**（`A未译残留 66 → 65` · B12 · E134 持平） |

### 顺手修掉的两个 cat 回退（`work\glossary\cat_fix_rules.py`）
`Tabor Mehal-la` 在定名二轮把中文改成 `梅哈利拉塔博尔`（末字不再是部队词），
`Tabor Ifni` 同理（`伊夫尼塔博尔`）⇒ 两者 `cat` 掉回 `PLACE`。
新增 `UNIT_EN_EXACT = {"tabor mehal-la", "tabor ifni"}` 人工登记钉住为 `UNIT`；
`Tabor-hegy (450 m) → 塔博尔山`（匈牙利山丘）仍正确保持 `PLACE`。

## 六、遗留与待裁定

1. ⚠️ **词库内部 4 个不一致家族**（本次只做「按 词库 逐键对齐」，家族级分歧未动）：
   - `African D`：`第N非洲师` **12 键**（`1 African D`=第1非洲师 …）vs `第N南非师` **6 键**（本次定名产出）。
     史实＝South African Division ⇒ **南非师**才对。
   - `Saharian Grouping`：`撒哈拉战斗群` 1 键（本次）vs `撒哈拉集群` 4 键（`350 R/…`/`atB/…`/`Novara B/…`/裸键）。
   - `Imperiali D/XXX/V`：`第5集团军` 1 键（本次，向 .txt 已全译写法对齐）vs `第5军` 2 键。
   - `Raemcke`：`拉姆克旅`（.txt 层）vs `雷姆克旅`（.xscn 层，并有散文双语注 `雷姆克(Raemcke)旅`）。
2. **另外 7 个 efile 的真命中**（`PzLIGA 85` · `GCE 78` · `KAISER 16` · `LXF 3` · `ROI 2` · `BASEKORP 2` · `OPENAK 1`）
   是否也铺同一套定名，**待用户裁定**（本次只铺 OLGWW2 ＋ pegww2）。
3. 🔴 **新查出的系统性误译：`Bon.` → `第76营`**（西班牙文 Batallón 缩写）。实证：
   ```
   GCN2.xscn g1#34  EN='Bon. Thaelmann'      ZH='第76营 台尔曼'        ← 词库 txt 层正确写法是「台尔曼营」
   GCN2.xscn g1#42  EN='Bon. Caz. Asturias No.1' ZH='第76猎兵营 阿斯图里亚斯 第1号'  ← txt 层「阿斯图里亚斯猎兵第1营」
   GCN4.xscn g1#78  EN='Bon. G. Hernandez/-/[XIV]' ZH='第76营 G. 埃尔南德斯/-/[XIV]'  ← txt 层「G.埃尔南德斯营」
   GCN3.xscn g1#1   EN='Bon./[Col. Iglesias]'  ZH='第76营/[伊格莱西亚斯上校]'
   ——— 对照：英文**带数字**时反而正确 ———
   GCN4.xscn g1#57  EN='8 Bon./1 Bda./[1Agrp.]'  ZH='第8营/第1旅/[1Agrp.]'
   GCN4.xscn g1#79  EN='80 Bon./-/[XIV]'          ZH='第80营/-/[XIV]'
   ```
   即：`Bon.` **无数字**时被填进一个凭空的「76」，且词干常留拉丁文；实测 **GCN0/GCN2/GCN3/GCN4 共 25 槽**
   （词库里落成 20 个 `…/[地名]` 键）。**修法＝用词库 .txt 层的正确写法（`X营` ＋ 方括号地名）逐槽改写**；
   因涉及 20+ 个已交付槽位，**待用户裁定后执行**。
4. 既有遗留（未动）：62 条 `olgww2-pending.tsv` 纯英文舰名 · A 余 65 条构成 · 28 行同键多译 ·
   `glossary\README.md:166` 那句「`cat` 为启发式判定，个别番号会落在 `PLACE`」需改（实测 10.6%）。

## 七、复算命令

```powershell
$env:PYTHONIOENCODING='utf-8'
python work\_sync-audit\scan_residue_all.py                    # 全仓残留扫描（只读）
python work\_sync-audit\apply_naming_peg.py                    # 干跑
python work\_sync-audit\apply_naming_peg.py --apply            # 落盘（自动备份）
python work\glossary\build_glossary.py                         # 重建词库
python work\_sync-audit\cmp_gloss_postnaming.py                # 与铺设前快照逐键对比
python work\glossary\ingest_layers.py --apply                  # 重生层表
python work\glossary\layer_gate.py                             # 门（须 ✅ 新增偏离 0）
python work\glossary\audit_authority.py                        # 权威核对
python work\_sync-audit\probe_bon76.py                         # Bon./第76营 对位取证（只读）
```
