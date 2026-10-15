# MEMORY.md · OpenPG 段归档全文（2026-10-10 压缩前）

> 2026-10-10 MEMORY.md 因超限压缩：OpenPG 段明细移入本文件，主文件只留索引。**勿删**。
> 另见 MECHANICS.md（机制）、MEMORY-archive-2026-10-10.md（逐 efile）、MEMORY-PeG-archive-2026-10-10.md（PeG）。

# 一、OpenPG（主线）

## 1.1 关键坐标

- 游戏 `D:\OpenPG2`；必读 `MECHANICS.md`（86KB）· `docs\08`（排查方法论）· `docs\30`（推进方案）· `docs\24`（排期）· `glossary\README.md`。
- 译名真源：`glossary\standard-glossary.tsv`（23,200 条，UTF-8 BOM）。
- ⭐ **统一总词库**：`work\xscn\master-glossary.tsv`（119,624 条整串，分 xscn/root/prose/glossary 四层）
  ＋ `master-words.tsv`（1,849 词级通名）。由 `build_{dict,root_dict,prose_dict}.py`（原文↔部署件**全量配对**）
  ＋ `build_master.py`（合并）产出；`apply_master.py` 做「程序优先匹配」——**新 efile 开工先跑它，
  master 覆盖 ~93%，只剩 ~6% 交 LLM**（PzLIGA 实测 94.4%）。
- ⭐ **冲突裁定**：`resolve_master.py` + `master-overrides.tsv`（21 条人工订正）→ `master-resolve.tsv`（1,436 条 src→权威译法），
  已接线 `build_master.py`/`apply_master.py`；重建后 master-glossary **0 多译法残留**。
- 每完成一个 efile 跑四连：`build_dict && build_root_dict && build_prose_dict && build_master`，成果自动沉淀回总库。
- 进度真源＝本文件 §1.2；投影＝`docs\00` §三（`work\audit\progress.py` 实测，可复算）。

## 1.2 进度（21 efile，已收官 **11**；交付单位＝一个 efile）

**已收官**：`AG` · `AO` · `ATOMIC` · `BASEKORP` · `COMWW2` · `GCE` · `KAISER` · `NASHORNPBEM` · `OLGWW2` · `OPENPG` · `PzLIGA`
（判据＝`.xscn` 漏译 ≤0.5% 且 `.txt` >99% 且 `.ply` 全译）。

| 层 | 状态 |
|---|---|
| L1 UI 主串 `OPENGUI\strings-zh.txt`（916 行） | ✅ 778 译 / 766 含汉字 |
| L2–L6 根级四件套 | ✅ **11 efile 全套**；欠账：ROI 仅 `names/nations`。⚠️ 文件名词形两种：多数是 `names.txt`，**`ATOMIC`/`LXF`/`SON` 是 `NamesEx.txt`** |
| 根级 `efile.txt`（机制 A，原文零改动） | 🟡 BASEKORP · COMWW2 · GCE · KAISER 已交付；余 ⬜ |
| ⭐ 装备名图标码反查 | ✅ `MECHANICS.md` §23；对余 14 个 efile 的 `equip.txt`（4 万余行）同样适用 |
| L7 exe 硬编码 | ✅ 地图HUD 49 + 面板 48 + `Main`→主国 |
| L8 位图文字 | ✅ `hex_text`×9（8 重绘，`Clu` 象形跳过）／`mouse_*`×7 |
| L9 `.xscn` | ✅ **11 efile**；余 10 待 |
| `.ply` 简报（全库 63 有正文） | ✅ 全译毕 |
| `.tmsg` / `.xsch`（原地改，无覆盖层） | ✅ AO / ATOMIC / BASEKORP / COMWW2 |
| ⭐ `USERSCEN\`（用户场景层） | ✅ COMWW2 · GCE · KAISER；余 **PzLIGA 150 `.xscn` ＋ 149 `.ply` ＋ 2 `.txt`** ⬜ |
| 场景 `.txt` 散文 | ✅ **10 efile 100%**（COMWW2 · GCE · KAISER 2203/2203 · PzLIGA 378/378） |
| 译名库 A 类 | ✅ 280 行 |

**逐 efile 明细（B5 COMWW2 / B6 GCE / B7 KAISER / B8 PzLIGA / B9 ATOMIC+COMWW2 收口）**
→ 已移至 `MEMORY-archive-2026-10-10.md`，要点：
- **COMWW2**：全库首个**全层收官** efile（含 298 个匈牙利地名 cp1252 残槽补译）。余 label 保留集 43→44 条英文编制名已清。
- **GCE**：西语内战题材；`.xscn` 88.3% 漏译 0；简报为「西语段＋英译段」**双段结构（全库仅 GCE）**⇒ 两段都译。
  ⚠️ 已知 `[CEM]`＝`Cuerpo de Ejército Marroquí`→「摩洛哥军」（**BASEKORP 带同一错误，未动，待批**）。
- **KAISER**：全库最大单批（588 `.xscn` / 2203 场景 `.txt` 含 57 个大写 `.TXT`）；`.xscn` 88.4% 漏译 0.42%。
  ⚠️ Git Bash 通配**区分大小写**。⚠️ **人名要译**（我曾误写「保留」）。
- **PzLIGA**：`.xscn` 98.6% 漏译 0；`apply_master` 覆盖 94.4% 验证通过。
  ⚠️ 生成器 TGT 必须与 `os.listdir` 目录名**逐字一致**（大小写）。
- **ATOMIC＋COMWW2 cp1252 残槽收口**：根因＝`ó/ö/á/é/ü/ä/ø/å` 被 `decode('gbk')` 解成**假汉字** ⇒ `apply`/`zhfix` 双跳，
  **只能走 `rawfix`**。落地 `atomic-xscn-rawfix.tsv`(402) / `comww2-xscn-rawfix.tsv`(302)。
  ⚠️ 旧记「ATOMIC 缺 `names.txt`」是**误记**（本名 `NamesEx.txt`）。

⚠️ **排期**：按 `docs\24` 优先级，**不被问题密度误导**；每批开工先**全 efile 量测**。
⚠️ **两种「假已改」不算进度**：① `EFILE_LXF` 426 安装戳、`BASEKORP` 8 官方自带；② 映射表 `src==dst` 恒等映射。⇒ **判进度必须直接读文件审计**。
⚠️ **cp1252 假汉字骗校验**：裸 `decode('gbk')` 把 cp1252 高字节解成假汉字。可靠判据＝GB2312 字节范围 ＋ 逐 efile 实证黑名单（`progress.py --dump-fake`）。

## 1.3 显示机制（目录矩阵见 `MECHANICS.md`）

1 `STRINGS-XX` 前缀（**按行索引**，22–41 地形名）→ `OPENGUI\strings-zh.txt`
1b `strings_efile.txt` 覆盖层（per-efile，覆盖 exe `[sides]`/`[classes]`）→ `<efile>\TEXT-ZH\`
2/3/4 `TEXT-XX\` ／ `TEXT-XX\SCENARIO\`（**仅 `.txt`/`.ply`**）／ `<efile>\SCENARIO\`（`.xscn`/`.tmsg`/`.xsch` **原地**）
5 PNG atlas `OPENGUI\hex_text.png` / `mouse_*.png`
6 `.xscn` 尾部字符串区（二进制回写）
7 `.ply` 简报正文 → `<efile>\TEXT-ZH\SCENARIO\`
8/9 `.tmsg`（首尾 `\r\n` 定位）／`.xsch`（24B 头＋记录：12B 参数＋104B 槽A＋u16 tail＋槽B）

**`.xscn` 串区**：`cnt==0` 是合法空组，不是结束信号。**判据只能是「解析位置 == 文件长度」**；组内可能有二进制项（占 `u16 len + L` 槽）：跳过登记但**仍推进 off**。

## 1.4 排查决策树（改了几处都没反应）

1. 全 exe 搜原文 ASCII → 看位置 2. 查 `strings-zh.txt` **行号** 3. 查 efile 目录（**先按目录矩阵确认走哪个目录**）
4. ★ **内存扫描**：命中 ⇒ 内存文本；**0 命中 ⇒ 不是文本，是图形！** 5. exe grep 图形名 → `OPENGUI\*.png`

## 1.5 关键地址

| FO | VA | 内容 |
|---|---|---|
| `0x5842A0` | `0x9858A0` | 内置 `[terrain]`（21×0x100）✅ |
| `0x5857A0` | `0x986DA0` | 内置 `[sides]` ❌ 英文 |
| `0x5859A0` | `0x986FA0` | 内置 `[classes]`（24）❌ 英文 |
| `0x511180` | `0x911F80` | 地图 HUD 串块 49 ✅（`docs\29`）|
| `0x5139BC` | `0x9147BC` | 单位面板/升级 48 ✅（`docs\28`）|
| `0x513A38` | `0x914838` | `Main`→**主国**（switch @`0x81A5E3`，OTP @`0x914804`）|
| `0x4B1A9A`/`0x4B1C86`/`0x4ECB39` | `0x8B2A9A`/`0x8B2A86`/`0x8ED939` | 三个合法空洞 |
| ⛔ `0x51CB31` | `0x91D931` | **废弃**：落在 PE `LoadConfig` ⇒ ntdll 崩 `0xC0000005` |

段布局：`.text` `0x401000`/`0x400` · `.rdata` `0x878000`/`0x477200` · `.data` `0x971000`/`0x56FA00` · `.rsrc` `0x12AB000`/`0x5BEC00`。
⚠️ **VA↔FO**：`.rdata` `VA=FO+0x400E00`、`.data` `VA=FO+0x401600`。明细 `work\exe\ledger.md`。

## 1.6 翻译口径

- 装备**型号保留原文**（M4A1、Bf-109G2）；著名装备用通行译名；**军舰舰名/舰级保留原文**。
- 各国原语言兵种/编制/后勤名译中文。**大写缩写保留**：`AT` `FlaK` `BB` `ZOC` `LOS` `LOF` `VH` `AAR` `BV` `U:%d` `pp`。
- **方括号/花括号标记**（`[XIII]` `[DAF]` `{Sab}`）视为符号保留。**括号别名**：有独立通行中文名≠主名 ⇒ 译；否则保留原语言；**严禁**译成与主名相同的重复串。
- **立场原则**：按扮演方视角用其代号与编制名。禁蔑称旧称。日期 `1941年5月14日`；知名将领用通行译名。
- **单位级别**：纯「数字+兵种缩写」位于父位＝**师级**（`N Pz`→第N装甲师）；后接 `R/Bde/Rgt/Bn`＝团/旅级。判据＝番号串顺序 `本单位/上级/再上级`。
- **`.txt` 按阵营用词**：日军 `第N师团`、国军 `国民党军第N师`、苏军 `第N师`；`.xscn` g1 一律 `第N师`（**待统一**）。
- **括号全/半角是分层约定**：场景 `.txt` 用**全角**；`equip.txt`/`.xscn` 用**半角**。
- **场景标题**：`Battle of/at/in X`→`X之战`；`YYYY Battle of X`→`YYYY年X之战`；`Operation X`→`X行动`；`X Tank Battle`→`X坦克战`；名词性 `Manchurian Operation`→`满洲战役`。
- ⚠️ **改专名前必须先查同一 efile 既有对译**（AG 的 `praetor` 既有译法「法官」）。

## 1.7 脚本（要点）

- ⭐ `work\audit\progress.py`：全库进度实测 → `docs\00` §三（`--dump-fake` 查黑名单）。
- ⭐ **cp1252 残槽四件套**：`list_residual.py` → `lookup_residual.py` → `union_residual.py` → `build_rawfix.py`；
  口径 `RESIDUAL-PLACE-POLICY.md`，订正 `residual-overrides.tsv`。
  ⚠️ `xscn.py export` **看不到**这类残槽（被假汉字骗过），必须用 `list_residual.py`。
- `find_slot.py --efile X --sub 串`（看某串在 `.xscn` 里的同组上下文）。
- ⭐ `work\xscn\xscn.py`：`--efile <EF> verify|export|apply --map F|zhfix --sub A B|rawfix`（后四者默认**干跑**，需 `--apply`）。
  ⚠️ `rawfix` 是修「保留原文」cp1252 残留的**唯一**入口。
- ⭐⭐ `work\xscn\build_dict.py`：跨 efile `.xscn` 词典（`backup/ORIGINAL-<EF>/SCENARIO/*.xscn` ↔ 交付件，按 (文件,gi,idx) 配对）→ `_xscn_dict.tsv` / `_xscn_conflicts.tsv`。
- ⭐ `work\comww2\probe_equip_icons.py <EFILE>`：装备名图标码反查（`--lines A-B`／`--grep 串`／`--todo 文件`）。§23。
- ⭐ `work\basekorp\gen_label_zh.py` → `work\comww2\gen_label_zh.py` / `gen_prose_zh.py`（**有任一未覆盖行即拒绝落盘**）。
- ⛔ 弃用：`audit_map_quality.py` · `audit_pollution.py` · `probe_residual_reuse.py`（B 档）· `audit_number_segments.py`（§25/§26）。
- `work\exe\`：补丁脚本（幂等）＋ `exe_zhfix.py`（已汉化串二次修正唯一入口）；台账 `ledger.md`+`holes.tsv`。
- 其他：`work\glossary\` · `work\efile-poc\` · `tools\*.ps1` · `work\build-zh.ps1 -Deploy`。

## 1.8 未解 / 待批

0. **旧账（OLGWW2/OPENPG，均未动）**：E 类标点 126 · `.xscn` g1 师团轴 292 段（**待批**）· 真漏译 1,380（`glossary-residual.tsv`）· 实质冲突 1,043 · 112 双语不平行 `.txt` · A 类 160 · ⚠️ **译名库 4,179 条恒等映射须单批清理**。
1. 实机核验 ✅ 已过（09-28）；清单 `docs\31`；回滚档 `backup\OpenGen.exe.before-*`。
2. OLGWW2 闪屏根因 ✅ 定位，已迁 `0x4B1A9A`，**待实机确认**。
3. B 类原文 4,433 行（真待办 3,737）：cp1252，游戏内正常、编辑器显假汉字。按 `docs\24` 推进，**不从 KAISER 开刀**。
4. `EFILE_ROI`：已建 `TEXT-ZH\{names,nations}.txt`+6 场景；`equip.txt`/`strings_efile.txt`/36 场景未汉化。
5. ⚠️ AG 待实机复核：单字母兵种缩写 A→辅助队/C→大队/S→射手/B→弩炮/R→骑兵/P→散兵/SP→斥候/AR→弓箭手/RC→骑兵。
6. `efile.xml` 名与描述：机制已定位（exe FO `0x4F6480` 附近，**先 `.txt` 后 `.xml`**）；`.xcam` 战役标题 186 个待批。
7. ⚠️ `progress.py` `.txt` 判据已加「`zh_score>=2` 且无残留拉丁字母」分支；`kept_style()` 不认 `'Xxx` 昵称前缀与 `U-\d+` 潜艇号。
8. OLGWW2 15 个场景仍用带空格日期（`dak*int` 等）需归一化。
9. 退出确认框改了但引擎没调用；P1–P4 UI 微调**已译未应用**（`work\exe\todo-p*.txt`）。
10. OLGWW2 法军航空编制译法待批：`Aé` 译「第N航空队」还是折写 `Ae`。
11. ✅ 面板「能力 XXX」＝特殊能力代号（行 835/836；836–877 是 41 项能力名）。
12. ⭐ **`USERSCEN\` 须单列排期**（PzLIGA 一家 19,564 条 `.xscn` 串 + 111K 字符简报）；工具 `work\userscen\userscen_tool.py`。
13. `readme.doc`（COMWW2，45KB OLE2 Word）＝战役说明，**玩家可见但非引擎渲染**，待批是否译。
14. ⚠️ **COMWW2 label 保留集 43 条英文编制名已清**（09-30，整行精确替换 15 文件/34 行；对照表 `label-keep-zh.tsv`）；剩余英文整行 69 行/28 种全是纯代号 ⇒ 口径保留。

## 1.9 硬纪律

1. **出稿 GBK(936)、无 BOM**；**换行沿用原文**。`UI_Lang` 必须 `strings-zh`（写 `zh` 静默回退英文）。
2. ⭐ **字体必须 `simhei.ttf`，禁用 `deng.ttf`**：DengXian 12px 拉丁字形溢出 advance ⇒ 重叠（`Main`→`Nlain`）。见 `docs\27`。
3. **绝不覆盖改原文**；**备份与覆盖分两条独立命令**；**先重建到临时 → 回读校验 → 才写正式**。
4. **含中文的脚本/数据文件必须显式确认 BOM**；`.ps1` 存 BOM 或纯 ASCII，数据文件一律**无 BOM**。
5. **需要截图时必须停下**，明确告知看哪一屏，由用户手动截取；**严禁自行启动/点击游戏**。
6. **优先级铁律**：词典（已交付件实证）> 归一化 > 人工批次（只填空缺，不得覆盖既有）。
