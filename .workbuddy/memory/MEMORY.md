# 汉化工程 · 索引（多游戏工作区）

> 工作区 `D:\DSH\军事游戏汉化`。**本文件只放状态与指针，明细一律下沉到 `docs\` 与归档**。
> 归档（**勿删**）：`MECHANICS.md`（机制 89KB）· `MEMORY-archive-2026-10-10.md` · `MEMORY-PeG-archive-2026-10-10.md` ·
> `MEMORY-OpenPG-archive-2026-10-10.md` · **`MEMORY-archive-2026-10-15.md`**（A＝PeG 明细 · B＝PeG-WW2 明细 · C＝宽屏线全文）。
> 2026-10-16 第五次压缩（上一版快照 `MEMORY.pre-compress-2026-10-15.md`）。
> ⚠️ 环境真源：`env.cmd` ＋ `requirements.txt`；解释器 `C:\Python314\python.exe`（3.14.7，旧 venv 失效）；跑脚本前先 `call env.cmd`（或 `PYTHONIOENCODING=utf-8; PYTHONUTF8=1`）；PowerShell 别包管道。

## 〇、游戏清单

| 代号 | 路径 | 引擎/界面 | 状态 |
|---|---|---|---|
| **OpenPG** | `D:\OpenPG2` | OpenGen 26.3.30.0；SDL2+SDL2_ttf | 主线，21 efile 收官 **11** |
| **OpenGeneral** | `D:\OpenGeneral` | **同引擎** OpenGen 25.02.26.0；波兰 GUS 版 | UI＋阶段 1/2/3 已完成；**下一步 阶段 4 `EFILE_GUS`** |
| **PeG** | `D:\Program Files\PeG` | SSI *modgen* 1998；DirectDraw+GDI ANSI | 文本内容层已汉化；**高分辨率线进行中（§五）** |
| **PeG-WW2** | `D:\Program Files\PeG-WW2` | 同引擎（与 PeG030 同构建 TimeDateStamp 903998521） | exe+界面+场景三层已部署（**待用户实机复测**） |
| **PG Forever** | 见 `PGFOREVER.md` | HTMLayout | UI 层完成，见 `docs\05` |
| **JTCS**（East Front / West Front / Rising Sun） | `D:\Program Files\John Tiller's Campaign Series` | JTCS **v2.05**（2025-09-08 重编译）MFC9/MSVC2008；DirectDraw+GDI **ANSI** | **只读评估完成，未动原文**；方案 `docs\91`，工具 `work\jtcs\` |

## 一、PeG 文本线（明细 → 归档 §A · `peg\README.md` · `peg\方法\` · `docs\38`）

**已达可用**：中文显示 ｜ 5 文本文件 ｜ 场景 825 `.txt`+14 `.ply` ｜ 列表分组编号 ｜ 简报/描述框 ｜ 日期汉化 ｜ UI 术语+装备名。
部署＝`PeG030.exe`（MBCS+日期补丁）＋ 825 `.txt` ＋ 14 `.ply`。**备份链勿删**：`PeG030.exe.orig-backup` → `testbed\*.pre-*` ｜ `backup-scn-flag\` ｜ `backup-ui-src\`。
- exe 补丁：`patch-mbcs.py`（iCharSet/`_pctype`/`__mbcodepage`＝中文治本）＋ `patch-date-lcid-zh.py`（`0x7BE86` LCID→0x0804）；`patch-lc-time-zh.py` 无效仅留档。
- 场景界面定论：场景名＝`_m.txt` 第 [`.SCN`@4] 行；进列表＝`@0==0`；「进行场景」≤2 人＝`@216(P3)==0`；描述框＝`.ply`（第 0 行须标题）；开局简报＝`@11329`+`@11349` **双字段**；列表按字节序 ⇒ `NN ` 前缀钉序。
- UI 术语：`Air Mission`→空中任务/出击、`Air Defense`→对空防御/防空、`Air Transport`→空运/空中运输（`peg\research\ui-glossary.tsv`）。文风总纲 `peg\research\各国军语风格口径.md`；官方繁中《解放軍之怒》考古同目录。
- 工具链：`gen_scn_zh.py`｜`gen_ply_zh.py`｜`gen_gui030_zh.py`｜`gen_peg_text.py`。⚠️ build 从 `testbed\backup\` 读原文；译法（`*-map.tsv`）/逻辑（`gen_*.py`）分离。

## 一之二、PeG-WW2（明细 → 归档 §B · `pegww2\README.md` · `docs\40–52`）

三层已部署（12 efile 补丁各 261B ＋ 5 界面文本 ＋ 场景层 **24,031 行真源 / 3,798 文件 / 五道校验 0 失败**）。
- **19+ 条踩坑 W1–W23** 已下沉到 [`pegww2\方法\踩坑档案-W1至W23.md`]（README 403→184 行，只留索引）；最值钱：W17 整串键控不适合同串多义（须 per-file 覆盖）；W19 描述框双字段；W22「表≠生效」；W23 消费端静默过滤。
- 地名三维规则（阵营/年代）：真源 `glossary\layers\faction-places.tsv`，审计器 `faction_place_audit.py`（视角 90%、年代 21%＝瓶颈）。⭐ 改真源必须重跑 `ingest_layers → converge_plan → layer_gate`；按英文键整行替换，禁全局替换。
- **番号展开批次（2026-10-20 收口）**：对照表 6414 行里「处置=译 5854 行」**此前从未落真源**（游戏里 `64/16` 一直是原文）⇒ 本轮落 **2167 行**（更新 40 + 新增 2127）· 部署 222 文件 · 三方 sha 全绿。工具 `work\pegww2\apply_desig_closure.py`。留痕见 `research\_番号收口-*`。
- ⚠️ **未落 249 行**：同键多译 36（须走 per-file 覆盖）＋ 纯数字键 213（`ingest_layers.load_pairs` 第 134 行**跳过纯数字 en 键**，落了 layer_gate 报「缺失 N」拒构建 ⇒ 本批不落）。
- ✅ **`Bon.→第76营` 已闭环**（OLGWW2 44/44 · GCE 32/32 · 全域残留 0 · 26 张表旧值 0），此前待办属**文档滞后**。
- **资产整理（2026-10-20 两轮）**：`research/` 顶层 **217 → 149 → 34**。v2 判据＝「**下一步要不要直接打开**」：派生物 **20** 进 `_derived/`（**11 个脚本已重定向输出，重跑不再弄脏顶层**）· 同族同构 **29** 合并成 2 册（`_superseded/merged/`）· 历史留痕 **67** 进 `retired/`。索引 [`pegww2\research\README.md`] · 判据 [`pegww2\方法\资产治理与索引规范.md`]（7 条）· 工具 `work\pegww2\reorg_research.py` + `split_readme.py`（均幂等 · dry-run 默认）。README 403→184 行。
- 遗留：`方法\` 已有 **7 篇**，**技能上浮未做**（唯一一款没上浮的）。→ ✅ **2026-10-20 晚已完成**（见下条）。
- **资产整理第二阶段（2026-10-20 晚）**：① **脚本树 2→1**（`pegww2\work\scn` 22 `.py`+3 `.mjs` → `work\pegww2\scn\`；数据 `chunks\` **留 pegww2 侧**免脱离版本控制；⚠️ `.gitignore` 原缺 `!.mjs` 白名单已补）· ② **`testbed\out` 3,779 个 `*.lineage.tsv` 移入 `out\_lineage\`**（`out\SCENARIO` 顶层 7,573→3,796；未来重生成须 `gen_scn.py --lineage=testbed/out/_lineage`）· ③ **2 个用户级技能上浮**（`~/.trae-cn/skills/retro-game-hanhua-playbook` + `cm-asset-governance`）。校验全绿：py 895/0 失败 · `regression.py` rc=0 · `gen_scn dry` 3800/0 失败 · 成品 vs 游戏目录 3796+2 全一致。⚠️ 修复 `_c1_scan_refs.py` 自引用污染后重生成 `work\SCRIPTS.md`。

## 二、OpenPG 主线（明细 → `MEMORY-OpenPG-archive-2026-10-10.md` · `docs\08/24/30`）

- 译名真源 `glossary\standard-glossary.tsv`（23,200）；⭐ 总词库 `work\xscn\master-glossary.tsv`（119,624，四层）。**新 efile 先跑 `apply_master.py`**（覆盖 ~93%）；冲突裁定 `resolve_master.py`+`master-overrides.tsv`。收尾四连：`build_dict && build_root_dict && build_prose_dict && build_master`。
- 收官 11/21：`AG·AO·ATOMIC·BASEKORP·COMWW2·GCE·KAISER·NASHORNPBEM·OLGWW2·OPENPG·PzLIGA`（判据＝`.xscn` 漏译 ≤0.5% 且 `.txt` >99% 且 `.ply` 全译）。
- ⚠️ 判进度**必须读文件审计**：①安装戳/官方自带 ②映射表 `src==dst` 恒等 —— 都不算。⚠️ cp1252 假汉字骗 `decode('gbk')`；可靠判据＝GB2312 字节范围＋黑名单（`progress.py --dump-fake`）。⛔ 弃用 `audit_map_quality/pollution/number_segments.py`。

## 二之三、OpenGeneral（明细 → `docs\70–80` · 日志 `2026-10-16.md`）

5 efile：`GUS` / `GUS_Wx` / `GUS_PeG` / `GUS_Zx` / `ALBERICH`（共 3,046 场景）。
- ✅ UI 层（零翻译搬运：`strings-zh.txt`+`simhei.ttf`+3 张 PNG，`Settings.cfg` 只改 3 行）｜✅ 阶段 0 工具链 `--root`/`resolve_dir()`/`check_loop.py`｜✅ `docs\76` 编码修正（**本作 `GUS` 是 cp1250**，其余 cp1252）｜✅ 阶段 1 根级 25 件（5×5）｜✅ 阶段 2 `GUS_Zx` 全层收官（G2 实机「无英文波兰文」）｜✅ 阶段 3 `ALBERICH` 全层收官（8 `.xscn`／332 槽，`check_loop` 异常 0）。
- ⏭ **阶段 4 `EFILE_GUS`**：978 `.xscn`／27,367 唯一串（程序覆盖仅 46.8%）；`SCENARIO\*.txt` 2,463 个／1,146,106 字符。`.xscn` 覆盖率合计实测 **39.4%**。方案对比见 `docs\80-OpenGeneral阶段4`。
- **可见文本面穷尽清单**（`docs\79` §十一）：要汉化的只有根级 5 件 + `SCENARIO\*.txt`/`*.tmsg` + `.xscn` 串区；`MISC.TXT`/`Strings-Leaders.PL` 是**死文件**别做；7 条海军领袖技能为 exe 硬编码盲区，**不作为缺陷**。

## 三、硬纪律（跨作通用）

1. **绝不覆盖原文**；备份与覆盖分两条命令；**先重建到临时 → 回读校验 → 才写正式**。
2. 出稿 **GBK(936)、无 BOM**（OpenPG 词库 TSV 例外 UTF-8 BOM）；换行沿用原文；拆行须三态 `(\r\n|\r|\n)`。
3. **改 exe 前先查导入表**（`GetDateFormatA`/`GetLocaleInfoA` ⇒ 文本来自 Windows，改数据无用）。
4. **补丁三纪律**：幂等 · 默认 dry-run（`--apply` 才写）· 等长替换优先。
5. 不全量翻译脚本/说明类文件——建整文件排除清单。
6. **不靠肉眼不靠猜**——编码、字体、格宽、行数全部实测或脚本复算。
7. **需要截图时停下告知，由用户手动截取；严禁自行启动/点击游戏**。定式：我说明要看哪个界面 → 用户截图或口述 → 我据此判断。⚠️ 2026-10-16 在 `D:\OpenGeneral` 违反一次（自行启动 `OpenGen.exe`＋模拟点击），用户重申此条。
8. 结论被推翻时写明撤回原因；未实测的标 `[推定]`。
9. OpenPG 字体必须 `simhei.ttf`（禁 `deng.ttf`）；`UI_Lang` 必须 `strings-zh`。
10. 优先级铁律：**词典（已交付件实证）> 归一化 > 人工批次**（后者只填空缺）。
11. **并发子代理上限 2–3**。⚠️ 2026-10-16 一次开 7 个导致用户界面反复崩溃，用户当场定规矩。
12. **子代理产物要亲自复核**：读回输出 → 与输入逐行对齐 → 统计「译文/保留」分布 → 抽检保留行。⚠️ equip-03 只交 49 条（同规模批次交 135 条）——口径要写死在派活时。
13. **不许把「子代理在跑」当「会做完」**：唯一判据是磁盘有没有输出文件且行数对齐。
14. **装备名截断是引擎行为，不改数据**。受控实验定案：`汉`/`汉汉汉`/`汉 汉 汉`/`国民警卫` 全完整，`汉汉汉汉` 显示 `汉汉汉?` ⇒ **卡的是汉字个数（阈值 3）**，非像素宽非字节数；单位面板里同名完整显示 ⇒ 信息不丢。⚠️ 教训：别凭少量样本归纳引擎规则，要布受控实验；小字截图先程序化定位文字带再裁。**未了**：「最长连续 ≤3」vs「总数 ≤3」未区分，用户说不测了。
15. **双字节写盘三静默陷阱**：① `xscn.py` 的 `--src-first` 必须显式传，否则 cp1250 变音符被 GBK 解成假汉字而 `continue` 跳过（阶段 2 曾漏写 60 条）；② `load_map()` 写死跳过第 0 行 ⇒ 映射表**必须带表头**；③ KEEP 不能写 `dst==src`（含变音符时 GBK 重编码仍不同会被静默改写）⇒ 剔除同行，靠「不在表里」实现保留。
16. 其他 disciplines： OpenGeneral 可见面清单见 §二之三。

## 四、跨作经验 → 技能（`~/.workbuddy/skills/`）

| 层 | 技能 | 覆盖 |
|---|---|---|
| 方法论 | `military-game-docs-translation` | 跨引擎（双轨制/文风/单字节引擎范式/开工单） |
| 项目 | `opengen-sdl2-efile-localization` | OpenPG |
| 项目 | `ssi-modgen-peg-localization` | PeG |
| 项目 | `pgforever-htmlayout-localization` | PG Forever |
| 手法库 | `win-game-html-ui-localization` | 跨项目二进制/界面通用手法 |

⚠️ 分层判据（唯一）：「换一款游戏/引擎，这条还成立吗？」成立⇒方法论｜同引擎⇒项目技能｜只对本作⇒项目档案。
⚠️ 收尾必做「可复用清单」盘点。**PeG 19/19 已上浮；PeG-WW2 未做**。

## 五、PeG 高分辨率/宽屏线（逆向史全文 → 归档 §C · `docs\53–67/71–74` · **方案 `docs\80-PeG030`** · 实施 `docs\81`）

**目标**：原生 16:9／1080p，一屏看更多地图（**显示层拉伸不是正解，已排除**）。
> ⛔ **2026-10-19 已停用**（用户决定）：游戏目录已还原为纯汉化状态（`ddraw.dll`＝原 Svens 包装 md5 `337866f0…`；16:9 入口/说明/日志 → `archive\PeG-16比9-入口-已停用-20261019\`；母本 `PeG030.exe` md5 始终 `c462e897…` 未被改过）。`docs\80/81/82` 与 `work\peg\relayout\` **仅作归档，不再推进**。

**2026-10-16 路线重置**：常量猜谜（G/H/I/K 组零可见变化）已叫停 ⇒ 改走 **`docs\80` 的四层适配**：**(T1 显示分辨率 / T2 后缓冲与 blit 预算 / T3 UI 布局参数化 / T4 资源位图)**，核心是「**几何拦截层 = 坐标缩放 + 视口居中**」而非改常量。
- ✅ **P0 普查已交付**（`work\peg\relayout\`）：`layout_model.py`（坐标模型，六档断言，实跑通过）· `resolve.py`（站点解析→字节计划）· `gen_p0.py` · `sites.tsv`(275) · `tables.tsv`(18 表) · `text_immediates.tsv`(487 立即数) · `image.py`（母本只读 VA 读取）。
- ✅ **P1 已交付待实机**（`docs\81`）：`peg_launcher.py --relayout [--relayout-strategy S1|S2]`（默认关，开时自动关冲突的 I/K 组）；1920×1080 写 **1277 条**（=275−74(I)+1076 控件表）；`--selftest` 实测「1277 条写入并回读一致、exe 未改动」。入口 `D:\Program Files\PeG\启动-16比9-重排版P1.cmd`，回退用旧 `启动-16比9-内存版.cmd`。
- 🔴 **2026-10-16 独立复算发现 P1 模型的粒度缺陷**（`docs\82`）：P1 是**单一全局仿射**（屏幕中心=设计中心 400,300 的像），但表里**没有一个面板记录是居中的**（11 条 b11=4 面板外框偏心最大 (−229,−156)/(+175,+9)）⇒ 偏移被按 s 放大保留，1920×1080 下 win 9 组仍偏屏幕中心 **(−200,−119) px**、win 6 偏 (−149,−125) ⇒ **治不掉"子界面还在旧坐标"**。解法＝**按窗口组各自居中**：记录尾部 `byte@+0x0A` 疑似窗口 id（7 个取值、记录按段连续），每组的修正只是一笔常数平移 `Δ=(400−cx)·s,(300−cy)·s`，组内零形变 ⇒ A1/A2 自动继承。**该字段语义 [推定]**，需 V8 运行时确认（退路＝几何聚类）。加了 Δ 后改变 98.3% 字段目标值（1056 中 1038），写通道不变。 **[推定]** 分组字段语义待 V8。
- ⚠️ 记录清点实况（复算）：272 条 = 271 值域内（idx271 垃圾）+ **7 条 1×1 哑元**(0,263–268) + **2 条原始即倒置**(98/99，**不得扶正**)；有效矩形 264 条=1056 字段；实测写入 1076 = 271×4 − 8 个恒等字段 ⇒ `relayout_plan()` 打印的「272×4=1076」是**会计口径错误**（待修），不是功能问题。
- 复算脚本（可重跑、不采信日志）：`_check_p1.py`（六档不变量）· `_probe_groups.py`（结构/倒置）· `_probe_parent.py`（分组聚集）· `_probe_containers.py`（几何容器）· `_plan_group.py`（方案 B 量化）。
- **仍在使用**的内存补丁入口 `启动-16比9-内存版.cmd`（`work\peg\peg_launcher.py`，exe 零改动，母本 md5 `c462e897…`，`--selftest` 267 条）：默认 274 条 = 站点表/UI 记录/布局表 236 + **M** 31（地图面/绘制界 `0x780`→4096）+ **N** 8（横向滚动钳位守卫）。
- **显示层**：DDrawCompat 0.7.1 + `FullscreenMode=exclusive` ⇒ 输入/文字/色键三要素全通。⚠️ `LogLevel=trace` 会让鼠标完全失效（逐调用同步写盘），试玩必须 info。
- **已解决**：地图全黑 = 引擎把 scrollX 强制成 −202，源矩形左边界为负 ⇒ DirectDraw 整笔拒绝；N 组关掉强制 + M 组给 2176 像素余量后正常（实测 `scroll=17,271`、`extent=37x27`）。
- **待解决**：①选中单位后鼠标静止不显示移动范围阴影 ②鼠标拖影/黑块残留 ③坐标漂移（>800×600 区域）与点选精度。
- **关键地址**：视口 `[0x4af300]/[0x498d3c]/[0x498d40]/[0x498d44]`；滚动 `[0x4af2f8]/[0x4af2fc]`；地图面 `[0x655574]/[0x622A10]`；已绘范围 `[0x622d42]/[0x622d44]`；地尺寸立即数 `0x441BFD/0x441C04/0x441C90/0x441C97`；上屏 `0x41FF8A`；整块重绘 `0x41FA85`；逐格 `0x41F41C/0x41F685`；滚动更新器 `0x41F2C0`；整屏刷新 `0x44AC45`；控件循环 `0x423CD6`。
- **共享刷新标志 `0x498D74`**：40+ 处消费者各自「读标志→重绘自己那部分→清 0」。⚠️ 任何「每帧强制整屏刷新」的补丁都会抢掉别人的信号。
- 工具：`peg_launcher.py` · `diag_ddraw.py --play/--restore` · `diag_run.py` · `hint_pe.py`/`d.py`/`xr.py`/`vtcalls.py`/`find_mem.py`/`peek_va.py`。
- ⚠️ 纪律：换层脚本「换入前校 md5、finally 必还原」；调试器路线（DEBUG_ONLY_THIS_PROCESS）在 32 位进程建不出窗口，已废弃；**一次只改一类、无证据不算完成**。

---

## 六、JTCS（明细 → `docs\91` · 工具 `work\jtcs\` · 日志 2026-10-20 §四/§五）

三作共用一引擎：`ef.exe` 1,609,488 / `wf.exe`·`risun.exe` 1,610,000（RS 引擎改名）；资源同构 107 条目（MENU 165 项 · DIALOG 36 · STRING 173）。数据全为**纯文本 CRLF**（`.scn/.scl/.org/.oob/.txt/LOCATION.DAT`），**含 cp1252 变音字节**（`ä ö ü é ë ° "`）→ 必须归一化后整体 GBK，半译会吞字。
- **字体无需改**：21 处 `CreateFontA` 全 `charset=0`，仅 3 个名字（`Times New Roman`/`Times Roman`/`MS Sans Serif`）；GDI 实测 ACP=936 下自动换宋体、汉字正常（h=18 → 17px/字）。**备用补丁**＝就地改名字面量 `→SimSun`（等长可行）。运行环境必须 cp936。
- 分层：L1 资源(UTF-16) · L2 exe `.rdata` ASCII 串(4,446，须等长/短替换) · L3 场景(简报预折行,中位 9 行/最多 32) · L4 编成(634,621 行，名称在行尾、`.org` 缩进=层级) · L5 txt · L6 地名(5,581) · L8 含字位图 6 类 · L9 `.hlp` 不做。
- **含字位图**：`Menuscrn`(三作)/`Menu Screen`+`Charport`(仅 EF)/`phasebox`/`infobox`/`Extended InfoBox`(RS 无)；同名图三作 md5 不同。`EastFont.BMP`＝未引用遗留 [推定]。`Command Reports`/`Controls2`/`Tutorial`/`Victory*` 无字。
- 部署走自带 **JSGME**（`Mods/<模组>/<游戏目录>/` 镜像）；先译 EF（三作 exe 串重合 63%）。旧报告 `docs\90` 三处已修正（见 `docs\91` 附录 A）。

## 附：待办速查

| 事项 | 位置 |
|---|---|
| PeG-WW2 实机复测 | 用户跑 `D:\Program Files\PeG-WW2`（清单 `research\实机复测清单-场景层.md`） |
| ~~PeG-WW2 技能上浮~~ | ✅ 2026-10-20 完成：`~/.trae-cn/skills/retro-game-hanhua-playbook` + `cm-asset-governance` |
| ~~PeG-WW2 两处脚本树合并~~ | ✅ 2026-10-20 完成：`pegww2\work\scn` 26 件 → `work\pegww2\scn\`；数据 `chunks\` 留 pegww2 侧 |
| PeG-WW2 番号未落 249 行 | 冲突 36 → per-file 覆盖；纯数字 213 → 需先改 `ingest_layers` 过滤（独立决策） |
| ~~`Bon.→第76营` 修法~~ | ✅ 2026-10-20 核实**已闭环**（OLGWW2+GCE+26 表全绿） |
| ~~PeG030 高分辨率 P1/P2 实机验证~~ | ⛔ 2026-10-19 停用；线归档 `docs\80/81/82`，入口归档 `archive\PeG-16比9-入口-已停用-20261019\` |
| OpenGeneral 阶段 4 `EFILE_GUS` | 方案见 `docs\80-OpenGeneral阶段4` |
| 地名收敛 ②③④（`docs\48` §九） | 词库值==英文 62 条 · 简报 9 处 · WW2 图名 36 组 |
| 残留 28 行同键多译 | 只能走 `scn-place-override.tsv` |
| JTCS 最小验证（MVP T1–T4） | 待用户确认后执行，方案 `docs\91` §三：备份→四层各一测→判定/回滚/分支 A–D |
