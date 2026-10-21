# pegww2 — 《PeG-WW2 2.7》（People's General 二战 MOD，Redball 2005）简中化子项目

> 工作区 `D:\DSH\军事游戏汉化` 的 **PeG-WW2 子项目归档**。对位前作 [`../peg/`](../peg/README.md)（同引擎、已收官的 PeG 冷战线）。
> **用途**：用户研究 **「西方游戏文化渗透史」** 的对象 —— 以二战为题材、由社区 MOD 作者维护的 SSI *People's General* 改版。
> ⚠️ **仅供学习研究，请支持原版**；汉化只做语言转换，**不改原文世界观、阵营划分与叙事措辞**（保真优先）。
> 发布仓库：`https://github.com/Akkingking47/peg-cht`（本作与 PeG 同仓；成品包见 §发布包）。

## ⚡ 入口（30 秒；先读这三处，其余按需）

| 想知道什么 | 读这里 |
|---|---|
| **现在做到哪、资产在哪** | 本文件 §一句话结论 + §现况表（只此两节） |
| **场景层真源/派生物/归档怎么分** | [`research/README.md`](research/README.md)（顶层只有 34 个文件；派生物在 `_derived/`，历史在 `_superseded/`） |
| **踩过的坑与可复用判据** | [`方法/踩坑档案-W1至W23.md`](方法/踩坑档案-W1至W23.md) · [`方法/资产治理与索引规范.md`](方法/资产治理与索引规范.md) |
| **开工跑什么命令** | 本文件 §工具链速查 + §汉化流水线（顺序不可颠倒） |

> ⚠️ 本 README **只留索引与现役内容**；历史踩坑档案已下沉 `方法/`——**不要上手就读全文**。

## 一句话结论

PeG-WW2 是 **SSI *modgen* 引擎（1998-08-24 构建）** 游戏，**12 个 efile 与前作已汉化成功的 `PeG030.exe` 是同一构建**，
三处双字节补丁落点**逐字节等于原版** ⇒ **补丁 1:1 套用，无需重新逆向**。
**文本 100% 外置**，exe 只硬编码文件名 stem（12 个 efile **完全一致**）⇒ **改一次全部生效**。

**现状（2026-10-20 · 三层全部部署完毕，待实机复测）**：

- **exe 层**：**12 个 efile 已打补丁**（各 261 B：字集 / 字符类别表 / 代码页 / 日期 LCID），原版另存 `<名>.orig-backup`
- **界面层**：✅ **5/5 全量中文化并部署** —— `WW2Gui.txt` 604 · `WW2Misc.txt` 45 · `WW2Tips.TXT` 43 · `ww2-eqp.txt` 906 唯一串 · `WW2NAME.TXT` 400 条
- **实机**：**界面层已实测通过** —— 中文成像干净（无方块/缺字/裁切）、日期 `1944年8月30日`、英文零影响 ⇒ **无需字体补丁**
- **场景层**：✅ **21,865 条唯一行全部译完（空译 0）** —— 生成 **3,777 个文件 / 改动 47,049 行 / 五道校验 0 失败**；已部署
- **场景层（2026-10-20 番号收口批）**：真源 `ww2-scn-map.tsv` **21,904 → 24,031 行**；
  生成 **3,798 文件 / 改动 54,792 行 / 五道校验 0 失败**；增量部署 **222 文件**（回读 0 不一致）
  —— 收口细节见 [`方法/踩坑档案-W1至W23.md`](方法/踩坑档案-W1至W23.md) §番号展开收口
- **部署核验**（2026-10-11 复跑）：`verify_deploy.py` 三方 sha **全绿**（12 efile + 5 文本）；
  成品 vs 游戏目录 **3,777 + 2 逐文件 sha 全一致（0 不一致 / 0 缺失）**
- **收尾审计**：`dup_check`（50 组命中）·「中文串残留英文」扫描 · 「游戏目录残留英文行」扫描 —— **均无损**，
  命中项全为缩写/拼写变体，或**有意保留**的军级罗马数字（`XXXVIII`）、海军前缀（`HMS`/`KMS`/`USS`/`ITS`）、
  部队代号（`GMech`/`DAK`）与 MOD 元数据（`Gameset:` / `Equipment: … E-File` / `PeGWW2 conversion:`）
- **待办**：① **用户实机复测**（场景层 + 兵器名缩短后效果）
  —— 清单已备好：[`research\实机复测清单-场景层.md`](research/实机复测清单-场景层.md)（9 张待截图 + 判据 + 误报速记）
  ② **技能上浮**（`方法\` 已有 7 篇，唯此一款未上浮）
- **W20 实机反馈处置**：三图三问题已定责，**只有「兵器名溢出」是本作问题**，已按方案 A + A′ 修复
  （载具括注缩写 17 行 ＋ 删除英文没有的类别词 78 行）——详见 [`方法/踩坑档案-W1至W23.md`](方法/踩坑档案-W1至W23.md)

## 发布包

> 仓库 `https://github.com/Akkingking47/peg-cht` 的 `release/` 下提供「解压覆盖原版目录即可玩」的成品包：

| 包 | 文件 | 大小 | 内容 |
|---|---|---|---|
| 精简版 | `release/PeG-WW2-汉化包-精简版-20261021.zip` | 4.5 MB | 3,703 场景文本 + 根目录文本 + 12 个中文 exe（不含旗帜） |
| 完整版 | `release/PeG-WW2-汉化包-完整版-20261021.zip` | 77.7 MB | 上述全部 + `WW2GEN.dat`（史实德国旗） |

> 精简版随仓库跟踪；完整版建议作为 GitHub Release 资产。安装/还原见包内 `安装说明.txt`。

> ⚠️ **跑本项目脚本前先设** `$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'` ——
> 否则脚本里的 `✅`/`⭐` 撞 GBK 控制台编码，**在第一次打印就崩**。


> ⭐ **踩坑档案 W1–W23 全文已迁至** [`方法/踩坑档案-W1至W23.md`](方法/踩坑档案-W1至W23.md)
> （含 W15/W16/W17/W19/W20/A′ 与「表≠生效」番号教训；README 只留索引，避免上手即读 400 行）。

### 场景层批次账（每片 600 行，**严格串行**）

| 批 | 内容 | 唯一行 | 片数 |
|---|---|---:|---:|
| `m` | 地图格名/场名/地名 | 3,368 | 6 |
| `u` | 部队名/单位名 | 4,127 | 7 |
| `prose` | 简报/战役内简报/战后评述 | 4,021 | 7 |
| **合计** | | **21,865** | **20** |

> ⚠️ **本层只做整行精确匹配，绝不做行内子串替换** —— 前作踩过「内嵌替换误伤」
> （`Type 05-I Taliban` 只替换行内 `Taliban` ⇒ 括号里只剩 `(Taliban)`）。未命中的行一律**原样保留**，绝不局部改写。

## 档案

| 文件 | 内容 |
|---|---|
| [`../docs/40-PeG-WW2中文化可行性评估.md`](../docs/40-PeG-WW2中文化可行性评估.md) | ⭐⭐ **阶段 0 交付**：引擎识别 · 文本普查 · 工作量测算 · 位图取证 · 风险表 · 路线 |
| `方法\` | 本作经验总结 **7 篇**：**`踩坑档案-W1至W23`** · **`资产治理与索引规范`** · `全程复盘-踩坑与问题汇总` · `术语统一-治本` · `DOCS汉化经验` · `DOCS证据-问题定性` · `面向玩家文档-汉化计划` |
| `~/.trae-cn/skills/` | ✅ **技能上浮已完成**（2026-10-20）：`retro-game-hanhua-playbook`（W1–W23 → 触发/规则/反面）· `cm-asset-governance`（七条治理判据） |
| [`research/README.md`](research/README.md) | ⭐ **场景层资产索引**（2026-10-20 建）：顶层**只 34 个**（真源/填表/输入/人读）· 派生物在 `_derived/` · 历史在 `_superseded/` |
| [`research/_derived/`](research/_derived/) | **生成器产出（可复算，勿手改）**：`_对照-*` · `_u-*-mined` · `_番号展开-对照表` · `_番号未展开统计*` · 收口四表；**11 个脚本已重定向到此** |
| [`research/_superseded/`](research/_superseded/) | **归档（可逆，勿删）**：`merged/` 2 册（17→1、12→1）· `rounds/` 177 · `retired/` 67 · `backups/` 12 · `tmp/` 15；留痕 3 份 |
| [`research/evidence/`](research/evidence/) | ⭐ 原始证据（脚本可复算）：普查报告 · `.scn` 字段 · 工作量 · 位图实渲染 PNG |
| `research\ui-glossary.tsv` | 界面军事术语表（阶段 1 Gate-1 产出，**待建**；先复用 `../peg/research/ui-glossary.tsv`） |
| [`testbed/backup/`](testbed/backup/) | ⭐ **原版备份链（勿删）**：12 efile + 8 文本 + `backup-manifest.tsv`（sha256） |
| `../../work/pegww2/` | ⭐ **全部脚本的唯一入口**（侦察 / 备份 / 补丁 / 生成器；**编辑入口在这里**） |
| `../work/pegww2/scn/` | **场景层「番号/国籍/年代」分析工具集**（2026-10-20 自 `pegww2\work\scn\` 迁入，与原两处脚本树合并）；用途索引见其 `README.md` |
| `work/pegww2/scn/` 的数据 | `pegww2\work\scn\chunks\`（4,021 行 prose **原英文参照**，被 `_scn-file-overrides.tsv` 当证据引用）**按 `.gitignore` 白名单留在 `pegww2` 侧，勿随脚本迁走** |
| `testbed/out/_lineage/` | 溯源 sidecar（3,779 个 `*.lineage.tsv`）**已从成品目录顶层移出**；需重生成时须显式指定 `gen_scn.py --lineage=testbed/out/_lineage` |

## 现况表（2026-10-20）

| 核心问题 | 结论 | 判据 |
|---|---|---|
| 中文能不能显示 | ✅ 预期能 —— 打 3 处双字节开关 + 日期 LCID | 落点与 PeG 逐字节相同 `[已实测]`；**成像待实机截图** |
| 文字存在哪 | 12 efile 只硬编码 stem `ww2gui/ww2misc/ww2name/ww2tips/ww2-eqp/ww2gen`；其余纯文本 | PE 串检索 `[已实测]` |
| 界面文本 | `WW2Gui.txt` 605 行 · `WW2Misc.txt` 45 · `WW2NAME.TXT` 401 · `WW2Tips.TXT` 44 · `ww2-eqp.txt` 1,001 | 全库普查 `[已实测]` |
| 场景层体量 | **3,783 文本文件 / 60,091 非空行 / 3.15 万唯一串 / 约 2.77 万可译唯一** | `recon5` `[已实测]` |
| 场景名从哪来 | `<场景>_m.txt` 第 `[.SCN@4]` 行；本作 **`@4` 恒 0** | 648/648 `[已实测]` |
| 开局简报从哪来 | `.SCN@11329` 的 stem；目录/扩展名由 **`@11349`** 定（`0`=Scenario+`.TXT`，`1`=Userscen+`.PLY`） | `[推定，沿用前作，待 atime 复验]` |
| 哪个场景进列表 | `.SCN@0 == 0` ⇒ **79 个**（569 个为战役专用） | `[已实测]` |
| 描述框 | **仅 2 个 `.ply`**（前作 14 个） | `[已实测]` |
| 编码 | 出稿 **GBK(936) + 无 BOM + 沿用原文换行**；拆行 `(\r\n\|\r\|\n)` 三态 | `[已实测]` |
| 位图文字 | 25 个全屏条目；`STARTSCR` + 12 国别画面**实渲染无文字** | `research/evidence/*.png` `[已实测]` |
| 词库复用 | 61,284 条既有词库，场景层**整串命中 24.8%** | `[已实测]` |
| 中文成像 | ✅ **干净**：`下一部队`/`补给`/`结束回合` 等无方块、无缺字、无裁切 | 用户实机截图 `research\evidence\R2-*.png` `[已实测]` |
| 字体补丁 | ✅ **不需要** —— ACP=936 下字体链接回退出中文 | 同上（`GetGlyphIndicesW` 报缺字形≠画不出） `[已实测]` |
| 界面层进度 | ✅ `WW2Gui` 604 · `WW2Misc` 45 · `WW2Tips` 43 · `ww2-eqp` 906 唯一串 | 生成器四道校验 + 三方 sha 对齐 `[已实测]` |
| 人名层进度 | ✅ `WW2NAME` 400 条（已部署，sha 对齐） | `verify_deploy.py` `[已实测]` |
| 场景层进度 | ✅ 真源 **24,025 有效键**（原 21,865）⇒ **3,798 文件 / 改动 54,792 行 / 五道校验 0 失败** | `evidence/gen-scn.txt` `[已实测]` |
| 场景层部署 | ✅ 成品 vs 游戏目录 **逐文件 sha 全一致**（2026-10-20 增量 222 文件 / 0 失败 / 回读 0 不一致） | `deploy-scn.txt` + 递归比对 `[已实测]` |
| 番号展开收口 | ✅ 6414 行对照表 → **落真源 2167 行**（更新 40 + 新增 2127）· 未落 249（冲突 36 / 纯数字 213） | `_番号收口-*` `[已实测]` |
| `Bon.→第76营` | ✅ **已闭环**（OLGWW2 44/44 · GCE 32/32 · 全域残留 0 · 26 张表旧值 0） | `bon76_apply.py verify/gceverify/audit` `[已实测]` |
| 资产整理（2026-10-20） | ✅ `research/` 顶层 **217 → 149 → 34**（v2 判据：按「下一步要不要直接打开」分层；派生物 **20** 进 `_derived/`、同族 **29** 合并成 2 册、历史 **67** 进 `retired/`）· 11 个脚本输出重定向 · README **403 → 195 行** | `reorg_research.py` / `split_readme.py`（均幂等 + dry-run 默认） `[已实测]` |
| 资产整理（第二阶段） | ✅ **脚本树 2 → 1**（`pegww2\work\scn` 26 件迁入 `work\pegww2\scn\`；数据 `chunks\` 留 `pegww2` 侧）· `testbed\out\SCENARIO` 顶层 **7,573 → 3,796** 文件（3,779 sidecar 移入 `out\_lineage\`）· `.gitignore` 补 `.mjs` 白名单 · `work\SCRIPTS.md` 重生成并**修掉扫描器自引用污染** · 2 个技能上浮 | `方法\资产治理与索引规范.md` §四 `[已实测]` |
| 收尾审计 | ✅ `dup_check` 50 组 + 残留英文扫描**均无损**（命中项=缩写/拼写变体或有意保留） | `evidence/dup-check.txt` `[已实测]` |
| 场景层实机 | 🟡 **待用户复测**（21:30 有启动痕迹，尚无新截图） | — |

## exe 补丁（FO 制 · 与前作同一套）

| # | 用途 | FO | 原 → 新 |
|---|---|---|---|
| ① | `CreateFontA` `iCharSet` | `0x70CE4` | `00` → `86`（GB2312） |
| ② | `_pctype` 高字节区（0x81–0xFE） | `0xA938A`–`0xA9489` | `0x0000` → `0x8040` |
| ③ | `__mbcodepage` | `0xA948C` | `1` → `936` |
| ④ | 日期 LCID | `0x7BE86` | `A1 48 91 49` → `B8 04 08 00`（zh-CN） |

> ⚠️ **不打**前作已作废的两条：行终止表（被 ② 取代）、`0x46FF1C` 丢行补丁（成品 exe 里并不存在）。
> ⚠️ 参照系：已实机成功的 `PeG030.exe` 与其原版差异**共 382 字节**，全落在上述四段 + 无效的 `lc_time` 表内。

## 工具链速查

```bash
PY=C:\Python314\python.exe          # ⚠️ 旧 venv（.workbuddy\...\envs\default）已失效：base 指向已卸载的 WorkBuddy
cd D:\DSH\军事游戏汉化
# ⚠️ Windows PowerShell 下必须加这两行，否则 ✅/⭐ 撞 GBK 控制台编码直接崩：
#    $env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'

# —— 阶段 0 侦察（只读，可复算）——
$PY work\pegww2\recon_engine.py        # PE/段/导入/stem
$PY work\pegww2\recon2.py              # 补丁落点逐字节核验
$PY work\pegww2\recon3.py              # 载体普查 + 编码/行尾/BOM
$PY work\pegww2\recon4_scn.py          # .scn 布局
$PY work\pegww2\recon5_workload.py     # 工作量 + 词库覆盖率
$PY work\pegww2\recon6_bitmap.py       # 位图渲染取证
$PY work\pegww2\recon7_fullscreen.py   # 全屏候选清单
$PY work\pegww2\recon8_render.py STARTSCR.S16:0   # 指定条目渲染
$PY work\pegww2\recon9_scnfields.py    # .scn 字段精查

# —— 备份（幂等；只读游戏目录，写入工作区）——
$PY work\pegww2\backup_originals.py
```

> ⚠️ **本沙箱已知坑**：用 PowerShell 管道/重定向（`2>&1 | Tee-Object`）包裹原生 exe 会报
> `Access is denied` 并触发 sandbox 拒绝 ⇒ **不要包管道**；需要落盘时**让脚本自己写报告文件**。

### 汉化流水线（**顺序不可颠倒**）

```bash
PY=C:\Python314\python.exe

# ① 生成译法真源工作表（前作可复用部分预填）——已有则跳过，保护人工已填
$PY work\pegww2\make_worksheets.py
# ② 二次复用：同串（同英文串在前作别处的已验译法）+ 术语总库精确命中
$PY work\pegww2\add_value_reuse.py
# ③ ⭐ 对齐审计：清空前作错配行 + 剥离序号前缀（**2 列映射必跑**）
$PY work\pegww2\fix_line_map_align.py
# ④ 合并人工填译（行号模式；@KEEP=原样保留，@订正=强制覆盖）
$PY work\pegww2\merge_fill.py
# ⑤ 装备表人工确认覆盖 + 引号规范化
$PY work\pegww2\apply_eqp_fill.py
# ⑥ 生成（四道硬校验，任一不过拒绝落盘）
$PY work\pegww2\gen_text.py all      # 行号模式：WW2Gui / WW2Misc / WW2Tips
$PY work\pegww2\gen_value.py all     # 值模式：ww2-eqp / WW2NAME
# ⑦ 核验（不信任生成侧自述）
$PY work\pegww2\verify_eqp.py        # 装备表：集合一致 / 空值 / 残留 / 代号丢失 / 违禁
# ⑧ 部署（唯一会写游戏目录的脚本；默认 dry-run）与三方 sha 核验
$PY work\pegww2\deploy.py --exe --text WW2Gui.txt WW2Misc.txt WW2Tips.TXT ww2-eqp.txt --apply
$PY work\pegww2\verify_deploy.py
# 回滚
$PY work\pegww2\restore.py --apply
```

### 场景层（3,777 文件，**与根级文本是两条独立管线**）

```bash
# 生成（dry 空跑先看五道校验；默认 dry-run）
$PY work\pegww2\gen_scn.py dry         # 五道校验：行数 / CR·LF·TAB / 控制字符个数一致 / 禁用词 / GBK
$PY work\pegww2\gen_scn.py             # 真生成 → pegww2\testbed\out\{SCENARIO,USERSCEN}
# 名栏 vs 说明文件交叉核对（不一致项以说明文件为准，追加进 per-file 覆盖表）
$PY work\pegww2\crosscheck_names.py
# 部署 + 核验（场景层专用；先建备份再覆盖，回读校验）
$PY work\pegww2\deploy_scn.py --apply
$PY work\pegww2\verify_deploy.py
# 收尾审计（数字都可复算）
$PY work\pegww2\run_dup_check.py 200   # 复制粘贴错译 → evidence\dup-check.txt
```

> ⚠️ **「生成」必须从 `testbed\backup\` 读原文**；**「部署」绝不读原文**。两者是不同脚本、不同命令。
> ⚠️ **整串键控不能用在「同串多义」上**（W17）—— 同一原文在不同文件需不同译文时，**必须走 per-file 覆盖**
> （`research\_scn-file-overrides.tsv`，现 **88 条**），否则会**静默误伤**别处正文。

## 边界与纪律（沿用前作硬纪律）

- 游戏目录 `D:\Program Files\PeG-WW2` **原文零改动**，直至阶段 2 实机验证通过并获授权。
- **绝不覆盖改原文**；备份与覆盖**分两条命令**；**先重建到临时 → 回读校验 → 才写正式**。
- 构建必须**从 `testbed\backup\` 读原文**，否则第二次运行会把中文再翻一次。
- 需要截图时**停下告知，由用户手动截取**；**严禁自行启动/点击游戏**。
- **不全量翻译**说明/脚本类文件：`WW2gen.txt`（MOD 素材清单）· `DOCS\` 手册 · `CINE\`/`WAVS\` 媒体 ⇒ **排除**。
- **本归档不含游戏本体的受版权保护内容**；`research/` 内引用原文仅为研究定位所需。
