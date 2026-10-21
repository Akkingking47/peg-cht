# OpenGeneral 汉化阶段计划

- 日期：2026-10-16 ｜ 效力：**现行**
- 对象：`D:\OpenGeneral`（OpenGeneral 波兰发行版 · OpenGen.exe 25.02.26.0）
- 依据：`docs\70`（UI 层）· `docs\72`（exe 硬编码）· `docs\24`（efile 推进顺序方法论）
  · `docs\06`（efile 语言机制）· `MEMORY.md`（硬纪律 10 条）
- ⛔ **本计划不含任何自行启动游戏的动作**（`MEMORY.md` 硬纪律第 7 条）；实机验证一律由用户执行。

---

## 〇、起点

| 层 | 状态 |
|---|---|
| UI 界面（根级 `OPENGUI`） | ✅ **已完成并实机通过**（`docs\70`） |
| efile 级遮蔽的位图 | ✅ 已修（`EFILE_GUS_Zx\OPENGUI` 的 `mouse_build` / `mouse_missions` 同步为汉化版） |
| exe 硬编码 P0（退出确认框） | ✅ **已实机通过**（`docs\72` §六） |
| exe 硬编码 P1（13 条 / 17 槽位） | ⏳ **已落盘，待实机验证**（`docs\72` §十） |
| **内容层（5 个 efile）** | ❌ **0%，完全未动** |

---

## 一、总工程量（实测，非估算）

| 层 | ALBERICH | GUS_Zx | GUS_PeG | GUS | GUS_Wx | 合计 |
|---|---:|---:|---:|---:|---:|---:|
| 根级唯一行 | 9,062 | — | — | — | — | — |
| `.xscn` 文件 | 8 | 76 | 458 | 978 | 1,526 | **3,046** |
| `.xscn` 唯一串 | 320 | 1,818 | 6,526 | 27,367 | 39,654 | **75,685** |
| `.txt` 文件 | 9 | 118 | 1,846 | 2,463 | 5,269 | **9,704** |
| `.txt` 字符 | 10,499 | 63,052 | 590,213 | 1,146,106 | 1,787,553 | **3,597,423** |
| `.ply` 文件 | 0 | 1 | 0 | 31 | 0 | **32** |

> **GUS / GUS_Zx / GUS_PeG / GUS_Wx 的根级数据文件 MD5 全同**（`equip.txt` `1636C24B`、
> `names.txt` `04490CA6`、`nations.txt` `741AFAF9`、`fronts.txt` `AD8C3316`、
  `TerrainEx.txt` `A4BB8295`、`EQUIP.XEQP` `323971C1`），
> `strings_efile.txt` 更是 **5 个 efile 全同**（`FD0C9D57`）
> ⇒ **根级只需 2 套翻译**（GUS 家族一套 + ALBERICH 一套），**不是 5 套**。

**可复用度**（用 OpenPG2 的 `master-glossary` 124,270 条实测，**已按 `docs\76` 更正**）：
- `.xscn`：程序可覆盖 **39.4%** ⇒ 需人工/LLM **45,883 条唯一串**（155,608 槽位）
  ⚠️ 早期口径给的是 42.6% / 46,842 条（唯一串 81,629）——那是 `apply_master.py` 写死 cp1252
  解码 + `decode()` 先试 GBK 吞串造成的**虚高**，详见 `docs\76`。**排期用 39.4%。**
- `.txt`：整行复用率仅 **6.3%** ⇒ 需处理 **≈3,309,667 字符**（散文多为整段新译）

**体积对照**：本作 ≈ OpenPG2 全部 21 个 efile 的 **35%–50%**
（`.xscn` 槽位 50%、`.txt` 字符 38%、根级去重后 20%、SCENARIO 文件 68%）。

---

## 二、范围裁定

### ✅ 在范围内
- 5 个 efile 的根级 4 件（`equip.txt` / `names.txt` / `nations.txt` / `strings_efile.txt`）
- 5 个 efile 的 `SCENARIO\*.xscn`（尾部串区字节级回写）
- 5 个 efile 的 `SCENARIO\*.txt`（战前简报 / 胜败文本 / 战役简介）
- `SCENARIO\*.ply`
- 根级 `Tips1-4.txt`（见阶段 7）
- exe 硬编码 P2+（见阶段 7）

### ⛔ 明确排除（附判据）
| 项 | 排除理由 |
|---|---|
| `MAPNAMES\`（975 文件 / 4.36 MB / **18,571 个唯一地名**） | **`OpenGen.exe` 对该目录零引用**（`MAPNAMES`/`ALT_NAMES` 命中 0）；只有 `OpenSuite.exe` 读它（`%sMAPNAMES\%03d.txt`、`%sDATA\MAPNAMES.STR`）⇒ **编辑器专用数据，不进游戏画面** |
| `OpenSuite.exe` 编辑器界面 | exe 内 `Strings-` 命中 0 ⇒ **不读语言包**，无法汉化 |
| `MAP\`（2322 文件 / 1141.7 MB） | 纯地形图像 |
| `SMACK\`（38 个 .avi / 134 MB）· `SOUND\` · `SFX\` | 视频/音频资源；`.avi` 无字幕流 |
| `DOC\`（13 份 PDF / 25 MB） | 手册，独立文档工程，非游戏运行期 |
| `EQUIP.XEQP` / `*.xeqa` / `*.front` / `OpenIcons.dat` | 二进制数据 |
| `OpenIcons.csv` / `EquipIcons.csv` | 编辑器图标选择器用（与 `MAPNAMES` 同类） |

### ❓ 待盘点（阶段 7）
- **`MAPFILES\*.mapx`（1,242 个）** —— 未被本次量测覆盖。地图地名可能经它进入游戏画面
  （`.map` 由 `%sMAPFILES\%s.MAP` 读取，而地名很可能存在 `.mapx`）。

---

## 三、阶段划分

### 阶段 0 · 工具链改造与最小闭环（前置，**必须最先做**）
**问题**：既有脚本 `work\xscn\apply_master.py`、`work\xscn\measure_efile.py` 的
`ROOT = r"D:\OpenPG2"` 是**硬编码**的；且两者对 `--efile` 参数做 `a.strip().upper()` ——
`--efile GUS_Wx` 会变成 `EFILE_GUS_WX`，**匹配不到 `D:\OpenGeneral\EFILE_GUS_Wx`**（Windows 大小写不敏感，
但 Python 路径拼接后目录名必须真实存在）。直接跑会静默作用于错对象或报错。

**任务**：
1. 把 `ROOT` 参数化（`--root`，默认仍 `D:\OpenPG2` 保持向后兼容），或在工作区新建
   `work\xscn\apply_master_og.py` 薄封装。
2. 修 `--efile` 的 `upper()` 大小写问题（改成「在 `ROOT` 下做不区分大小写的目录名匹配」）。
3. 用 `EFILE_GUS_Zx` 的**单个** `.xscn` 跑通闭环：
   `apply_master → prematch-map.tsv / prematch-miss.tsv → 出稿 → xscn 回写 → 独立解析器复核`。
4. 确认跨作词库适用度：抽 200 条 `prematch-map.tsv`，人工核对 OpenGeneral 的
   二战东线/波兰题材专名译名是否与 OpenPG2 词库口径一致（不一致的进 `master-overrides.tsv`）。

**出口**：单个 `.xscn` 端到端跑通，`xscn` 解析器复核 0 异常。
**估工**：1–2 人·日。

---

### 阶段 1 · GUS 家族根级（**一套覆盖 4 个 efile**）
| 文件 | 行数 | 唯一 | 实测分类 | 备注 |
|---|---:|---:|---|---|
| `equip.txt` | 9,690 | 6,417 | 含数字 6,192（型号保留）+ `X Class` 140 + **纯字母待判 3,357** | 词库仅命中 **984 行（10.2%）**；口径见 `docs\75` |
| `names.txt` | 3,007 | 2,813 | 词库命中 1,209（40.2%）⇒ **1,798 待音译** | ⚠️ 头部疑似测试者昵称段需切分（`docs\75` §六 1） |
| `nations.txt` | 107 | 99 | **29 待译** | 国名，全译口径 |
| `strings_efile.txt` | 121 | 86 | **8 待译** | **5 个 efile 全同**，含 `[terrain]`/`[movement]`/`[classes]`/`[requisition]` |
| `fronts.txt` / `TerrainEx.txt` | — | — | 无玩家可见文本 | 纯配置（数字 + 英文注释），不译（`docs\32:287`） |

**交付**：在 **GUS / GUS_Zx / GUS_PeG / GUS_Wx 四个目录各建一份 `TEXT-ZH\`**（内容是同一套，复制过去）
—— **不动任何原文**（`docs\06`）。

**出口**：实机切到任一 GUS 家族 efile，装备浏览器/国家名显示中文。

**估工：6–10 人·日**（原估 3–5，已上修 —— 见 `docs\75` §五）。上修原因是原估把 `equip.txt` 当「由词库覆盖」，实测词库只命中 10.2%，且**「哪些译、哪些留」的分类本身就是工作量**。既有工程已有成文口径（型号/舰级/缩写保留，兵种/编制/通则译中文，著名装备用通行译名），**沿袭即可，不新立**（`docs\75` §一）。

**前置**：`docs\75` §六 的 5 项待查（昵称段切分 / `NamesEx.txt` 是否必需 / 含数字里该译量 / 分类器精度 / 变音符折写）先查完再开工。

---

### 阶段 2 · `EFILE_GUS_Zx` 全层收官（**首个完整 efile，试刀**）
- `.xscn` 76 个 / 2,968 槽位 / **1,818 唯一串**（程序覆盖 72.1%）
- `SCENARIO\*.txt` 118 个 / 63,052 字符
- `.ply` 1 个 / 32 字符
- 附带：该 efile `OPENGUI` 下的 `mouse_build` / `mouse_missions` **已改**；
  `hex_text.png` 经逐格分析确认是**纯图标**（洋红底 + 16×16 图标，无文字）⇒ 不需处理

**出口（本阶段是全计划的第一个质量门）**：三项校验全过 + **用户实机验收整个 efile**
（地图标签、单位面板、场景简报、胜败文本四处都看不到英文）。
**估工**：3–6 人·日。

---

### 阶段 3 · `EFILE_ALBERICH` 全层收官（独立 efile）
- 根级**独立一套**（`equip.txt` 9,436 行 / 唯一 6,194；`names.txt` 2,976 / 2,784）
- `.xscn` 8 个 / **320 唯一串**（程序覆盖 78.1%）
- `.txt` 9 个 / 10,499 字符 —— ⚠️ **含唯一一块真波兰语散文**
  （`LC.txt`：`>> ALB LC v.1.0.02 ---- CONDOR TRIFFT EIN EUROPA 1936 Niemcy. Po dwóch dekadach…`）
  ⇒ 需**从波兰语原文翻译**，不能走英译中管线；且是 cp1250，须防假汉字（`docs\23`）
- `.ply` 0

**估工**：3–5 人·日。

---

### 阶段 4 · `EFILE_GUS` 全层收官
- `.xscn` 978 个 / 61,975 槽位 / **27,367 唯一串**（程序覆盖 46.8%，需 LLM 14,548 条）
- ⚠️ 本 efile 原文是 **cp1250**（波兰语 `Pułk` / `Jastrząb` / `Jeńcy`），不是 cp1252 —— 见 `docs\76`
- `SCENARIO\*.txt` 2,463 个 / 1,146,106 字符（散文多为从波兰语转写的粗译英文）
- `.ply` 31 个 / 1,103 字符

**估工**：8–15 人·日。

---

### 阶段 5 · `EFILE_GUS_PeG` 全层收官
- `.xscn` 458 个 / 14,259 槽位 / **6,526 唯一串**（程序覆盖 **34.9%，本作最低**）
- `SCENARIO\*.txt` 1,846 个 / 590,213 字符
- `.ply` 0

**估工**：5–9 人·日。

---

### 阶段 6 · `EFILE_GUS_Wx` 全层收官（**最大，压轴**）
- `.xscn` 1,526 个 / 76,082 槽位 / **39,654 唯一串**（程序覆盖 **33.1%，本作最低**）
- `SCENARIO\*.txt` 5,269 个 / 1,787,553 字符
- `.ply` 0

**估工**：10–18 人·日。

---

### 阶段 7 · 收尾与补完
1. **`MAPFILES\*.mapx` 盘点**（1,242 个）—— 确认地图地名是否经它进画面，决定是否补做。
2. **根级 `Tips1-4.txt`** 汉化一次（23 KB / 131 行，`Tips1/2` 英文、`Tips3/4` 波兰语）
   ⇒ 5 个 efile 全部受益（`docs\70` §8.2）。
3. **exe 硬编码 P2**（含 printf 格式符，`docs\72` §10.5）：
   `%s * Mode: %d x %d x %d bpp (Click to show Credits)` · `   File: %s   [%d scenarios]` ·
   `Frozen/Mud ground condition supply: %+d%%` —— 逐字保留格式符并机检个数与种类一致。
4. **exe P3**：`push` 引用 = 0 的 4 条（`Toggles terrain labels` 等），先探承载方式。
5. **`.rsrc` UTF-16 对话框模板**：`Disable Campaigns Dialog at start` / `Hide windows' task bar` /
   `Change to` / `Tables` / `Files in folder` / `Check campaigns & DL missing maps` /
   `CREDITS` / `DISCLAIMER`
   （UTF-16 下中文与拉丁同为 2 B，槽位大概率够）。
6. **全库审计**：`work\audit\progress.py`（须带 `--dump-fake` 防 cp1252 假汉字）。

**估工**：3–6 人·日。

---

## 四、每阶段的固定作业流程

### 每批交付物（一批 = 一个 efile，一次做完）
| 层 | 交付方式 | 关键约束 |
|---|---|---|
| 根级 4 件 | `<efile>\TEXT-ZH\{equip,names,nations,strings_efile}.txt` | ✅ `TEXT-XX` 机制**生效**；**不动原文** |
| 场景散文 `.txt` | `TEXT-ZH\SCENARIO\*.txt`（**覆盖层，首选**） | ✅ 2026-11 修订：`docs\14:55-74` 逐站点反汇编证明 **文本类走 LangDir 优先**（`%sSCENARIO\%s.txt` @ `0x757011`，`mov edx,[0x11951B0]`=LangDir），失败才回退 efile 根。~~原写「引擎根本不查」是错的~~。阶段 2 实机（G2）与阶段 3 均按此落盘并通过 |
| 场景数据 `.xscn` | `SCENARIO\*.xscn` 尾部串区**字节级回写** | 只认 `<efile>\SCENARIO\` |
| 简报 `.ply` | `TEXT-ZH\SCENARIO\*.ply` | — |
| 位图 | `OPENGUI\hex_text.png` / `mouse_*.png` | 仅文字型；`EFILE_Clu` 的 `hex_text` 是象形图标须跳过 |

### ⚠️ 覆盖原文的三条铁律（`docs\06` 的 2026-09-20 事故教训）
1. **备份与覆盖必须拆成两条独立命令**。当时把两者写在同一条 PowerShell 里，
   命令含语法错误（`"$D:\OpenPG2\..."` 被当变量名）⇒ 整条被拒执行，
   **备份没跑但覆盖执行了**，导致 `EFILE_OLGWW2`(807 个) 与 `EFILE_OPENPG`(190 个) 原文丢失。
2. **先小范围验证，再批量**；批量前先 `-WhatIf`。
3. **覆盖后立即抽检**。

### 每批必做三项校验
1. 出稿 **GBK(936) / 无 BOM / 换行沿用原文**；中文侧行数与原文**逐行对齐**。
2. `.xscn` 用**独立解析器**复核（条目数 / 组表 / 长度自洽，异常 **0**）。
3. `.xscn` ↔ `.txt` **硬桥校验零新增**（`bridge_check.py`）。

### 每批完成后跑四连
```
build_dict && build_root_dict && build_prose_dict && build_master
```
词库是真源：**词典（已交付件实证）> 归一化 > 人工批次**（`MEMORY.md` 硬纪律第 10 条）。

### 中文侧硬约束
**GBK 装不下西文变音符**（`'Légion'.encode('gbk')` 直接抛异常）。带变音符的西文必须二选一：
- **折写 ASCII**（ä→a、é→e、ü→u、ö→o、ñ→n、ç→c），用于人名/型号
- **译成中文**（Fallschirmjäger→伞兵、Légion Etrangère→外籍军团）

`glossary-orig-charset-fix.tsv` 已备好 `ASCII折写` 列。

---

## 五、阶段门禁

| 门 | 判据 |
|---|---|
| G0（阶段 0 出口） | 单个 `.xscn` 闭环跑通；解析器复核 0 异常 |
| G1 | 切到 GUS 家族任一 efile，装备浏览器/国名显示中文（用户实机确认） |
| **G2（关键门）** | **阶段 2 的整个 `EFILE_GUS_Zx` 经用户实机验收**：地图标签、单位面板、场景简报、胜败文本**四处均无英文**。此门通过才允许铺后续大 efile |
| G3–G6 | 每个 efile 收官的统一判据：**`.xscn` 漏译 ≤0.5% 且 `.txt` >99% 且 `.ply` 全译**（`work\audit\progress.py` 实测，须带 `--dump-fake`） |
| G7 | 全库审计 + `MAPFILES` 归属裁定 |

> ⚠️ **进度判据必须直接读文件审计**。两种「假已改」不算数：
> ① 安装戳/官方自带；② 映射表 `src == dst` 恒等（`MEMORY.md` §二）。

---

## 六、风险与待确认

| # | 风险/待确认 | 处置 |
|---|---|---|
| 1 | **P1（13 条 exe 串）尚未实机验证**，其中 `干燥 - 结冰 - 泥泞 - 地形` 中文比 ASCII 宽，**移动力表头列对齐可能错位** | 阶段 0 之前先请用户验；错位则回滚并把 4 个槽位拆出单独处理 |
| 2 | `apply_master.py` 对 OpenGeneral 的程序覆盖率只有 **39.4%**（`MEMORY.md` 声称的「~93%」是**乐观口径**，已用 OpenPG2 自身 21 个 efile 做对照证伪） | 按 39.4% 排工，**不要按 93% 估** |
| 3 | 跨作词库口径：OpenPG2 的 `master-glossary` 是否适配 GUS 题材（二战东线/波兰） | 阶段 0 抽 200 条人工核对 |
| 4 | `EFILE_ALBERICH` 的 `.txt` 是真波兰语；`Tips3/4` 也是波兰语 | 走「波兰语→中文」而非「英译中」；cp1250 防假汉字 |
| 5 | `MAPFILES\*.mapx`（1,242 个）未盘点 | 阶段 7 盘点后再定 |
| 6 | 硬编码 `push=0` 的串与 `.rsrc` UTF-16 对话框 | 阶段 7 单独探承载方式 |
| 7 | 场景 `.txt` 覆盖原文**不可逆**（引擎不查 `TEXT-ZH\SCENARIO\`） | 严格执行 §四的三条铁律；备份进 `backup\` |
| 8 | `work\audit\progress.py` 是 **PG2 专属**（`GAME="D:\OpenPG2"` + PG2 形状判据），不能直接审计本作；本作缺独立进度审计器 | **阶段 2** 产出第一份成品后新建，其假汉字黑名单须从 cp1250/cp1252 原文侧重build，不得沿用 PG2 的 `backup\ORIGINAL-*`；见 `docs\76` §五.4 |
| 9 | `docs\23` 通篇假定「原文侧应为 cp1252」，未考虑 cp1250 | 该文档需加修订说明；A/B 类判据仍适用，只是「用哪种单字节表」要按 root 区分 |

---

## 七、估工汇总

| 阶段 | 内容 | 估工（人·日） |
|---|---|---:|
| 0 | 工具链改造 + 最小闭环 | 1–2 ✅ 已完成（`docs\74`） |
| 1 | GUS 家族根级（共享 4 efile） | **6–10**（原 3–5，见 `docs\75` §五） |
| 2 | `EFILE_GUS_Zx` 收官（试刀） | 3–6 |
| 3 | `EFILE_ALBERICH` 收官 | 3–5 |
| 4 | `EFILE_GUS` 收官 | 8–15 |
| 5 | `EFILE_GUS_PeG` 收官 | 5–9 |
| 6 | `EFILE_GUS_Wx` 收官 | 10–18 |
| 7 | 收尾与补完 | 3–6 |
| | **合计** | **39–71 人·日 ≈ 8–14 周** |

> 与 `docs\70`/`docs\72` 之前的评估口径一致（当时给 31–58 人·日）。
> 区间上端对应「散文全部人工精修」，下端对应「`apply_master` 词级组合 + MT 初稿 + 精修」。
> **阶段 4 与 6 合计占 ~50% 工作量** —— 排期上它们是唯一的关键路径。
>
> ⚠️ **尚未修订的部分**：阶段 3/4/6 的**根级**成本同样受 `docs\75` 口径影响（`equip.txt` 分类成本随行数线性增长），
> 但**不一次性调高全部** —— 各阶段量测后逐段修订。上表除阶段 0/1 外仍是 `docs\73` 原值。

---

## 八、建议的下一步（立刻可做）

1. **用户**：实机验证 P1 那 5 处（`docs\72` §10.4），特别是移动力表头对齐。
2. **我**：等 P1 结论的同时，先做**阶段 0**（工具链参数化 + `GUS_Zx` 单 `.xscn` 闭环）
   —— 这项工作与 P1 结论无关，不需要等。
