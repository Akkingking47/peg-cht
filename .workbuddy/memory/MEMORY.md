# 汉化工程 · 索引（多游戏工作区）

> 工作区 `D:\DSH\军事游戏汉化`。**本文件只放状态与指针**。
> 归档（**勿删**）：`MECHANICS.md`（机制 89KB）· `MEMORY-archive-2026-10-10.md` · `MEMORY-PeG-archive-2026-10-10.md` ·
> `MEMORY-OpenPG-archive-2026-10-10.md` · **`MEMORY-archive-2026-10-15.md`**（A＝PeG 明细 · B＝PeG-WW2 明细 · C＝高分辨率/宽屏线全文）。
> 2026-10-15 第四次压缩（原文件快照 `MEMORY.pre-compress-2026-10-15.md`，过渡备份）。

## 〇、游戏清单

| 代号 | 路径 | 引擎/界面 | 状态 |
|---|---|---|---|
| **OpenPG** | `D:\OpenPG2` | OpenGen 26.3.30.0；SDL2+SDL2_ttf | 主线，21 efile 收官 **11** |
| **PeG** | `D:\Program Files\PeG` | SSI *modgen* 1998；DirectDraw+GDI ANSI | UI+5 文本+场景主体已汉化；宽屏线进行中（§五） |
| **PeG-WW2** | `D:\Program Files\PeG-WW2` | 同引擎（**与 PeG030 同构建**）；PeG 二战 MOD | exe+界面+场景三层已部署（待实机复测） |
| **PG Forever** | 见 `PGFOREVER.md` | HTMLayout 界面 | UI 层完成，见 `docs\05` |

## 一、PeG · 状态（明细 → `MEMORY-archive-2026-10-15.md` §A · `peg\README.md` · `peg\方法\`）

**✅ 已达可用状态**：中文显示 ｜ 5 文本文件 ｜ 场景 825 `.txt` + 14 `.ply` ｜ 列表分组编号 ｜ 简报/描述框 ｜ 日期汉化 ｜ UI 术语+装备名。
**部署形态**：`PeG030.exe`（MBCS+日期补丁）＋ 825 `.txt` ＋ 14 `.ply`。**备份链勿删**：`PeG030.exe.orig-backup` → `testbed\*.pre-*` ｜ `backup-scn-flag\` ｜ `backup-ui-src\`。
- **exe 补丁**：`patch-mbcs.py`（iCharSet/`_pctype`/`__mbcodepage` 三处＝中文显示治本）＋ `patch-date-lcid-zh.py`（`0x7BE86` LCID→0x0804＝日期汉化真正生效的一刀）；`patch-lc-time-zh.py` 实测无效仅留档。⚠️ 改 exe 前先查导入表（`GetDateFormatA` ⇒ Windows 在格式化，改数据无用）。
- **场景界面定论**：场景名＝`_m.txt` 第 [`.SCN`@4] 行；进列表＝`@0==0`；「进行场景」只显 ≤2 人＝`@216(P3)==0`；描述框＝`.ply`（第 0 行必须是标题）；开局简报＝`@11329`(stem)+`@11349`(位置标志 0/1) **双字段必须同时核对**；列表按字节序排序 ⇒ `NN ` 前缀钉序。
- **UI 术语定案**：`Air Mission` 按词性分「空中任务/出击」（BANNED 整串黑名单＋5 面板名锁定）；`Air Defense` 分「对空防御/防空」；`Air Transport` 分「空运/空中运输」；北约代号意译。术语表 `peg\research\ui-glossary.tsv`。
- **文风总纲**：叙事简报体为默认（非命令体）；原文限制军事化程度；意象成链；禁台湾 1990s「民国感」词。全文 `peg\research\各国军语风格口径.md`。
- 官方繁中版《解放軍之怒》考古 → `peg\research\官方繁中版《解放軍之怒》译法考.md`。
- 工具链：`gen_scn_zh.py`（三态拆行/整文件排除/分组序号）｜`gen_ply_zh.py`｜`gen_gui030_zh.py`｜`gen_peg_text.py`。⚠️ build 必须从 `testbed\backup\` 读原文。译法（`*-map.tsv`）/逻辑（`gen_*.py`）分离。

## 一之二、PeG-WW2 · 状态（明细 → `MEMORY-archive-2026-10-15.md` §B · `pegww2\README.md` · `docs\40–52`）

**三层已部署**（2026-10-11）：12 efile 全补丁（各 261B）＋ 5 界面文本全量 ＋ 场景层 21,865 唯一行全译（3,777 文件/47,049 行/五道校验 0 失败）；复算核验三方 sha 全绿。
⭐ **最大发现**：12 efile 与 PeG030 同一构建（TimeDateStamp 903998521）⇒ 双字节补丁 1:1 套用。
- **待办**：① 用户实机复测 ② `方法\` 经验总结（空目录）③ 可复用经验上浮到技能。
- **19 条踩坑（W1–W19）**：全文 `pegww2\README.md` §踩坑档案。最值钱：W17 整串键控不能用于同串多义（须 per-file 覆盖）；W19 描述框双字段；W11 HUD 是元件拼装。
- **地名三维规则**（阵营/年代）：真源 `glossary\layers\faction-places.tsv`；审计器 `faction_place_audit.py`（视角判定 90%，年代仅 21%＝瓶颈，需逆向 `.scn` 日期字段）。
- **地名收敛＋两作同步**（docs\47/48）：12 组新名已落盘重生成部署（PeG 57/WW2 22，回读 md5 一致）；⭐ 改真源必须重跑层表链（`ingest_layers → converge_plan → layer_gate`）；⭐ 按英文键整行替换，禁全局文本替换。
- **按场景定点覆盖层＋第三真源入库**（docs\49/50）：`scn-place-override.tsv` 空表回归 0 变化；`_scn-file-overrides.tsv` 已并入词库（收 271 键，门 555 偏离全登记 ✅）；⚠️ 生成器应记录每行命中来源，防「成品对而真源错」倒挂。
- **cat 误标治理**：`work\glossary\cat_fix_rules.py` 挂 `build_glossary.py` merge 末尾（PLACE 7120→6216）。⚠️ 规则改动必须抽看命中样本。
- **残留专名定名**（docs\51/52）：95 条 146 处已落盘；遗留待裁定 4 项家族分歧（African D `南非师`/`非洲师` 等）；🔴 **系统性误译 `Bon.→第76营`**（25 槽）待用户裁定修法。
- ⚠️ 环境**真源**：`env.cmd` ＋ `requirements.txt`（工作区根目录）｜解释器 `C:\Python314\python.exe`＝Python 3.14.7（旧 venv 失效）；跑脚本前 `call env.cmd`（或设 `PYTHONIOENCODING=utf-8; PYTHONUTF8=1`）；PowerShell 别包管道。

## 二、OpenPG（主线）· 状态（明细 `MEMORY-OpenPG-archive-2026-10-10.md`）

- 必读：`MECHANICS.md` · `docs\08`（排查方法论）· `docs\30`（推进）· `docs\24`（排期）· `glossary\README.md`。
- 译名真源 `glossary\standard-glossary.tsv`（23,200）；⭐ 统一总词库 `work\xscn\master-glossary.tsv`（119,624，四层）＋ `master-words.tsv`(1,849)。**新 efile 先跑 `apply_master.py`**（覆盖 ~93%，余交 LLM）；冲突裁定 `resolve_master.py`+`master-overrides.tsv`。每完成一个 efile 跑四连：`build_dict && build_root_dict && build_prose_dict && build_master`。
- **进度**：21 efile 收官 **11**：`AG·AO·ATOMIC·BASEKORP·COMWW2·GCE·KAISER·NASHORNPBEM·OLGWW2·OPENPG·PzLIGA`（判据＝`.xscn` 漏译 ≤0.5% 且 `.txt` >99% 且 `.ply` 全译）。投影 `docs\00` §三（`work\audit\progress.py` 实测）。
- ⚠️ **判进度必须直接读文件审计**：两种「假已改」不算——①安装戳/官方自带 ②映射表 `src==dst` 恒等映射。
- ⚠️ **cp1252 假汉字骗校验**：裸 `decode('gbk')` 把高字节解成假汉字；可靠判据＝GB2312 字节范围 ＋ 逐 efile 黑名单（`progress.py --dump-fake`）。
- ⛔ 弃用脚本：`audit_map_quality.py`·`audit_pollution.py`·`audit_number_segments.py`。

## 三、硬纪律（跨作通用）

1. **绝不覆盖改原文**；备份与覆盖分两条命令；**先重建到临时 → 回读校验 → 才写正式**。
2. 出稿 **GBK(936)、无 BOM**（OpenPG 词库 TSV 例外用 UTF-8 BOM）；换行沿用原文；拆行须 `(\r\n|\r|\n)` 三态（老引擎可能裸 CR）。
3. **不改 exe 前先查导入表**（`GetDateFormatA`/`GetLocaleInfoA` ⇒ 文本来自 Windows，改 exe 数据无用）。
4. **补丁三纪律**：幂等 · 默认 dry-run（`--apply` 才写）· 等长替换优先。
5. **不全量翻译脚本/说明类文件**——建整文件排除清单。
6. **不靠肉眼不靠猜**——编码、字体、格宽、行数，全部实测或脚本复算。
7. 需要截图时**停下告知，由用户手动截取**；**严禁自行启动/点击游戏**。
8. **结论被推翻时写明撤回原因**；未实测的结论标 `[推定]`。
9. OpenPG 字体必须 `simhei.ttf`（禁 `deng.ttf`）；`UI_Lang` 必须 `strings-zh`。
10. 优先级铁律：**词典（已交付件实证）> 归一化 > 人工批次**（只填空缺，不覆盖既有）。

## 四、跨作经验 → 技能

`~/.workbuddy/skills/` —— ⭐ **「一作一技能 ＋ 一方法论 ＋ 一手法库」**（2026-10-10 第 36 轮定型）：

| 层 | 技能 | 覆盖 |
|---|---|---|
| 方法论 | `military-game-docs-translation`（13KB/7refs） | 跨引擎（双轨制/文风/单字节引擎范式/归档规范/开工单） |
| 项目 | `opengen-sdl2-efile-localization`（24KB） | OpenPG（SDL2 + efile 目录制） |
| 项目 | `ssi-modgen-peg-localization`（14KB） | PeG（SSI modgen · DirectDraw+GDI ANSI） |
| 项目 | `pgforever-htmlayout-localization`（16KB） | PG Forever（HTMLayout） |
| 手法库 | `win-game-html-ui-localization`（8KB/9refs） | 跨项目二进制/界面通用手法（按汉化阶段分册） |
| 其他 | `sd25-pe` | Seedance 提示词（**第三方技能**，自升级可能覆盖拆分，审计 `work/_audit_skills.py`） |

⚠️ **分层判据（唯一）**：「换一款游戏/引擎，这条还成立吗？」成立 ⇒ 方法论 ｜ 同引擎成立 ⇒ 项目技能 ｜ 只对本作成立 ⇒ 项目档案。
⚠️ **收尾必做「可复用清单」盘点**：换引擎仍成立的手法**必须上浮到技能**（PeG 19/19 已上浮；**PeG-WW2 未做**）。
⚠️ 拆分手法：脚本按行范围切分（`work/_split_skills.py`），不做重写；原文件备份 `peg\testbed\skills-backup\`。

## 五、PeG 高分辨率/宽屏线（2026-10-13 重开 · 逆向史全文 → `MEMORY-archive-2026-10-15.md` §C · `docs\53–67`）

**目标**：引擎原生 16:9 宽屏，一屏看更多地图（显示层缩放不是正解，已排除）。

**当前状态（2026-10-15）**：
- **唯一入口** `D:\Program Files\PeG\启动-16比9-内存版.cmd`（运行期内存补丁，exe 零改动，母本 md5 `c462e897…`）；`--selftest` 267 条全绿。试验 exe/ddraw 已收档 `archive\`。
- **已实机确认**：DDrawCompat 0.7.1 + `FullscreenMode=exclusive` ⇒ **输入/文字/色键三要素全通**（品红消失、悬停文字正常、鼠标可动）。
- **待验证**：M 组（地图面/绘制界 31 处 `0x780`→4096，治地图黑屏/破碎）已默认开打，等用户实机跑。
- **关键定论**：屏幕描述符写死 800×600 是画布类症状根因（`docs\64`）；位块助手 `0x41EB70` 裁剪算术须成套改（docs\66 §5.7）；**常量猜谜路线已叫停**——G/H/I/K 组零可见变化 ⇒ 控制点在函数行为不在常量，改走「分层策略 + 运行时几何拦截」（`docs\67`）。
- **工具**：`peg_launcher.py`（内存补丁启动器）· `diag_ddraw.py --play/--restore`（显示层换装）· `hint_pe.py`/`d.py`/`xr.py`/`vtcalls.py`/`find_mem.py`/`peek_va.py`（逆向工具箱）。
- ⚠️ 纪律：换层脚本「换入前校 md5、finally 必还原」；调试器路线（DEBUG_ONLY_THIS_PROCESS）在 32 位进程建不出窗口，已废弃；一次只改一类、无证据不算完成。

---

## 附：待办速查

| 事项 | 位置 |
|---|---|
| PeG-WW2 实机复测 | 用户跑 `D:\Program Files\PeG-WW2` |
| PeG-WW2 `方法\` 总结＋经验上浮技能 | `pegww2\方法\`（现为空） |
| `Bon.→第76营` 系统性误译修法 | 待用户裁定（`docs\52` §六-3） |
| PeG 宽屏 M 组实机验证 | `启动-16比9-内存版.cmd` |
| 地名收敛 ②③④（docs\48 §九） | 词库值==英文 62 条 · PeG 简报 9 处 A-HI · WW2 地图名 36 组 |
| 残留 28 行同键多译 | 只能走 `scn-place-override.tsv`（按场景词干） |
