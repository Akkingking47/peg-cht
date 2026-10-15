# MEMORY 归档 2026-10-15（第四次压缩迁出 · 勿删）

> 来源：MEMORY.md 2026-10-15 压缩。逐字节迁出，零改写。
> A＝PeG 明细（原 §一）· B＝PeG-WW2 明细（原 §一之二）· C＝PeG 高分辨率/宽屏线全文（原 §五 第 1–70 条）。

---

# A. PeG 明细（原 §一）

## 一、PeG（People's General）· 状态（明细 `MEMORY-PeG-archive-2026-10-10.md`）

**✅ 已达可用状态**：中文显示 ｜ 5 文本文件 ｜ 场景 825 `.txt` + 14 `.ply` ｜ 场景列表分组编号 ｜
简报/描述框 ｜ 日期汉化 ｜ UI 术语 + 装备名。
**部署形态**：`PeG030.exe`（MBCS + 日期补丁）＋ 825 `.txt` ＋ 14 `.ply`（Scenario/Userscen）。

**备份链（勿删）**：exe `PeG030.exe.orig-backup`（原版）→ `testbed\PeG030.exe.pre-month-zh`（MBCS 后）→
`…pre-lcid-zh`（月份补丁后）｜`.SCN` 快照 `testbed\backup-scn-flag\`｜UI/装备源码 `testbed\backup-ui-src\`。

**exe 三处补丁（工具在 `work\peg\`）**
1. **`patch-mbcs.py` — 中文显示治本**：① `0x4718E3` iCharSet `6A 00`→`6A 86`(GB2312)；
   ② `_pctype`(`0x4ABA8A`) `0x81–0xFE`→`0x8040`；③ `[0x4ABC8C]`(`__mbcodepage`) `1`→`936`。
2. `patch-lc-time-zh.py` — exe 内建 CRT `lc_time` 月份/星期表（`0x8B47C` 起）改中文。
   ⚠️ **实测无效（日期不走这里）**，仅作无害保留。
3. **`patch-date-lcid-zh.py` — ★真正生效的那一刀**：日期由 Windows **`GetDateFormatA`** 生成；
   `0x7BE86` `A1 48 91 49 00`→`B8 04 08 00 00`（`mov eax,0x0804`，zh-CN，等长 5B）⇒ 输出「2006年4月3日」。
   ⚠️ **方法论**：改 exe 字符串前**先查导入表**确认「谁在格式化/取名字」（看到 `GetDateFormatA` ⇒ 改 exe 数据无用）。

**「場景選擇」界面结构（第 24–29 轮定论 · 踩坑 3 次）**
- **场景名** ＝ `<场景名>_m.txt` 的**第 [`.SCN`@offset4] 行**（通常 0；`_m`/`_u` 不加原文括号）。
- **进列表判据** ＝ `.SCN@0 == 0`（`1`＝战役专用）⇒ 61 个。
  ⭐ **「进行场景」只显示 ≤2 人**：判据 `.SCN` Player3 主国家 `@216 == 0` ⇒
  **61 = 51（进行场景·单人组）+ 10（开始多人场景·多人组，P3≠0）**。⚠️ 曾误判为序号 bug，已证伪。
- **列表按「显示名」字节序排序**（ASCII 在 GBK 汉字前）⇒ 故加 `NN ` 前缀钉顺序（**分两组各自编号**）。
- **描述框 ＝ `.ply`**（定长 501B、NUL 填充；`场景名/日期/空行/描述`；全库 **14 个**）。
  ⭐ **描述框只显示第 1 行起** ⇒ **第 0 行必须是标题**（8+1 个原本缺标题 ⇒ 描述框空白）。
- **开局简报 ＝ `<@11329 名>.txt`** —— **与 `.ply` 是两个不同展示位**！14 个附加包场景原本无此 `.txt`，已补。
- ⭐⭐⭐ **双字段（第 29 轮真因）**：`@11329`(20B)＝intro 名（扩展名可有可无）；
  **`@11349`(1B)＝位置标志：`0`＝Scenario+`.TXT` ｜ `1`＝Userscen+`.PLY`** ⇒ 引擎据此找文件。
  已修 **8 个 flag 写错**的场景（`fix_scn_intro_flag.py`，每场景只改 1 字节）。
  ⚠️ **诊断法**：比对文件 **atime** 与游戏启动时刻（被读过的会刷新）。
  ⚠️ `_m.txt`/`_u.txt` **不受该 flag 影响**（atime 已证）。
  ⚠️ **只看 `@11329` 会漏判**（第 26/28 轮补 `.txt`、改 `.ply` 均无效，真因是 flag 错）。

**工具链**：`gen_scn_zh.py`（含长表整行直出 + 整文件排除 `REPORT|READ ME` + `(\r\n|\r|\n)` 三态拆行 +
`_m` 加分组序号）｜`gen_ply_zh.py`｜`gen_scn_desc_txt.py`（补 14 个 `.txt`）｜
`build_scn_number.py` + `build_scn_list_doc.py`。
⚠️ **build 必须从 `testbed\backup\` 读原文**（否则把中文再翻一次）。
⚠️ 教训：**「译/未译」计数＝有改动的行 ≠ 全译的行**（验收必须看内容）；**只译 `.txt` 会漏 `.ply`**。

**UI 术语定案**
- ⭐ **`Air Mission` ＝ 按词性分工**（★第 34 轮用户拍板）：
  **名词（面板名·资源名）⇒「空中任务」**：行 406 `M - 空中任务` · 517 `更多空中任务！` · 559–561 `空中任务点数`
  ｜ **动词（动作·按钮·事件）⇒「出击」**：行 487 `出击成本` · 488 `出击次数` · 489–491 `减少/增加一次出击`·
  `取消全部出击` · 513 `出击中止！` · 597/598 `执行已规划的出击`·`不执行任何出击`。
  ⚠️ 整串「空中出击」（第 32 轮试行面板名）**已作废**——已入 `BANNED`（**整串精确匹配**，不误伤含「出击」的译文）
  ＋**校验 5 面板名锁定**（行 406 必须＝`M - 空中任务`；整串黑名单抓不到 `M - xxx` 这类带前缀的）。
  ⚠️⚠️ **两条教训**：① **论证充分 ≠ 应采纳**（无先例可循的命名，先给 2–3 个候选让用户挑）；
  ② **用户说「改成 X」时先确认范围**（全部出现 vs 只改被指出的那处）——我只改面板名却把 13 处全回退，错了。
- **`Air Defense` 故意分译**：部队数值＝**对空防御**（配「对地防御」）｜兵种类·战报＝**防空**（位置语义不同，不强行统一）。
- **`Air Transport` 故意分译**：图标条按钮＝**空运**（动作）｜兵种类＝**空中运输**（配 地面运输/海上运输）。
- **装备名后缀统一**：`X AT`→**反坦克**｜`X Screen`→**掩护**｜`X Scout`→**侦察**。
- **北约代号一律意译**（不用无出处音译）：`SA-6 Gainful`＝**SA-6 有利**（❌根弗）· `SA-9 Gaskin`＝灯笼裤 ·
  `SA-8`＝壁虎 · `SA-10`＝轰鸣 · `SA-11`＝牛虻 · `SA-13`＝金花鼠 · `SA-17`＝灰熊；
  `Metis`＝混血儿（俄语本义）· `Shorland`＝肖兰。
- 生成链：GUI＝`gen_gui030_zh.py`（1-based 行号表 → 产出 `testbed\Gui030.zh.txt` 后**手工拷入**游戏）；
  装备＝`Equip30-map.tsv`（原文整串为键）＋ `gen_peg_text.py Equip30 [deploy]`。
- 术语表 `peg\research\ui-glossary.tsv`（含禁用黑名单；生成器会扫描拦截）。

**文风总纲**（全文 `peg\research\各国军语风格口径.md`）：**先判「文体」再定「语域」**——
PeG 简报**默认是「叙事简报体」（平实叙事），不是命令体**（第 18 轮「一律作战命令体」＝过度军事化）。
**原文限制译文的军事化程度；原文有比喻就照译比喻。**
文风基准＝**§五① 用户定稿**（生动平实的叙事：意象生动 · 节奏自然 · 用词有力 · 破折号承因果 · 专名后补通行译名）；
**「意象成链」**：原文一组连贯意象 ⇒ 译文一组互相呼应的词（拆散链即失败）。
诊断表 **A 机翻味 / B AI 文言腔 / C 过度军事化** 三组。
⚠️ 范本须**与作品时代匹配**：1979 后语料（`1979后中国军事文书范本.md`）**仅用于命令/战报两格**；
⚠️ 禁用台湾 1990s「民国感」词（`國力`/`佔領`/`武裝攻擊`/`前進觀測官`/`光榮勝利`）。
⚠️ 括注规则：简报中**地名/人名**一律 `译名(原文)`（半角）；`_m`/`_u` 不加。

**官方繁中版考古（第 19 轮）**：PeG **确有官方繁体中文版**＝**《解放軍之怒》**
（1999 台湾**名宇**中文化，`PEOPLES.EXE` 基于 PeG **1.0**，含自製「台海擴充包」）。
译法分歧：`Prestige→國力`（我作「威望」）· `Overrun→佔領` · `Hard/Soft→武裝/非武裝攻擊` · `前進觀測官`；
装备＝型号＋绰号（与我们一致）。⚠️ 中文版**新增「中華民國特種部隊」**、删「解放台灣人民」的「人民」
—— **在地代理改写辱华设定的一手材料**（用户研究主题）。
全文 `peg\research\官方繁中版《解放軍之怒》译法考.md`；⚠️ archive.org 被沙箱拦截，**未能下载取证**。

**OCR 手段（本机可用）**：模型读不了图时用 PowerShell + `Windows.Media.Ocr`
（`C:\Users\Administrator\ocr_shots.ps1` → `ocr_out.txt`），可提取截图中英文字。

**用途**：**仅用户个人研究「西方游戏文化渗透史」，不对外发布**；只做语言转换、**不改原文世界观**（保真优先）。
工具链原则：译法（`peg\research\*-map.tsv`）/ 逻辑（`work\peg\gen_*.py`）分离。

---

# B. PeG-WW2 明细（原 §一之二）

## 一之二、PeG-WW2（**三层已部署** · 2026-10-11 深夜收官）

**对象**：`D:\Program Files\PeG-WW2` = **PeG-WW2 2.7**（*People's General* 二战 MOD，Redball 2005）。
**用途同前作**（西方游戏文化渗透史研究对象）；**仅个人研究，不对外发布**。
**归档**：[`pegww2\README.md`](../pegww2/README.md) · **评估**：`docs\40` · 脚本 `work\pegww2\` · 备份 `pegww2\testbed\backup\` ·
**场景层滚动账**：`pegww2\research\进度-场景层.md`。

**现状（2026-10-11 21:26 部署完成 · 已复算核验）**：
- **exe 层**：12 个 efile 全部打补丁（各 261 B；字集 / 字符类别表 / 代码页 / 日期 LCID），原版另存 `<名>.orig-backup`。
- **界面层**：5/5 全量中文化 —— `WW2Gui.txt` 604 · `WW2Misc.txt` 45 · `WW2Tips.TXT` 43 · `ww2-eqp.txt` 906 唯一串 · `WW2NAME.TXT` 400。
- **场景层**：**21,865 条唯一行全部译完**（空译 0）⇒ 成品 **3,777 文件 / 改动 47,049 行 / 五道校验 0 失败**，已部署。
- **复算核验（2026-10-11 复跑）**：`verify_deploy.py` 三方 sha 全绿（12 efile + 5 文本）；
  成品 vs 游戏目录 **3,777+2 逐文件 sha 全一致（0 不一致/0 缺失）**；
  `dup_check`（50 组命中）与「中文串残留英文」扫描**均无损** —— 命中项全为缩写/拼写变体或**有意保留**的
  军级罗马数字、海军前缀、部队代号、MOD 元数据（`Gameset:`/`Equipment:`/`PeGWW2 conversion:`）。
- **待办**：① **用户实机复测**（21:30 有启动痕迹 `PEOPLES.INT` 刷新，但**尚无新截图**）② `方法\` 经验总结（现为空目录）
  ③ 阶段 5 归档：可复用经验**上浮到技能**（`ssi-modgen-peg-localization` / `win-game-html-ui-localization`）。

⭐⭐⭐ **最大发现**：12 个 efile 与前作已成功的 `PeG030.exe` **同一构建**（`TimeDateStamp 903998521`）
⇒ 双字节补丁 **1:1 套用，无需重新逆向**。
**落点（FO）**：① `0x70CE4` iCharSet `00`→`86`；② `0xA938A–0xA9489` `_pctype`→`0x8040`；③ `0xA948C` `__mbcodepage` `1`→`936`；④ `0x7BE86` 日期 LCID→`B8 04 08 00`。
⚠️ **不打**前作已作废的两条（行终止表被 ② 取代；`0x46FF1C` 丢行补丁成品里并不存在）。

- **12 个 efile 硬编码 stem 完全一致**（`ww2gui/ww2misc/ww2name/ww2tips/ww2-eqp/ww2gen`）⇒ **改一次全部生效**。
- **`.scn` 本作偏移（不得照搬前作）**：`@11210`=地图名 · `@11329`=简报名 stem · `@11349`=位置标志 · `@0`=进列表（**79×0** / 569×1）· **`@4` 恒 0**。
- **词库复用率低**：既有 61,284 条词库对场景层**整串仅命中 24.8%**（真源最终来源：人工确认 11,564 · 词库 9,966 · PeG 334 · 原样保留 295）。
- **排除项**：`WW2gen.txt`（MOD 素材清单）· `DOCS\`（手册）· `CINE\`/`WAVS\`（媒体）。
- ⚠️ **环境事故**：旧 venv `…\.workbuddy\binaries\python\envs\default` **已失效** ⇒ 用 **`C:\Python314\python.exe`**；
  ⚠️ 本沙箱下 **PowerShell 管道/重定向包裹原生 exe 会 `Access is denied`** ⇒ 别包管道，让脚本自己写报告；
  ⚠️ **跑脚本前设 `PYTHONIOENCODING=utf-8; PYTHONUTF8=1`**，否则脚本里的 ✅/⭐ 撞 GBK 控制台编码直接崩。

**本项目 19 条踩坑（W1–W19）全文**：`pegww2\README.md` §踩坑档案。三条最值钱的：
- **W17 整串键控不能用于「同串多义」** —— 同一原文在不同文件需不同译文时必须走 **per-file 覆盖**（现 88 条），否则**静默误伤**别处正文。
- **W19 描述框来源双字段** —— `.SCN@11329`(stem) + `@11349`(位置标志) **必须同时核对**；字段与文件实际位置/拼写不符时引擎**不报错，直接回退**。
- **W11 HUD 是「元件拼装」不是整句** —— 判 bug 前先查该显示位由哪几行拼成。

**地名三维规则（阵营/年代）**（2026-10-13）：
- 真源 `glossary\layers\faction-places.tsv`（47 处）＋ `faction-ops.tsv`（18 处）——**「同一个地名怎么译，看地图年代 + 玩家扮演的势力」**（用户口径）。
- 审计器 `work\glossary\faction_place_audit.py`：场景文件 **3682**，判定视角 **3306（90%）**，⚠️ 未判定 **376（10%）**；
  年代可判只 **765（21%）**（⇒ **时代来源＝下一步真正瓶颈**，需逆向 `.scn` 日期字段）。
- 门侧**只报不判**：`work\glossary\faction_wire.py` ＋ `layer_gate.py` 的 `wire_brief()`；
  `GLOSSARY_NO_WIRE=1` 时门 stdout 逐字节回退到接线前 `41B7C27EAABBEBEBF140A4D9235F7B3E`。
- ⭐ **实测结论：修「层表键」对门的影响＝0 条** ⇒ 用户裁定**不做**（理论缺口，无收益）。
- 已闭环 2 处真阳性：`SCENARIO\RM_usvsruss6v.txt` 行1/行2「捷尔诺波尔」→**「塔尔诺波尔」**（德方视角；同族第 7 个漏网文件）。
  走 per-file 覆盖表，脚本 `work\glossary\fix_tarnopol_6v.py`（只写表）＋ `deploy_tarnopol_6v.py`（临时重建→比对→才落盘）。
- 详见 `docs\44`·`docs\45`·`docs\46`。

**地名收敛「采用新名」＋ 两作成品同步**（2026-10-13，`docs\47`＝评估 · `docs\48`＝执行记录）：
- 用户四项裁定：「1.采用新名。2.按部队本身属性分流。3.简报测按阵营方描述来统一。4.地图侧看预设是扮演哪方势力时，就使用对应势力地名写法。」
- ✅ **①已落盘**：12 组新名（Kuri 九里 · Morotsu 诸津 · Chio 千绪 · Naikawa 内川 · Burnoshevo 鲁斯科耶 ·
  Toro 塔路 · Chiwagai 奇瓦盖 · Okutai-gawa 奥库泰河 · Chingyong/Chinyong 进永 · Hatsutai 哈茨泰 ·
  Acroma 阿克罗玛 · Wolzskij/Volzhshiy 伏尔加斯基）。
  真源改了 2 张表共 **25 行**：`peg\research\scenario-map.tsv` 13 行（1076/1076 行数校验）·
  `pegww2\research\ww2-scn-map.tsv` 12 行（21874/21874）；执行器 `work\glossary\fix_name_converge.py`
  ——⭐ **必须按英文键整行替换，禁全局文本替换**（`库里` ⊂ `库里纳河`＝`Kurina River`，会误伤）。
- 重生成两作（**先建到临时目录 + 逐文件证明 `旧文.replace(旧名→新名) == 新文`**，不成立即停）：
  PeG **57/57**、WW2 **22/22** 差异全部可解释；部署 57 →`D:\Program Files\PeG`、22 →`D:\Program Files\PeG-WW2`；
  备份 `backup\before-name-converge\{peg-game,ww2-game,layers}`；回读 md5 全一致。
  执行器 `work\peg\regen_scn_name_converge.py` · `work\pegww2\regen_scn_name_converge.py`（`--promote`/`--deploy` 分步）。
- ⭐ **改完真源必须重跑层表链**：`ingest_layers.py --apply` → `converge_plan.py --apply` → `layer_gate.py`。
  门先报 ❌ 新增偏离 6 条（＝本作新名 vs 前作旧名的**合法**跨项目差异、尚未登记）⇒ converge 自动登记 **286 条**
  进 `scope-diff.tsv` ⇒ **门 ✅ 新增偏离 0 条**。（只有 6 条被拦 ⇒ 说明另 5 组已收敛。）
- 残留扫描（`work\_sync-audit\residual_scan.py`＋`verify_name_converge.py`；⚠️ **须 Python 解 GBK**，rg 搜中文假报）：
  真残留 **0**；`因杜库里`（PeG `Name030.txt:689`）· `库里洛夫卡`（WW2 9 处）是别的词，`初代` 那处是 `.wav` 二进制误命。
- ②③④ **尚未执行**（`docs\48` §九）：② 62 条「词库值==英文原文」按部队属性分流；
  ③ PeG 简报侧 9 处 A-HI（`suchan` 苏昌｜苏城 ×7 场景 · `amur river` 阿穆尔河｜黑龙江）；
  ④ WW2 地图名栏自身多值 36 组按「预设扮演哪方」取值。

**按场景定点覆盖层 ＋ 词库第三真源入库**（2026-10-15，`docs\49`）：
- 用户指令（`m01214`）：「加一层按场景定点覆盖，2.补齐。3.按预设扮演势力弄地名。」
- ✅ **①机制**：真源 `glossary\layers\scn-place-override.tsv`（列 `en|项目|场景词干|译名|依据`，
  `en` 可为映射表短名或长段表整行原文）⇒ 接线 `layer_gate.load_overrides()`（第 3 列）
  ＋ 两个生成器（`work\peg\gen_scn_zh.py`、`work\pegww2\gen_scn.py` 各加
  `OVRFILE/SUFFIX/STEM_TAIL/stem_of/load_scn_override`）。⭐ **空表回归：两作重建逐字节 0 变化** ⇒ 纯加性。
  ⚠️ 坑：`work\peg\regen_scn_name_converge.py:67` 曾漏传 `ovr` ⇒ 新层**静默失效**；新增层必须逐个入口接线。
- ✅ **②补齐真因**：`pegww2\research\_scn-file-overrides.tsv` 是**第三个译法真源**
  （**per-file 行号级覆盖 > 整串精确匹配 > 原样保留**），而 `work\glossary\ingest_layers.py` **从不读它**
  ⇒ 词库只看到映射表的 `Breda -> Breda`，把「映射表保留英文」误当最终译法。
  覆盖表 602 行 / 280 文件 / 283 键，**282 键与映射表同键异值**、12 键同键多译。
  keep 桶（词库值==英文）514 条中，成品 `_m.txt` 真出现 97 键：**58 键实由覆盖表翻译**、39 键是真·番号缩写保留英文。
- ✅ **②落盘**：`ingest_layers.py` 新增来源 ②e-bis，**scope 用 `PEGWW2_SCN_OVR`**（不是 `PEGWW2_SCN`——
  两者是不同优先级层，并进同一 scope 会被门判「同 scope 多译」**假冲突 108 条**）；
  只收「映射表没给中文」的行 ⇒ **收 109 键**（`common-glossary.tsv` 37285→37395 行）；
  108 条政策对自动登记进 `override.tsv`（该表是派生物，登记写在脚本 `reg` 列表）⇒ **门 ✅ 新增偏离 0**；
  层表键 `(en,层,scope)` **没有文件维度** ⇒ 202 行（12 键同键多译＝28 行 · 映射表另有中文＝174 行）
  只落 `glossary\evidence\ingest-scn-ovr.tsv`；备份 `backup\before-scn-ovr-ingest\layers`。
- ⚠️ **③ backlog（未批量改）**：证据表 174 行是「**番号内嵌地名按势力分叉**」
  （`131 Ftr [Poznan]` 覆盖表 `[波森]` vs 映射表 `[波兹南]`；`1 R/HG D` `第1团/赫尔曼·戈林师` vs `第1团/HG师`）
  ——正是「按预设扮演势力弄地名」，只是藏在番号里；需先按场景词干判阵营再决定走定点覆盖还是拆出地名。
- ⚠️ **教训**：生成器「查表 → 写盘」应记录每行**命中来源**（哪张表/哪一行），否则「**成品对而真源错**」
  的倒挂极难发现（`docs\47` 就把它误判成「词库滞后于成品」，实为第三真源未入库）。

**`cat` 误标治理 ＋ per-file 覆盖表并入词库**（2026-10-15，`docs\50`）：
- 用户裁定（`m01713`，逐字）：「**1，需要治理。2，并入。**」
- ✅ **① 治理 `PLACE` 误标**：根因＝`build_glossary.py` 的 `cat` 是启发式
  （`cat_of_name()` 命中不了部队后缀就**默认 `PLACE`**；`collect_xscn()` 只按「是否 0 号组」二分），
  实测 **752 条 / 7120（10.6%）**，746 条在 `EFILE_OLGWW2`（`HG div -> 赫尔曼·戈林师` 被判地名）。
  新规则模块 **`work\glossary\cat_fix_rules.py`**：`unwrap()` 剥包裹引号/括号 → 城市·地貌护栏与
  人名地名护栏（列宁格勒/斯大林格勒…）→ 舰名（中文「…号」收尾不含数字，或英文大写海军前缀）
  → 具名装备白名单 → 部队后缀＋佐证 ⇒ `recat()`。
  挂载点：`build_glossary.py` 的 **`merge()` 末尾后处理**（只改 `cat` 列，不动 `(en,scope)` 主键与 `zh`）。
  落盘：主库 `PLACE 7120 -> 6216`（**904 条**：→UNIT 698 · →EQUIP 206），其余 4 个产出**逐字节未变**，
  层表只动 cat（+note 回声），**门 ✅ 新增偏离 0**；留痕 `work\out\glossary-cat-fix.tsv`。
  ⚠️ 教训：**规则改动必须抽看命中样本**——`NAVAL_EN` 早期不区分大小写的 `orp?` 会命中散文裸词 `or`
  （把 `Efile: OLGWW2 … or higher` 判成 EQUIP），只看计数发现不了。
- ✅ **② 并入**：取消 ②e-bis 里「**映射表另有中文**」这条排除（174 行）——映射表（`PEGWW2_SCN`）与
  per-file 覆盖表（`PEGWW2_SCN_OVR`）是**两个优先级层**，去重键 `(en,层,scope)` 不冲突，可并存。
  ⚠️ **两侧中文都要登记** `override.tsv`：只登记覆盖表那侧 ⇒ 门立刻报 `跨层多译 84 + 通用层内多译 74`。
  结果：按场景覆盖**收 109 -> 271 键**，证据表 **202 -> 28 行**，门 **555 条偏离全部已登记 / 新增 0 ✅**。
- ⚠️ **残留**：28 行「同键多译」（同一英文在**不同文件**取值不同，如 `Avalanche`/`Dessau`）——
  层表主键**没有文件维度**，压平必造假 ⇒ 仍只落证据表；要表达只能走 `scn-place-override.tsv`（按场景词干）。
- ⚠️ **教训**：新增一层/一条排除规则，牵动「**排除规则 → 登记 → 写入**」三处，必须同时改，否则静默失效。
- ✅ **下游回归**（`cat` 是下游判据，故全仓 `"PLACE"` 消费点逐个查过，`docs\50` §七）：
  `faction_wire.py:51-52` 准入收紧（**改善**，`Crusader` 那类假命中的根因）· `audit_authority.py:176/218` 无影响 ·
  `audit_authority.py:207` `lay = 'txt' if cat in ('PLACE','TEXT') else 'xscn'` **规则换档** · `ingest_layers.py:285` 无影响。
  实测（探针 `work\_sync-audit\cmp_authority.py`，同基准只换库）：问题 **300 → 306**（A未译残留 **160 → 160 不变**；
  差异全在 B/E 的层判据换档：新进 11 · 退出 5）⇒ **没有制造新问题、也没有掩盖旧问题**。
  `authority-baseline.tsv` 的 284 条是**权威译名基准**（供 F 权威偏离比对），不是问题数基线，无需更新。

**残留专名定名（95 条候选 · 146 处）**（2026-10-15，`docs\51`）：
- 用户批示（`m02306`，逐字）：「**好的，定名补进词库**」。
- 对象＝`docs\50` §八 A类六桶里的 **③ 番号/编制 28 条 ＋ ⑥ 外语番号整段 67 条**（`residual-names-todo.tsv`）。
  **排除不动**：具名装备 7（`SS Panther D`/`Wirbelwind`/`Maultier`…）· 署名/URL 元数据 19 · `not used` 9。
- 规则表 **`work\_sync-audit\naming.tsv`**（键＝残留英文，**95 行**，按 `len(old)` 倒序套用）；
  执行器 **`work\_sync-audit\apply_naming.py`**（默认 dry-run）三落点：
  `.txt`（`SCENARIO\` **与** `TEXT-ZH\SCENARIO\` 两层）· `.xscn`（**字节级改写槽值并同步 2 字节长度前缀**）·
  真源 `work\efile-nashornpbem\olgww2-glossary.tsv`（只改 `dst`，PRI 0 参与投票）；备份 `backup\before-naming\`。
- 命名口径要点：`Habforce 哈巴尼亚部队` · `2 African D 2南非师` · `A.Highlander 阿盖尔高地` ·
  `SS-Verfugungs-Division 党卫军特别机动师` · `Gen. Defontaine 德丰坦将军` · `Bru.-Btl. 架桥营` ·
  `Imperiali 因佩里亚利`（向同串 `.txt` 已全译写法对齐）· `Folgore “闪电”` · `FET 长枪党` · `Mehal-la 梅哈利拉塔博尔` ·
  日舰 `Asagumo/Harusame/Kawakaze/Minegumo/Murasame/Samidare/Umikaze → 朝云/春雨/江风/峰云/村雨/五月雨/海风` ·
  `第2/第9驱逐舰 → 第2/第9驱逐队` · `[Okinawa] 冲绳` · `Balikpapan部队 巴厘巴板部队` ·
  西班牙内战按「人名/地名＋第N营」译（`Octubre No.46 → 第46“十月”营`、`Cen.Alava → 阿拉瓦百人队`）。
- ✅ **结果**：两轮共改 **146 处**（29 `.xscn` ＋ 2 真源行）；`verify_naming.py` 242 个 `.xscn` **槽键序列全一致 0 异常**；
  槽位超限 **0**；权威核对 **问题 306 → 212（A未译残留 160 → 66）**，B12/E134 持平；
  门 **✅ 新增偏离 0**（定名后先报 22 条「通用层内多译」，经 `converge_plan.py --apply` 登记 ⇒ `override 627→649`）。
- ⚠️ **22 条跨作偏离的真身**＝PeGWW2 映射表 `pegww2\research\ww2-scn-map.tsv` 同键仍英文（如 `第51团/第2 African D`）——
  本次**只登记未改写**（不越权动另一作源表），是否铺同一套定名**待用户裁定**。
- ⚠️ **教训**：`Get-ChildItem -Include` 在**无 `-Recurse` 且路径无通配符**时**静默返回 0 个**
  （本次因此漏备份 5 个词库产出；可靠 `backup\before-naming\` 的 30 个源文件复算还原）。
- ⚠️ **教训**：定名会拉动 `E标点规范`（一轮 134 → 140，汉字间多空格）——**改完必须复跑权威核对，不能只看 A 指标**。
- ⚠️ 定名前观察到**既有可疑统一译法**（本轮未动，仅备案）：西班牙 `Bon.`（Batallón）一律译作 `第76营`。

### 词库更新铺设到 PeG 及 PeG-WW2（2026-10-15，`docs\52`）

- 用户逐字指令 `m02542`：「很好，把这些词库更新后的内容更新到Peg及peg-ww2中」。
- 全仓扫描 `work\_sync-audit\scan_residue_all.py`（→ `residue-all-hits.tsv` 5296 行）：
  **PeG 侧零命中**（`D:\Program Files\PeG` · `peg\research` · `EFILE_OPENPEG` 各 0）——95 条定名全是二战期术语，铺 PeG 无对象；
  真正还有对象的是**另外 7 个 efile**：`PzLIGA 85` · `GCE 78` · `KAISER 16` · `LXF 3` · `ROI 2` · `BASEKORP 2` · `OPENAK 1`（**是否一并铺设待用户裁定**）。
- 执行器 **`work\_sync-audit\apply_naming_peg.py`**（默认 dry-run）：落点＝`pegww2\research\ww2-scn-map.tsv` 列≥1 ·
  `_scn-fill-prose-r13-01.tsv` 列≥1 · `EFILE_OLGWW2` 的 `SCENARIO`/`TEXT-ZH\SCENARIO` `.txt` · `SCENARIO\*.xscn` 字节级；
  ⚠️ `TEXT-ZH\SCENARIO\*.xscn` 是**英文原文死镜像**，一律不动；双语注 `译名(原文)` 跳过；备份 `backup\before-naming-peg\`。
- ⭐ **判据修正**（否则漏 9 行）：原判据「连续 ≥2 汉字」会把 `第52营/第1 African D` 这种汉字被数字隔开的单元格漏掉；
  改为 **`ZH_SET`＝词库 zh 列的全部汉字**，文本含其中任一字即算中文侧（同时仍挡住 `Caballer韆 FET` 这类 cp1252 假汉字行）。
  命中而**无连续汉字**的明细标 `LOOSE-` 供复核（本次 9 处全部正确）。
- ✅ **结果**：改 10 个文件（map 24 行 · `.txt` 4 行 · `.xscn` 10 槽）；词库重建 23475 条（**-1 已解释**：
  `You better resign … "friterie/frituur".` 原按 `/` 拆成两行，中文侧变整句后不再拆 ⇒ 正确收敛）；
  层表 `COMMON 37470/SERIES 183/SCOPE 10694` · **漂移 218→196** · 槽位超限 `scn20B 0` · **门 ✅ 新增偏离 0（555 全已登记）** ·
  权威核对 **212→211**（A 66→65，B12/E134 持平）。
- 🔧 顺手修 2 个 cat 回退：定名二轮把 `Tabor Mehal-la→梅哈利拉塔博尔`、`Tabor Ifni→伊夫尼塔博尔` 后末字不再含部队词，
  cat 掉回 `PLACE` ⇒ 在 `cat_fix_rules.py` 加 `UNIT_EN_EXACT = {"tabor mehal-la", "tabor ifni"}` 钉为 `UNIT`；
  `Tabor-hegy (450 m)→塔博尔山` 仍正确为 `PLACE`。
- ⚠️ **遗留待裁定**：① `African D` 家族 `第N非洲师` 12 键 vs `第N南非师` 6 键（史实应为**南非师**）；
  ② `Saharian Grouping` `撒哈拉战斗群` 1 vs `撒哈拉集群` 4；③ `Imperiali D/XXX/V` `第5集团军` 1 vs `第5军` 2；
  ④ `Raemcke` `拉姆克旅`（.txt）vs `雷姆克旅`（.xscn ＋散文双语注）。本次只做「按词库逐键对齐」，家族级分歧未动。
- 🔴 **新查出系统性误译：`Bon.` → `第76营`**（`docs\52` §六-3，取证脚本 `work\_sync-audit\probe_bon76.py`）：
  西班牙 `Bon.`（Batallón）**无数字时**被填进凭空的「76」且词干常留拉丁（`Bon. Thaelmann→第76营 台尔曼`，
  而词库 .txt 层正确写法是 `台尔曼营`）；英文**带数字**时反而正确（`80 Bon.→第80营` · `78 Bon.→第78营`）。
  实测 GCN0/GCN2/GCN3/GCN4 **25 槽**（词库落成 20 个 `…/[地名]` 键）。**修法＝用 .txt 层正确写法逐槽改写，待用户裁定**。


---

# C. PeG 高分辨率/宽屏线全文（原 §五）

## 五、PeG 高分辨率线（2026-10-13 重开）

1. **分支工作区 `D:\DSH\军事游戏汉化-1` 已删除** ⇒ 分辨率实验线的全部脚本（`patch_resolution.py` v4、`probe_res5–32.py`、`verify_resolution_patch.py`）与日志（`out\res_constants.txt`、`out\probe_res*.txt`、`out\shot-v3*.png`）**全盘搜不到**，`backup\` 里也没有快照。
2. **唯一幸存产物**：`D:\Program Files\PeG-1\PeG030res.exe`（734720 B，2026-10-13 01:12:02）＝ v4 版 1024×768 副本。
3. ⭐ **可逆**：`D:\Program Files\PeG\PeG030.exe` 与 `PeG-1\PeG030.exe` **逐字节相同**（MD5 `C462E897B3AA1C384870C857CE9E01DF`）⇒ **`PeG030.exe` ↔ `PeG030res.exe` 的 diff 就是 v1–v4 全部改动点**，patch 脚本可由 diff 反推重建。
4. **用户已拍板**：目标＝**引擎原生高分辨率「一屏看得更多」**（放弃外部放大与换引擎两条路）；S1/S2 已完成，2026-10-13 又拍板「**先做 S3/v5**」「**先不管图标，先让布局正确**」「**两版都做，我跑一版给你反馈**」。
5. **S1 完成（自证通过）**：`work\peg\diff_res_canvas.py` 由母本↔v4 产物 diff 反推，**生成** `work\peg\patch_resolution.py`（259 站点：.text 52 / .data 207）；重放与 v4 产物 `PeG-1\PeG030res.exe` **逐字节一致**（md5 `2107b73bbfd4213719b622a1a9d4c6ad`）。中文补丁三处（charset FO `0x070CE3`、`__mbcodepage` FO `0x0A948C`、LCID FO `0x07BE86`）每次构建后复核。
6. ⭐ **S2 完成（根因已定位）**：花屏**不是** stride/pitch（该假设被静态证据否定），而是 **v4 在同一基本块里把 `cmp [0x663388],0x320`／`mov [0x663388],0x320` 改成了 1024，却漏掉真正参与运算的 `mov eax,0x320`（0x44C730 等 6 处）** ⇒ 地图视口 Blt 矩形仍按 800×600 算，右侧 224 px／下侧 168 px 从未被写 ⇒ 显示未初始化表面内存。共 **43 处**仍带旧分辨率的漏点已按语义分组（视口裁剪 6／矩形对 10／屏幕边框 2／坐标夹取 7／尺寸全局 4／其它 6）。
7. **同类调研与路线选择** ⇒ [`docs\53-PeG高分辨率支持-现状抢救与同类方案调研.md`](docs/53-PeG高分辨率支持-现状抢救与同类方案调研.md)；**S1/S2 全部细节与 43 处漏点地址表** ⇒ [`docs\54-PeG高分辨率-S1补丁重建与S2花屏根因.md`](docs/54-PeG高分辨率-S1补丁重建与S2花屏根因.md)。
8. ⭐ **v4 已实机取证**（2026-10-13 用户亲手跑 `PeG-1\PeG030res.exe` 并截图，md5 核对＝`2107B73B…`）：**地图侧成功** —— 内容区 x 888..1016 已是地形，1024 宽铺满，「看得多」成立；**界面侧失败** —— 右侧工具列由 v3 的 26 px 方块（内容 x 762..787）变成 **186 px 横向拉伸胶囊（内容 x 800..985）**，而 v4 补过的按钮记录指向 986..1011，那里**什么都没画**；底栏记录已 +168 却纹丝不动。⇒ [`docs\55-PeG高分辨率-v4实机取证与运行时重算根因.md`](docs/55-PeG高分辨率-v4实机取证与运行时重算根因.md)
9. ⛔ **教训**：该线在 `-1` 的 `MEMORY.md` 与 `PeG汉化经验总结.md` 里**一行都没写**，知识只活在脚本 docstring/日志里，副本一删即不可复现 ⇒ **重要实验线必须当场落档**。
10. ⭐ **界面布局由代码重算（面板链已找到）**：`0x41C4D4` / `0x41C4DB` 把面板矩形写成 `{right=799, bottom=571}`，`0x41C4EB` 宽 180 ⇒ `left = right − 180 + 1 = 620`；紧随的循环（`0x41C528`，idx 0x20..0x27）用 `rec.x − 620`、`rec.y − 22` 后调 `0x425407` 绘制 ⇒ **控件屏幕位置 = 面板基准 + 记录相对坐标**。v4 只做了 `.data` 记录的 `x += 224`（163 处）、**没动这条链** ⇒ 「记录位移了、基准没动」，很可能双重错位。屏幕边框 `0x44C5CC`(570) / `0x44C5D1`(796) 与视口裁剪三组 `0x44C730` / `0x44C777` / `0x44C869` / `0x44C8B0` / `0x44CC67` / `0x44CCAE`（800/600）同样是 v4 漏点。
11. ⭐ **v5 三个诊断变体已生成（等用户实机跑一个）**：生成器 `work\peg\build_v5.py`（新；默认干跑，`--apply` 才落盘；逐站内容断言 + 回读校验 + 中文补丁复核）。产物在 `work\peg\out\`，并已复制到 `D:\Program Files\PeG-1\`：
    - `PeG030-v5a.exe` ＝ v4 + 面板矩形 2 处（571→740、799→1023），md5 `8b03c59b638a9020557bcbd0a67bbbac`
    - `PeG030-v5b.exe` ＝ v4 + 面板/边框/裁剪共 10 处，md5 `0d38ae6222d3b0dff30298ea3072c69f`
    - `PeG030-v5c.exe` ＝ **母本** + `.text` 52 + 除 `dx` 外 `.data` 44 + 同批代码 10 处（共 106 站点）＝「代码驱动布局、记录不做横向位移」这条更自洽的假设，md5 `4657e47d9170aebf586fc52730e0a1f8`
    ⚠ 面板 bottom/right 的 **imm32 地址是 `0x41C4D7` / `0x41C4DE`**（指令地址 `0x41C4D4`/`0x41C4DB` + 3），别拿指令地址当补丁地址。细节与「怎么读结果」⇒ [`docs\56-PeG高分辨率-v5变体（代码驱动布局验证版）.md`](docs/56-PeG高分辨率-v5变体（代码驱动布局验证版）.md)
12. **下一步**：用户实机跑一个 v5 变体（建议 v5c）并截图 ⇒ 判定「代码驱动布局」是否成立；成立则 v5c 即正确架构，余下是图标/细节；若工具列毫无变化，则需继续找工具列真正的绘制循环（v4 里画在内容 x 800..985、周期 36 的那一列仍未定位）。实机试跑与截图必须由用户执行（我方严禁自行启动游戏）。
13. ⭐ **v5a/b/c 已实机验证（2026-10-13 用户跑三版并附图）**，实测（`probe_btn.py` 找绿框连续段，内容坐标）：v3 基线＝**762..787**（26 宽清晰方块）｜v4＝**800..985**（186 宽拉伸带）｜**v5a＝与 v4 同型**（⇒ 面板/边框/裁剪那 10 处代码补丁**对工具列毫无影响**）｜v5b＝更差（左边缘消失、420 行无绿框）｜**v5c＝762..787，与 v3 逐像素一致**（⇒ **拉伸由 v4 那 14 个按钮记录字段 `x`/`right` +224 直接造成**，机制最可能是 pg-cht 记的「dst/src 共用同一条 RECT」陷阱）。地图在 v4/v5a/v5b/v5c 四版**都铺满 ~1016** ✓。另：底栏**不是记录驱动** —— 字节核对确认 v4 把 `0x4A24F0` 改成 `y=744/right=1014`（`20 18 0A 00 E8 02 F6 03 FA 02`）而画面底栏纹丝不动 ⇒ 靠改记录让底栏下移行不通。
14. **v5c 是目前最佳基线**（地图铺满 1024 + 界面元件形状与原版一致；待解决：工具列仍停在原 x 762..787、底栏仍停原 y）。新产物 **`PeG-1\PeG030-v5d.exe`**（md5 `735a08d67a7cf95b4089d7f3678e62e6`，120 站点）＝ v5c + 只把那 7 条按钮记录的 x/right +224，用来隔离「单条记录位移是否就触发拉伸」。判读与后续 RE 目标 ⇒ [`docs\56-PeG高分辨率-v5变体（代码驱动布局验证版）.md`](docs/56-PeG高分辨率-v5变体（代码驱动布局验证版）.md) §六。
15. ⭐ **v5d 判读（隔离实验，用户已跑）＝`0x490494` 那 7 条记录只是「点击命中区」**：v5d（＝v5c＋只把这 7 条 `x`/`right` +224）的刀具列与 v3/v5c **逐像素一致**（762..787），改记录不挪画面。**真正被画出来的刀具列＝`0x4A22F8` 起的 13 条记录（组6）**〔勘误 2026-10-13：此处原写 `0x4A21B0`（组4），经 v7a 实测更正〕（`flags=0x1045, x=762, right=787, y=41/77/113/149/185/221/257/293/329/365/401/437`、527，步长 0x24，`bottom=y+25`）：v4/v5a/v6a 里它们已被改成 `x=986/right=1011`，v5c/v5d 里仍是 `762/787`。
16. ⭐ **界面绘制链**：`0x4235E5(rect, ctrl, index, dx, dy)`（187 处调用）算出 `dst = (rect.left+dx, rect.top+dy)` 并要求 `rect.surface==[0x676904]`；四个 rect 结构（`0x676980`/`0x675540`/`0x686408`/`0x65A9B8`）都在 `.data` 的 **BSS 段（VA ≥ ~0x4AF400，文件里没有初值）** ⇒ 运行时构造，这是「改文件里的记录搬不动界面」的结构性原因。路径 A `0x41D0AC` 把 dst 恒钉在 `(620,22)`（`dx=0x26C−(rec.x−2)`）；路径 B `0x41D290` 用 **`0x676980.left + rec.x`** ⇒ 决定位置的是运行时算出的面板左缘。**`find_imm.py 0x26c` 全 `.text` 恰好 4 处**（`0x41C567` / `0x41D11E` / `0x460372` / `0x4710A2`）＝面板左缘基准 620；**762/787/212 在 `.text` 0 命中**。
17. ⭐ **v6 已生成（等用户实机跑）**：`work\peg\patch_v6_panelref.py`（默认干跑；4 处 620→844，`6c 02 00 00`→`4c 03 00 00`）⇒ `PeG-1\PeG030-v6a.exe`（＝v5a＋4 处，md5 `fba578bc315c53871dfaf64e863f23f7`）与 `PeG-1\PeG030-v6b.exe`（＝v5b＋4 处，md5 `f82aaac6daf2d5cd0997d178dbf727be`）；v6a 与 v5a 的逐字节 diff **恰好 8 字节**。**期望：刀具列整齐出现在内容 x 986..1011（26 px）**。细节与判读 ⇒ [`docs\57-PeG高分辨率-v6面板基准620到844.md`](docs/57-PeG高分辨率-v6面板基准620到844.md)。
18. ⛔ **v6 实测＝毫无变化**（v6a 的刀具列与 v5a **逐段相同**；v6b 与 v5b 同型）⇒ **620→844 不是病根**。**教训（实验设计）**：若绘制位置 = `面板左缘 + (记录x − 基准)`，那么把「面板左缘」与「基准」**同时** +224 是**恒等变换** ⇒ v6a 必然与 v5a 逐像素相同，等于空转；**改一处、留一处**才有信息量。
19. ⭐ **控件数组是一组平铺在 .data 的定长数组**（步长 36）：`0x490470`（命中测试用，索引 0..39，`0x43FE70` 设当前数组指针 `[0x4cce2c]`）· **`0x4A22F8`（＝画面上那 12 条 36 步长带的 y 序列 41/77/113/…/437，全文件被引用 35 次，是地图屏刀具列的数组）** · `0x4A2068` · `0x4A21B0` · `0x4A8648` · `0x494220` 等（各画面一套）。`push <数组基址>; call 0x440794` = 控件字段 setter（`0x4484xx` 段在做 `cmp ecx,0xc` 的 0..12 遍历＝13 个按钮初始化；`0x448556`/`0x44862A` 运行时改 `[0x4a248e]=0x62/0x4d` 图标索引）⇒ **几何来自 .data，图标/状态来自代码**。新增工具 `work\peg\find_calls.py`（按目标 VA 找 call 点 + 上下文）。
20. **v7 二分实验已生成（等用户跑）**：`work\peg\patch_v7_bisect.py`（基点 v5c）⇒ `PeG-1\PeG030-v7a.exe`（v5c+组6，md5 `f7b611c935fc9f34365e157cb2ec6b37`）· `PeG030-v7b.exe`（v5c+组4/5，md5 `403e063abf8c521b6f79e3e0876044d5`）· `PeG030-v7c.exe`（v5c+组2/3/10，md5 `5384d8692a10b1020ff625892947049f`）。**判读：哪个变体把刀具列变成 800..985 的拉伸带，就锁定它。** 若都不花，则责任在组1/7/8/9/11 或「组合效应」。
21. ⭐ **v7 实测（用户跑三版，2026-10-13）⇒ 画面上那一列刀具＝组6 `0x4A22F8`**：v7a（＝v5c＋组6 的 13 条记录 x/right +224）**把刀具列拉成 800..9xx 的横向拉伸带**（y=420 行：800..933+935..941）；v7b（组4+5 `0x4A2068`/`0x4A21B0`）与 v7c（组2/3/10 `0x494220`/`0x4949C8`/`0x4A8648`）刀具列**仍 762..787 清晰**（但地图右侧出现大片未绘制黑区）⇒ 只有改组6 才能让「画出来的列」动。
22. ⭐ **绘制公式（handler `0x44ACDA`，静态度量）**：`rec = [0x4cce2c] + idx*0x24`；rect = `{x=rec+2, y=rec+4−1, right=rec+6+1, bottom=rec+8+1, surface=[0x676904]}`；再调 5 参数助手 `0x4235E5(rect*, ctrl=0x663410, mode=1, dx, dy)`，其中 **`dx = 0x2EF(751) − rec.x`、`dy = 0x16(22) − (rec.y − 1)`**（见 `0x44AD7E` / `0x44ADA5`）。母本 rec.x=762 ⇒ dx=−11；v4/v7a 把 rec.x 改成 986 而锚点仍 751 ⇒ dx=−235 ⇒ 助手拿越界相对偏移取样 ⇒ **这就是 186 px 拉伸带的直接来源**。全 `.text` 里 751 恰 5 处：`mov edx,0x2ef`×2（`0x44AD7E`/`0x44ADA5`）＋`push 0x2ef`×3（`0x43AA47`/`0x448849`/`0x448940`，后两处紧跟 `push 0x16`）。
23. ⭐ **v8 已生成（等用户实机跑）**：`work\peg\patch_v8_anchor.py`（基点 `work\peg\out\v7a.exe`，把锚点 751→975＝751+224）。`D:\Program Files\PeG-1\PeG030-v8a.exe`（仅 2 处 `mov edx,0x2ef`，md5 `8823d6d67dad59401963129e4242b20b`，diff 4 字节）· `PeG030-v8b.exe`（v8a＋3 处 `push 0x2ef`，md5 `c60c5727856776322c1a72f3fcf79596`，diff 10 字节）。**判读：v8a 若把刀具列摆成内容 x 986..1011 的 26 px 清晰方块 ⇒ 锚点假设成立，下一步 v9＝把「组6 记录 + 锚点」统一套到其余画面并处理底栏；若仍拉伸 ⇒ 751 是源图坐标而非位置锚点，必须正面读 `0x4235E5` 内部。** 细节 ⇒ [`docs\58-PeG高分辨率-工具列绘制公式与锚点751修正（v8）.md`](docs/58-PeG高分辨率-工具列绘制公式与锚点751修正（v8）.md)

24. ⭐ **换引擎路线成本已评估（2026-10-13，用户提问触发）** ⇒ [`docs\59-换引擎路线成本评估（PeG到OpenGen）.md`](docs/59-换引擎路线成本评估（PeG到OpenGen）.md)。要点：
    ① 引擎现成 ＝ `D:\OpenPG2` **Open General / OpenGen 26.3.30.0**（SDL2＋FreeType，本仓主线，`docs\00` 首行目标游戏；21 efile 已收官 11；`UI_Lang=strings-zh`、`Font1=simhei.ttf`）；**分辨率不是问题**（SDL2 窗口化引擎，`Settings.cfg` 无 SetDisplayMode 式死分辨率，只有窗口/缩放偏好）。
    ② **PeG 内容已被社区移植** ＝ `D:\OpenPG2\EFILE_OPENPEG\`（`efile.xml`：**OpenPeG v1.01C，作者 MG43**），163 文件：**19 个 `.xscn`**（＝1998 美方战役链 almaty1…volgograd1）＋ **战役树 `1uscamp.xcam`** ＋ 77 个场景 `.txt` ＋ `equip.txt`/`equip.xeqp` ＋ names/nations/fronts/weather/TerrainEx/colors/strings_efile ＋ PeG 风格 `OPENGUI`/`OPENDAT` 美术。⭐ 本机 `Settings.cfg` 的 Recent 里有 `EFILE_OPENPEG\SCENARIO\1uscamp.xcam` ⇒ **已经跑过**。
    ③ 汉化缺口：OPENPEG 现 **0%**（`docs\00` §三：`.xscn` 576 条 / 含汉字 0、`.txt` 77 个 / 0），但 `docs\30` B13 判为**「小」档**（唯一串：`.xscn` 417 / equip 672 / names 719 / nations 41 / strings 101 ＋ 77 个 `.txt`/31 KB）⇒ 估 **6–10 人日（1–2 周，含用户实机验收）**；位图层 OPENPEG 的 `hex_text.png`/`mouse_build`/`mouse_missions` 我们已经做过（`docs\07` L65、`docs\09` L101）。
    ④ **两个真缺口**：**(a) 体验不是原版引擎**（战斗公式/AI/UI 流程/战役结构都不同，OpenGen 是重实现）；**(b) 场景覆盖**——PeG 原版 `Scenario\` **206** ＋ `Userscen\` **7** ＝ **213 个 `.SCN`**、`MAP\` **436** 文件，而移植只有 19 个 ⇒ 其余 194 个要自写 `.SCN`/`.MAP → .xscn/.map` 转换器（`OpenSuite.exe` ＋ 我们已懂 PeG `.SCN` 结构，属中等工程）。
    ⑤ **建议**：先做**零风险 S0 审计**（用户把 `Settings.cfg` 的 `EFolder=efile_kaiser\` 改成 `efile_openpeg\` 跑一局并截图；我方静态出未汉化清单），拿到事实再决定是否切换；RE 路线的 A/B/C 三选项仍在桌面。**本评估未修改任何文件。**

25. ⭐ **路线三度转向：用户只要「引擎原生 16:9 宽屏 + 一屏更多地图」**。用户 m01250 原话：「这么搞没啥意义啊。。。。我扩大适配的分辨率，就是想看更多地图啊，而且能宽屏看地图，让游戏支持16：9的画面是最好的。」⇒ **显示层缩放（cnc-ddraw/dgVoodoo/Magpie 那一类）不是正解**（它只把 800×600 放大铺满，永远看不到更多地形）——cnc-ddraw 试验副本 `D:\Program Files\PeG-cnc\` 保留为备选，不再作为主线（其配置说明见该目录 `说明-cnc-ddraw测试.txt`；Svens 原 `ddraw.dll` 已改名 `ddraw.svens.dll.bak` 可随时还原）。
26. ⭐ **参数化构建器 `work\peg\patch_res_wh.py`（新，本轮）**：把 S1 反推的 259 站点表 `work\peg\out\res_diff_v4.tsv` 按 **任意 w×h** 重算并落盘。
    - 用法：`python patch_res_wh.py --w 1920 --h 1080 --out out\PeG030-1920x1080.exe [--apply]`；默认**干跑**；加 `--keep-dx` 则同时做控件记录位移（＝v4 配方，已知会拉伸工具列，默认跳过那 163 条 `dx`）。
    - 默认配方（＝**v5c 配方参数化**）：106 站点 ＝ `.text` 52 尺寸站点 ＋ 非 `dx` 的 `.data` 44 条 ＋ 代码侧 10 处；逐站点内容断言 ＋ 回读校验 ＋ 母本 md5 断言 ＋ 中文补丁三处复核。
    - 语义：`w/w-1/w-4`→新宽；`h/h-1/h-28/h-30`→新高；`dx/dy`→旧值+(新宽−800)/(新高−600)；代码侧 10 处 ＝ `0x41C4D7`(h−28) `0x41C4DE`(w−1) `0x44C5CD`(h−30) `0x44C5D2`(w−4) `0x44C731/0x44C86A/0x44CC68`(w) `0x44C778/0x44C8B1/0x44CCAF`(h)。
27. ⭐ **两版 16:9 原生产物已生成（等用户实机跑）**：
    - `D:\Program Files\PeG-1\PeG030-1920x1080.exe`，md5 `44ac5cfe5a5875aa5ef51efd3d1afcf4`（与母本差 212 字节 / 87 段）
    - `D:\Program Files\PeG-1\PeG030-1600x900.exe`，md5 `2c0369eb9aa3960e75c751bc72b6429d`
    - 字节核验：`0x41C4DE`= `7F 07`(1919=w−1)、`0x44C731`= `80 07`(1920=w)、`0x44C778`= `38 04`(1080=h)；中文补丁三处 OK。
    - ⚠ **已知局限（必须在交付说明里讲清）**：配方里**不含控件记录位移**，所以地图铺满 1920 宽，但工具列/底栏仍画在 800×600 的老坐标上（工具列 x 762..787）。**UI 重排仍未解决**（见第 21–23 条的 v8 结论）。
28. ⭐ **v8 实测判读（用户跑 v8a/v8b 并附图，`work\peg\out\shot-v8a.png`/`shot-v8b.png`）：锚点假设证伪。** `probe_btn.py`（内容坐标）：v8a（仅 2 处 `mov edx,0x2ef`→975）y=420 行＝**800..894（95 px）**、y=300＝800..813｜836..907；v8b（再改 3 处 `push 0x2ef`）＝**800..985（186 px，同 v7a）**。⇒ **拉伸带左缘恒在内容 x=800**，改锚点只让右端左右移动，一次也没落到 986..1011 ⇒ **751 是源图/裁剪坐标系里的量，不是位置锚点**；且 `mov`（2 处）与 `push`（3 处）语义**相反**（v8a 改善、v8b 还原）。
29. ⭐ **绘制链已读穿（静态确证）**：`handler 0x44ACDA(idx)` → `rect={x=rec.x, y=rec.y−1, right=rec.right+1, bottom=rec.bottom+1, surface=[0x676904]}`、`dx=751−rec.x`、`dy=22−(rec.y−1)` → `0x4235E5(rect, ctrl=0x663410, idx=1, dx, dy)` → `0x47E0A0(rect, ctrl, idx, dx, dy, flags=0x1008000, 0)`（flags＝DDBLT_WAIT|DDBLT_KEYSRC）→ 源面 ＝ `ctrl->[4]+idx*0x1c+0x18`；`0x47E050(ctrl,idx,&a,&b)` 取表项前两 dword；`0x47E4E0(rect,ctrl,&out,idx,dx,dy)` 用 dx/dy 做裁剪 ⇒ **`dst.left = rect.left + dx` 仅当 `dx ≥ 0`；`dx < 0` 时保持 `rect.left` 不动**（这是母本 dx=−11 仍画在 762 的原因），`dst.top = rect.top + dy`，再用 `rect.bottom+1` 夹下边 → `call [ecx+0x14]` ＝ **IDirectDrawSurface::Blt**（错误码分支 0x80004005/0x80004001/0x80070057/0x8876006E → 报错串 0x4ab9xx）→ `0x4231DF` 画绿框。
30. ⭐ **同类老游戏做法调研（GitHub/网搜）**：当前社区主流＝**运行期 DLL 注入 + 代码 hook 重算 FOV/HUD**（代表 [`alphayellow1/AlphaYellowWidescreenFixes`](https://github.com/alphayellow1/AlphaYellowWidescreenFixes)，工具链 Cheat Engine/x32dbg/Ghidra）；纯显示层方案（[cnc-ddraw](https://github.com/FunkyFr3sh/cnc-ddraw)、DDrawCompat、dgVoodoo2、DxWnd、Magpie）**拿不到更多地图**（DDrawCompat 自述 "There is no API conversion involved"）；真正拿到更大视口的案例几乎都走 **DLL hook 重算** 或 **源码移植**（DevilutionX/OpenRA/OpenXcom，以及本项目主线的 OpenGen/PG Forever）。结论已写入 [`docs\58-PeG高分辨率-工具列绘制公式与锚点751修正（v8）.md`](docs/58-PeG高分辨率-工具列绘制公式与锚点751修正（v8）.md) §九–§十二。


31. ⭐ **UI 绘制机制已读穿（本轮，母本未改）**：绘制漏斗 `0x4235E5(rect*, ctrl, index, dx, dy)` → `0x47E0A0(...)` → `0x47E4E0(rect,ctrl,&out,idx,dx,dy)` 构造/裁剪矩形 → `call [ecx+0x14]`＝**IDirectDrawSurface::Blt**；`dx/dy` 是**图集内源偏移**，`rect` 是**屏幕目标矩形**；`0x4235E5` 共 **187 个调用点**。控件记录表 `0x4A22F8`（16 条，步长 `0x24`，字段 `+0` 标志 / `+2` x / `+4` y / `+6` right / `+8` bottom / `+0x10` 绘制回调，多为 `0x44ACDA`）与 `0x490470`（40 条）；`0x440794(table,index,flag)` **只改标志位、不写坐标** ⇒ 记录里的 x/y/right/bottom 就是布局真值。
32. ⭐ **移动记录必须同步改源偏移常量**：`0x44ACDA(idx)` 里 `dx = 751(0x2ef) − rec.x`（`mov edx,0x2ef` @`0x44AD7E`）、`dy = 22(0x16) − (rec.y−1)`（`mov ecx,0x16` @`0x44AD75`；对应 push 版 @`0x44AD9C`/`0x44ADA5`）。**只挪记录不动这两处 ⇒ `751−x` 变负、源矩形反向越界 ⇒ Blt 拉出彩色带**（v4/v7a/v8a/v8b 四轮同症）。正确配方：记录 +Δ 时必须把 `0x2ef` 改成 `0x2ef+Δx`、`0x16` 改成 `0x16+Δy`。
33. ⭐ **引擎自带「缩放 + 居中」阶段**：`0x420030`（工具栏绘制前于 `0x44882A` 调用）用 `w=[0x498d44]−[0x498d3c]+1` 乘 `[0x686a90]`/`[0x64c700]`、高用其倒数，再 `sar eax,1` 居中，结果写入 `[0x6633e0]..[0x6633ec]`。两个尺度量运行期**累加**（`0x41f10f`/`0x41f118` 清零，`0x41f284`/`0x41f2a2` 累加，`0x41f3ee` 处 `+0x28` 且 `cmp edx,0x780`＝**1920**）。
34. ⭐ **`0x498d3c`/`0x498d40`/`0x498d44` 是运行期工作矩形，不是布局常量**：唯一写入者 `0x424D27`（函数 `~0x424CF0`：`[0x4af300]=[ebp+8]`，`[0x498d3c]=[ebp+0xc]`，`[0x498d40]=[ebp+0x10]`，`[0x498d44]=[ebp+0x14]`，并存副本到 `0x655560..0x65556c`；调用前把旧值压栈、返回后恢复）。⇒ **改 .data 里那三个值对运行期无效**（会被每帧覆盖），布局来源是**调用方传入的记录值**。
35. **鼠标位置来源**：只导入 USER32（**无 DirectInput**）；`GetMessagePos`（IAT `0x6aa5bc`）**唯一调用点 `0x45012E`**，函数 `0x45011F` 把 `x=LOWORD`/`y=HIWORD` 与消息参数打包进栈结构，受 `[0x4c90d8]` 控制。`[0x4c90e0]` **不是屏幕尺寸，是 UI 状态标志字**（bit0/1/3/4 被反复测试置位；`0x41c4a1` 拷入 `[0x4af270]`）。
36. **本会话新增工具 & 文档**：`work\peg\find_mem.py`（线性反汇编 .text 并按绝对地址找读写点，坏字节自动跳过；`python find_mem.py 0x4c90e0 30 --ctx 2`）、`work\peg\peek_va.py`（直接 dump 磁盘 exe 某 VA 的 word/dword）；方案文档 [`docs\61-PeG-UI显示系统重构方案.md`](docs/61-PeG-UI显示系统重构方案.md)（含用户 m01288 反馈、机制结论、彩带成因三假设、路线 S/C/D 对比与 P0–P4 阶段）。**下一步待用户给：彩带出现时的截图 + 等比因子取舍（1920/800=2.4 与 1080/600=1.8 不等，不可能同时「等比放大」又「贴满四边」）。**

37. ⭐ **界面记录表 `0x4A22F8` 权威解读（母本实测）**：步长 `0x24`=36B，条数 = `word[0x4af460]`；字段 `+0 u16 flags / +2 i16 x / +4 i16 y / +6 i16 right / +8 i16 bottom / +0xa,+0xc i16 附加 / +0x10..+0x20 五个回调指针`（`+0x10` 多为 `0x44ACDA` 绘制处理器）。母本 16 条：**idx0–12 = 右侧工具栏 13 个按钮（X 762..787，Y 41+36i..66+36i，26×26）**；idx13 = 左上动作条（20..334 × 43..54）；idx14 = **底栏**（10..790 × 576..594）；idx15 = **地图视口**（0..799 × 22..571）。
38. ⭐ **绘制处理器 `0x44ACDA(idx)` 精确行为**：`rec=[0x4cce2c]+idx*0x24`（越界保护 `0<=idx<word[0x4af460]`）；`rect={x=rec.x, y=rec.y−1, right=rec.right+1, bottom=rec.bottom+1, surface=[0x676904]}`；**仅当 `(word[0x4c90e0]>>1)&1` 置位、且 idx==1 或 idx==4** 时算 `dx=0x2ef−rec.x`、`dy=0x16−(rec.y−1)` 再 `0x4235E5(rect, 0x663410, 1, dx, dy)`；否则只在 idx==0xe 时 `0x47097a(9)`。⇒ 那两个常量只管 idx1/idx4；且 `0x47E4E0` 在 `dx<0` 时保持 `rect.left`，**记录右移不会把内容推走，无需同步改 0x2ef**（v8 那轮的“必须成对改”结论只适用于 dx 变正的情形）。
39. **v9a（UI 原大小贴新四边）已生成**：`work\peg\out\PeG030-1920x1080-UIa.exe` md5 `3da266184470fea3637c39323715c69f`（副本 `D:\Program Files\PeG-1\PeG030-16x9-UIa.exe`），基准 = 16:9 产物 `44ac5cfe…`；31 站点（29 条实改）：idx0–12 的 x/right +1120→1882..1907；idx13 +560→580..894（居中）；idx14 right +1120→1910；idx14 的 y/bottom 与 idx15 的 right/bottom **已由 16:9 配方改过**（`w-1`/`h-28` 标签，idx15 现为 1919×1052）。构建器 `work\peg\patch_ui_layout.py`，站点表 `work\peg\out\ui_layout_v9.tsv`，文档 `docs\62`。**顶栏、右侧面板背景、子界面（装备简介等）都不在这张表里，尚未开始。**

40. **GUI 崩溃事故定位（2026-10-14，用户 m01612 提问）**：日志 `C:\Users\Administrator\AppData\Roaming\DSH Desktop\logs\dsh-2026-10-14.log`（＝`.error.log`）显示 `renderer process gone (reason: crashed, exitCode: -36863 / 0xffff7001)` → 自动恢复**两轮共 6 次**全部 `recovery exhausted: renderer recovery timed out waiting for page load and client health` → 第三轮 `renderer process gone (reason: killed, exitCode: 1)` → `DSH Host exited (1)` → 桌面 `12:51:56` 自动重启（本会话由磁盘状态恢复，未丢）。**排除**内存不足（31.8 GB 装 / 20.1 GB 空闲）；`…\DSH Desktop\Crashpad\reports\` 无当日 dump（最新 2026-10-11）。**唯一体积信号**：`[basic-compaction-engine] … shadowed 609 surface nodes (seqs 8-1844, ~524706 tokens)`。恢复逻辑源码：`D:\Program Files\DSH Desktop\resources\app\lib\electron-runtime-C_4WapB_.js`（`formatDesktopExitCode` L780-782、`RETRY_DELAYS_MS` L987、`HEALTH_TIMEOUT_MS=3e4` L992、`STABLE_PERIOD_MS=6e4` L993、`fail()/reload()` L1030-1099、`renderer process gone` L1934）。**规避纪律（长期）**：大表/大清单落盘只回统计、子代理产出落盘只回 ≤400 字摘要、每轮压缩已消费区间、聊天里不重复贴同一截图、进入新阶段开新会话。附带：`mcp-client(openviking)` 对 `http://127.0.0.1:1933/mcp` 连续 10 次重连失败后 `tools unregistered`（建议关掉）；`[agent-registry] … agent/disposed listener threw: TypeError: Cannot read properties of undefined (reading 'catch')` 属子代理销毁噪音，可忽略。

41. **记录表 `0x4A22F8` 附加字段全部在用（本轮实测修正）**：`+0xa`/`+0xc`/`+0xe` 三个 i16 均非空闲（idx0–12 非 `0xFFFF`，idx13 起为 `0xFFFF`）⇒ 原计划「借 padding 存位移」**作废**；回调槽 `+0x10`=`0x44ACDA`、`+0x14`=`0x44889F`、`+0x18`=`0x448A3A`、`+0x1c`=0、`+0x20`=`0x44C1E1`。

42. **绘制处理器 `0x44ACDA` 完整语义（反汇编确证）**：越界保护（`idx < word[0x4af460]`）→ `rec=[0x4cce2c]+idx*0x24` → `rect={x=rec.x, y=rec.y−1, right=rec.right+1, bottom=rec.bottom+1, surface=[0x676904]}`（存 `[ebp-0x18]/[ebp-0x14]/[ebp-0x10]/[ebp-0xc]/[ebp-8]`）→ 若 `(word[0x4c90e0]>>1)&1`：**仅 idx==1（0x44AD75）与 idx==4（0x44AD9C）绘制**（`push (0x16−rect.top); push (0x2ef−rect.left); push 1; push 0x663410; push &rect; call 0x4235E5`），其余立即 return；未置位时只有 `idx==0xe → push 9; call 0x47097A`。⭐ 屏幕上那一列按钮**不是它画的**；`[ebp-0x18]/[ebp-0x14]` **同时**是目标矩形左上与源偏移的被减数 ⇒ 位置与取样被同一对局部变量耦合（「挪记录＝拉彩带」的结构性原因）；`0x4A22FA`（rec0.x 绝对地址）在全 `.text` **零引用** ⇒ 读取方是按索引算指针，不出现绝对地址。

43. **右侧面板/工具栏的搬移量＝运行期动画量**（`0x4488C5` 段）：`movsx eax,word[0x4af32c]`（动画索引）→ `movsx ecx,word[eax*2+0x498d38]`（该索引目标状态）→ `movsx edx,word[0x4af2fc]`；不等则 `[eax*2+0x498d34]=word[0x4af2f8]`、`[edx*2+0x498d38]=word[0x4af2fc]`、`push 0; push word[0x4af2fc]; push word[0x4af2f8]; call 0x41FF8A`，再按 `(word[0x4c90e0]>>1)&1` 决定是否 `push 0x16; push 0x2ef; push 1 …`（与 `0x448847` 段同型的**字面图集坐标 (751,22)** + 同一 ctrl `0x663410`）。⇒ **v9b 应动的是 `0x4af2f8`/`0x4af2fc` 这条面板滑动基准，而不是记录表**；`0x2ef` 全 `.text` 仅 5 处硬编码（`0x43AA47`/`0x448849`/`0x448940` 的 `push`、`0x44AD7E`/`0x44ADA5` 的 `mov edx`）。

44. **地图视口 clamp/滚动函数（`0x44C6F0` 段）**：`0x44C703 cmp dword[0x663380],0 / jge`（滚动 X 归零保护）；`0x44C724 cmp dword[0x663388],0x320 / jle` → `0x44C730 mov eax,0x320; sub eax,[0x663380]; mov [0x4a2730],eax; mov [0x663388],0x320`；`0x44C76B cmp dword[0x66338C],0x258 / jle` → `0x44C777 mov edx,0x258; sub edx,[0x663384]; mov [0x4a2734],edx; mov [0x66338C],0x258`；随后 `push 0; push 0x1000000; push 0x663380; push [0x676904]; push 0x4a2728; push [0x686528]` 提交 Blt。⇒ 地图目标矩形 **`0x4a2728 = (−sx, −sy, 800−sx, 600−sy)` 每帧由代码重算**（与记录表无关，故挪记录搬不动地图）；源偏移直接传 `&[0x663380]`；「地图铺满」靠 16:9 配方改这 6 处 `0x320`/`0x258`。

45. **本轮落档** [`docs\63-PeG-16比9界面重构：崩溃事故、v9a判读与v9b设计.md`](docs/63-PeG-16比9界面重构：崩溃事故、v9a判读与v9b设计.md)（六节：崩溃事故证据链与规避／v9a 判读／新静态事实（记录表全解、`0x44ACDA`、面板动画量、地图 clamp）／v9b 设计三路径（B1 成对改 `0x2ef`+记录；**B2 推荐：位移表 + 矩形构造改写 + 命中测试同步**；B3 运行期 hook）／彩带三假设与判别实验 **E1**（把地图滚到右侧真地形再移动鼠标：彩带消失⇒越界采样为主；不消失⇒光标 save-under 为主）与 **E2**（不动/动鼠标两图对比）／下一步五项）。**本块未改任何 exe（母本与全部产物原样）。** 子代理状态：4 路调研全部结束（`63cd31ea` 已交结论，见第 48 条）。

46. **实机截图（1920×1080 两张，用户 m01713/m01714）像素级测量结论**（脚本 `.workbuddy\tmp\analyze_shots.py`、`analyze_shots2.py`）：已绘制（非黑非品红）区域 = shot1 的 `{x≤799：全高 y=23..1048}` ∪ `{y≤614：x≤1591}`；shot2 的 `{x≤799 全高}` ∪ `{x=800..1119 全高}` ∪ 更右侧**斑驳补画**块；**x≥1600 两张都是 0% 已绘制（纯黑）**，y≥1055 整行纯黑（底栏没被重绘）。品红（16bpp `0xF81F`）只在两处出现：`y=22`（x=800..1357 的顶行细线）与 `y≈600..620`（x≈1172..1915 的 ~20 px 宽带；`y=1040` 还有 x=1..2）。⇒ **引擎按“脏区/脏标志”增量重绘，新暴露区域从不初始化**（两张图的已绘制形状不同即为证）；地图 1:1 铺满、无拉伸变形，工具列仍在 x=762（新旧分辨率不变），顶栏正常。

47. **重绘/刷新机制（本轮静态确证，母本实读）**：`0x423CD6` = 控件刷新循环（遍历 `[0x4cce2c]` 的记录，`flags & 0x8000` 结束；`flags & 0x84` 才 `call 0x42380F(i)`；按母本 flags：idx0–12=0x1045 满足 0x84、idx13/14=0x1820 与 idx15=0x0001 不满足）。`0x44AC45` = 刷新函数：若 `byte[0x4af360]≠0` 直接返回，否则 `call 0x44C50A`（顶栏）→ `call 0x44C57B`（底栏，**全仓唯一调用者就是这里**）→ `call 0x423CD6`。它只被 `0x4489CC` 在 `word[0x498d74]≠0` 时调用并清标志。`word[0x498d74]`：置 1 于 `0x425CA8`（随后 `push 1; call 0x456AB5`）；清 0 于 `0x40ACFE`/`0x40B1B9`/`0x41361C`/`0x414BF0`/`0x41E4D1`；读取于 `0x4135EC`/`0x414BD3`/`0x41DD69`/`0x4238B1`。`0x44C50A`（顶栏绘制）有 14 个调用点（含 `0x40AB60`，位于函数 `0x40AB5A`：`sub esp,0x14; call 0x44c50a; call 0x425b79`）。⇒ **强制全刷新 = 让 `word[0x498d74]` 每帧非 0（或改 `0x4489CC` 的条件）**，这是“黑区/底栏不显示”的第一候选修法。

48. **第 4 路调研（开源重制版如何做 UI/宽屏）**：全文 `.workbuddy\tmp\research-remake-ui-scaling.md`（33,983 字节 / 437 行，含 file:line）。三条正交机制：**(1) UI 尺寸常量完全不动；(2) 位置变成屏幕尺寸的算术函数（锚点表达式 / 标准窗口偏移 / 面板原点）；(3) 缩放只发生在输出层且必须整数倍 + 黑边（或居中）**。OpenRA：widget 的 X/Y/W/H 是 YAML 算术表达式，Initialize 注入 `WINDOW_WIDTH/WINDOW_HEIGHT/PARENT_WIDTH/PARENT_HEIGHT` 后求值（`OpenRA.Game/Widgets/Widget.cs:292-320`），右下居中写 `X: PARENT_WIDTH - WIDTH - 15`、`X: (WINDOW_WIDTH - WIDTH) / 2`（`mods/cnc/chrome/*.yaml`），像素精确靠 dpiScale 切 Image2x/Image3x（`ChromeProvider.cs:117-122`）。**DevilutionX（最值得抄）**：`MainPanelSize{640,128}` 固定，位置 `((gnScreenWidth-640)/2, gnScreenHeight-128)`（`Source/control/control_panel.cpp:243-247`），面板内元素全用「面板原点 + 原坐标」（`GetPanelPosition`），宽屏时底栏不再扣视口高度、地图吃满（`:275-277`）。OpenXcom：`Screen::getDX() = (baseW - 320)/2`（`src/Engine/Screen.cpp:596-608`）+ `State::centerAllSurfaces()` 一次性给所有控件加偏移、原坐标不改（`src/Engine/State.cpp:379-389`）。ja2-stracciatella：专用 `UILayout` 类，`STD_SCREEN_X/Y` + `recalculatePositions()`，`tpYOffset = screenH - TEAMPANEL_HEIGHT`（贴底）、`tpXOffset` 居中（`src/game/UILayout.cc:57-63`），issue #1399 有成文设计。ScummVM：整数倍 pixel-perfect + aspect 校正（`graphics/scaler/aspect.cpp`）。最贴近前例：pg-cht 的 `pacgen/docs/09-a1-hires-canvas-roadmap.md`（同代 DirectDraw 拉高画布，SetDisplayMode 单点、P0–P5 含 P4 坐标/命中区映射，但它是 UI 一起放大，与「UI 不变只挪位」互补）。未取到：DXX-Rebirth（抓取超时）、EDuke32（不在 GitHub）、Open General / PG Forever（无公开源码）。

49. ⭐ **【根因】屏幕描述符写死 800×600（本轮最大发现）**：`0x44219F` 段在每次 `SetDisplayMode` 后初始化三个描述符 —— `0x676980`（surface `[0x676904]`，`0x4421D4`/`0x4421DE` 写死 `0x31F`/`0x257`＝799/599）、`0x676960`（surface `[0x675538]`，`0x442219`/`0x442223` 同样写死）、`0x676120`（surface `[0x655574]`，用运行期真实尺寸 `[ebp-0x6C]-1`/`[ebp-0x74]-1`）⇒ 引擎拿得到真实屏幕尺寸，只是前两处没跟着走；**改 `.data` 里的 799/599 无效**是因为每次切模式都被这段重写。统一漏斗 `0x4235E5 → 0x47E0A0 → 0x47E4E0` 的裁剪正是用描述符矩形 ⇒ 元素 `dx` 超过 800 时 `dst.right` 变负、目标矩形左右反转 ⇒ 源图被横向拉伸/错切、命中区错位。**一条根因解释全部怪象**：跟随鼠标的彩色/品红拉伸带、底栏整条不出现（y≥600 的绘制被夹掉）、右侧大片黑区（越界 Blt 被拒 + 脏区重绘不覆盖新区域，牵引地图才补上＝用户 m01750）、v9a 把按钮挪到 1882 后整列被拉成条（dx 更大 ⇒ 更负）。
50. ⭐ **v10a/v10b 已生成（等用户实机跑）** ⇒ [`docs\64-PeG-16比9画布根因（屏幕描述符写死800x600）与v10构建.md`](docs/64-PeG-16比9画布根因（屏幕描述符写死800x600）与v10构建.md)。构建器 `work\peg\build_v10.py`（基点＝16:9 产物 `44ac5cfe…`；两遍补丁：A 画布 4 处 + B 每帧强制整屏重绘 1 处 → v10a；再叠 D UI 重排 29 条 + `0x45696D` 面板位置 → v10b）。产物：`work\peg\out\PeG030-1920x1080-v10a.exe` md5 `2bd80503e85f171fc0ea562694a544c1`（副本 `D:\Program Files\PeG-1\PeG030-16x9-v10a.exe`，与 16:9 基准差 10 字节/5 段）；`…-v10b.exe` md5 `c885440c8ac8c371b06a584259a5a670`（副本 `D:\Program Files\PeG-1\PeG030-16x9-v10b.exe`，差 70 字节/35 段）。**判读 6 项**（彩带是否消失／底栏是否出现／黑区是否消失／v10b 工具列是否整齐落在 1882..1907 且仍 26 px／最右按钮点击是否有反应／子界面是否正常）见 docs\64 §三。
51. **工具教训（本轮）**：16:9 站点表**已经包含**坐标夹取的 4 处写入（`0x43B22C`/`0x43B242`/`0x43BD8F`/`0x43BDA5`），`build_v10.py` 必须把「现值已等于目标值」当无操作（否则误判成母本不匹配）；`0x45696D` 是 `66 c7 05` 前缀的 **16 位** `mov word [0x4A42EC], imm16`，解析必须跳过 `0x66`（`kind=word`）。两套站点的 `va` 含义不同：`ui_layout_v9.tsv` 的 `va` 是**数据字段地址**，代码侧站点 `va` 是**立即数地址**。
52. **v10b 实测（用户截图 m01875）**：✅ 工具列 13 按钮贴到最右（实测 x=1882..1907，26 px 未拉伸，D 组有效）；✅ 大片纯黑消失（整屏非黑 80.9%，对照此前 x≥1600 整列 0%，B 组「每帧强制重绘」有效）；✅ 顶栏正常、地图 1:1 铺满。❌ 鼠标移到工具按钮上时，本该是小的「说明文字框」，实为三大条**品红带**：`y=192..251`（x=800..1818，宽 1019）、`y=300..359`（同宽）、`y=372..467`（x=800..1842，宽 1043，96 行＝两条叠加），文字只占每条最左约 150 px（x≈803..955），其余为品红（RGB(240,0,240)≈16bpp `0xF01E`）⇒ 提示框**底色（透明键色）整块外露**，且**宽度按「旧 800 边界→屏幕右边」算**（左缘恒为 x=800＝旧按钮右缘 787+13）⇒ 提示框锚点/宽度都没随新分辨率走。❌ 底部 y≥1056 仍纯黑（底栏未画）；❌ 用户口述鼠标移出 800×600 仍有拖影（A 组未解决）。
53. **v10c/v10d 隔离构建**（`python work\peg\build_v10.py --skip-desc --apply`，新增 `--skip-desc` 开关跳过 A 组屏幕描述符）：`work\peg\out\PeG030-1920x1080-v10c.exe` md5 `ed7b6f4648241f48390580243016f52c`（仅 B，diff 2 字节/1 段）；`work\peg\out\PeG030-1920x1080-v10d.exe` md5 `7c8f1baab1b4d9e8e19a417719d17940`（B+D，diff 62 字节/31 段，副本 `D:\Program Files\PeG-1\PeG030-16x9-v10d.exe`）。判读：v10d 下说明框若消失⇒品红框由 A 组放大裁剪框后才露出；若依旧⇒与 A 无关。`SetColorKey`（IDirectDrawSurface vtable **+0x74**）命中点：`0x41C14C`（key 的 surface 参数来自 `0x4AF26C`）、`0x441E07`（`0x6633FC`）、`0x441F02`（`0x62CE10`）、`0x441F9B`（`0x681D0C`）、`0x442034`（`0x675538`）、`0x47D629`。屏内坐标夹取函数在 `0x43B203..0x43B242`（把 `[0x61E924]/[0x61E928]`=x、`[0x61E92C]`=y 夹进屏内，随后 `push 0x5DC; push [ebp+8]; push 0x61EAA0; call 0x47FBA0` 写 1500 字节结构）。

54. ⭐ **用户叫停「反复试变体」并指定做法（`m01977` 逐字）**：「你先完整的看看游戏的画面显示机制吧，现在这种改法太反反复复空耗token了。看看为什么用不了地图，为什么不显示文字。明白机制后再说如何改，一次性改好。」⇒ 本轮起改为**机制驱动的单点改动**，每轮只动一处、并写明预测。两路只读测绘（显示管线 / 地图合成）已返回，结论落档 [`docs\65-PeG画面显示机制全图（DirectDraw管线测绘）.md`](docs/65-PeG画面显示机制全图（DirectDraw管线测绘）.md)（十节：初始化→DDraw 创建→面清单→绘制漏斗→上屏与丢失恢复→写死 800/600 全清单→症状归因→候选单点→**§10 显示层能力矩阵与决策**）。逐条证据：`.workbuddy\tmp\research-display-pipeline.md`、`.workbuddy\tmp\research-map-composition.md`（均只读，未改 exe、未启动游戏）。

55. **地图合成机制（子代理报告，逐条有地址）**：地图面 `[0x655574]` 与 `[0x622A10]` 都是 **1920×1920、16bpp、SYSTEMMEM**（7.4 MB/个；创建于 `0x441BE5–0x441C22`，`dwHeight/dwWidth=0x780`，母本＝产物）；地块/精灵用 BltFast（`0x424AFD`/`0x424C56`）或 Lock+直写（`0x43D6E1`，坐标夹 `cmp 0x780`）填满；每帧 `0x41EB33 call 0x41FF8A` 把视口窗口（x=`[0x4af2f8]`、y=`[0x4af2fc]`、宽=视口 right−left+1）一次 BltFast 到后备缓冲 `[0x676904]` 的 (0,22)，再叠层/GDI 文字/与整屏画布 `[0x675538]` 互拷（`0x425BCB`），最后 `Flip([0x61F900])`（`0x41FE4C`）。**行距取自 Lock 回填，无 pitch 硬编码**。⇒ ①**无包装下地图不画**＝视口源矩形 (x,y,x+1920,y+1032) 一滚动就越出 1920×1920 面，原生 DirectDraw **整笔拒绝**（代码只记日志 `0x42000B` 不回退）；②**cnc-ddraw 黑空洞**＝增量重绘（`0x4489D8` 的 `je`）+ 越界被夹取（拖动改变 x ⇒ 夹取范围变 ⇒ 黑区被补上，即用户 `m01750`）；③**Svens 品红**＝该包装**未执行 `DDCKEY_SRCBLT`**（键值 `[0x6769B0]`：565→`0xF81F`、555→`0x7C1F`；SetColorKey 于 `0x441E07`/`0x441EF1`/`0x441F8A`/`0x442034`）。⚠️ 报告建议：可用 `0x441BFA`/`0x441C01` 的 `0x780` 放大（如 `0x1000`）治源矩形越界；**切勿单独放宽裁剪框**。

56. **显示层能力矩阵 → 选定 DDrawCompat 作单点验证（本轮决策）**。引擎实际用到三项 DirectDraw 语义（均有静态证据）：① Blt/BltFast 的 `DDCKEY_SRCBLT` 抠图（浮动提示框/光标面/整屏画布靠它抠品红底）；② 源矩形越界时**夹取而非拒绝**（地图视口必然越界）；③ 16bpp 面的 GetDC/GDI 文字。实测：**Svens Wrapper 缺 ①②**（品红抠底失效 + 黑区）｜**cnc-ddraw 缺 ③**（悬停不显文字）｜**原生 DirectDraw 缺 ②**（地图完全不画）｜**DDrawCompat v0.7.1 = 三项都有，待实机验证**。获取：`https://github.com/narzoul/DDrawCompat/releases/download/v0.7.1/DDrawCompat-v0.7.1.zip`（1,067,481 B，解包仅 `ddraw.dll` 3,612,672 B，md5 `26275ED572A4DF16141B26E952B50106`，FileVersion v0.7.1；识别 `DDrawCompat.ini`，键含 `DisplayResolution`/`DisplayAspectRatio`/`ResolutionScale`/`BltFilter`/`TextureFilter`/`CompatFixes`/`SurfacePatches`/`PresentDelay`）。**四套对照副本，同一个 exe（v10b `C885440C8AC8C371B06A584259A5A670`）、只换显示层**：`D:\Program Files\PeG-ddc\`（DDrawCompat；原 Svens 改名 `ddraw-svens.dll.bak`，说明 `说明-DDrawCompat测试.txt`）｜`D:\Program Files\PeG-nw\`（无包装）｜`D:\Program Files\PeG-cnc16\`（cnc-ddraw 7.1.0.0）｜`D:\Program Files\PeG-1\PeG030-16x9-v10b.exe`（Svens 对照）。**判读要点**：品红/黑区/文字三者的差异必然归因于显示层，与我们的补丁无关。备选 exe 侧改动（DDrawCompat 不成再动）：地图面 0x780→0x1000、`0x456070 RestoreAllSurfaces` 的「任一失败即中止」改为「记录并继续」。

57. **本会话新增/常用工具（可复用）**：`work\peg\vtcalls.py`（按 IDirectDrawSurface vtable 槽找调用点，如 `python vtcalls.py 0x54`＝GetPixelFormat、`+0x74`＝SetColorKey）· `work\peg\imm_range.py`（列范围内立即数写入）· `work\peg\peek_va.py --exe <exe> <va>`（dump 磁盘上任意产物的 word/dword；不带 `--exe` 默认母本）· `find_bytes.py "<hex 带 .. 通配>" <节> --ctx N` · `disasm_range.py <lo> <hi>`（起点必须是指令边界）· `find_mem.py <va> <maxhits> --ctx N` · `xref_call.py`（调用图，base 必须＝节 VirtualAddress＋imagebase 0x400000）· `peek_table.py "exe" 0x4A22F8` · `build_v10.py`（A/B/D 组，`--skip-desc`）· `patch_res_wh.py`（任意 w×h）· `patch_ui_layout.py`（记录位移）。

58. ⭐ **运行期内存补丁启动器（方案 A 落地，母本 exe 零改动）**：`work\peg\peg_launcher.py`（359 行）。机制：`CreateProcess(..., CREATE_SUSPENDED)` 挂起启动 → 从 WOW64 的 PEB 读实际模块基址（本机读回 `0x400000`，仍按 delta 换算、不假设）→ 在主线程执行任何指令前用 `VirtualProtectEx` 开写权限 → **逐站点「先读旧值、等于母本旧值才写」并立即回读** → 任一不符**打印并中止且不做任何写入** → 恢复页保护 → `ResumeThread` 放行（Python 退出不影响游戏）。站点 **141 条**（1920×1080）＝尺寸站点表 `out\res_diff_v4.tsv` 96 条（`va`=立即数地址，按 tag 重算，跳过 163 条 `dx`；`idx14.y`/`idx14.bottom` 与尺寸表一致自动合并）＋代码侧 imm32 10 条（同 `patch_res_wh.py` 的 `CODE_EDITS`）＋A 组描述符 4 条＋B 组 `0x4489D8 74 1B→90 90` 1 条＋D 组 UI 位移 29 条＋面板位置 1 条。用法：`--dry-run`（只打印）／`--selftest`（挂起启动→打补丁→回读校验→杀掉，**游戏不跑一帧、无窗口**）／默认（正常启动）；可加 `--w/--h/--exe/--cwd/--no-ui/--no-repaint/--no-canvas`。**自测抓到的两次地址错误（已修正，留档）**：①A 组四个站点在 `build_v10.py` 里是**指令 VA**（`0x4421D4/0x4421DE/0x442219/0x442223`），启动器必须写 **指令 VA+6** 的立即数地址（`0x4421DA/0x4421E4/0x44221F/0x442229`），误写指令地址报 `内容=c7058869 期望 1f030000`；②`0x45696D` 是 `66 c7 05 <abs32> <imm16>`，`0x66` 前缀把 `c7 05` 的 2+4 顶到 +7 ⇒ imm16 在 **`0x456974`**（误用 +6 报 `内容=001f 期望 1f03`）。修正后 `--selftest` ✅「141 条已写入并回读一致（exe 文件未改动）」。另遇一次 `CreateProcess 失败：WinError 5 拒绝访问`，重跑即过（疑似安全软件瞬时拦截）。**分发**：`D:\Program Files\PeG\启动-16比9-内存版.cmd` 与 `D:\Program Files\PeG-1\启动-16比9-内存版.cmd`（各指向同目录 `PeG030.exe`，两处 md5 均为 `c462e897b3aa1c384870c857ce9e01df`），依赖 `C:\Python314\python.exe`；md5 校验只认母本 ⇒ 改过的产物（v10a…v10d）不要交给启动器。落档 [`docs\66-PeG运行期内存补丁启动器（原版exe零改动）.md`](docs/66-PeG运行期内存补丁启动器（原版exe零改动）.md)。

59. ⭐ **目录清理：游戏侧唯一入口（用户 m02455「清理掉之前的分支版本，现在太混乱了，我都不知道从哪个exe进游戏看效果了」）**：删掉五个试验副本 `D:\Program Files\PeG-1`／`PeG-nw`／`PeG-cnc`／`PeG-cnc16`／`PeG-ddc`（合计释放 **2.69 GB**；副本里的 Scenario 译文比 `PeG` 旧、`SAVE\*.sav` 时间戳与母本一致即无独有存档，已核对后才删）。**删除前先收档**：18 个试验 exe → `D:\DSH\军事游戏汉化\archive\exe\`（`PeG030-1920x1080.exe 44ac5cfe…`、`PeG030-16x9-UIa.exe 3da26618…`、`-v10a 2bd80503…`、`-v10b/-16x9 c885440c…`、`-v10c ed7b6f46…`、`-v10d 7c8f1baa…`、`-1600x900 2c0369eb…`、`PeG030res.exe 2107b73b…`、`v5a 8b03c59b…`/`v5b 0d38ae62…`/`v5c 4657e47d…`/`v5d 735a08d6…`/`v6a fba578bc…`/`v6b f82aaac6…`/`v7a f7b611c9…`/`v7b 403e063a…`/`v7c 5384d869…`/`v8a 8823d6d6…`/`v8b c60c5727…`）；三种显示层 dll → `archive\ddraw\`（**Svens** `337866f0c870384f5a16c8a11c46a963` 159,232 B／**cnc-ddraw 7.1.0.0** `1f989788547df3315d18f11f5f10400b` 411,648 B／**DDrawCompat 0.7.1** `26275ed572a4df16141b26e952b50106` 3,612,672 B）＋三份旧测试说明 → `archive\说明存档\`。**唯一入口 = `D:\Program Files\PeG\启动-16比9-内存版.cmd`**（同目录新增 `说明-怎么进游戏.txt`；`PeG030.exe` 母本 md5 仍是 `c462e897b3aa1c384870c857ce9e01df`，未被改）。`Peg-Part-2`、`PeG-WW2` 是用户自己的其它安装，**未动**。收档与重建配方（robocopy 母本 + 换 ddraw.dll + 拷启动器）写在 `archive\README.md`；docs\66 §6 已同步。

60. ⭐ **「点 .cmd 启动不了」根因＝批处理用 LF-only 写出（已修）**：用户 `m02491`「点击.cmd启动不了。。。。」。排查：`启动-16比9-内存版.cmd` 当时的字节是 `40 65 63 68 6F 20 6F 66 66 0A …`＝**UTF-8 无 BOM ＋ 只有 LF**；`Get-Content` 证据同时显示 PeG 目录里没有新写入（`PEOPLES.INT` 仍 10-11、无 `.log`）⇒ 根本没走到启动。**根因：`cmd.exe` 解析批处理依赖 CRLF**，LF-only 文件遇到跨行的 `if errorlevel 1 ( … )` 块会解析失败、窗口一闪而过（连 `pause` 都跑不到）。**修法**：`.cmd` 重写为 **cp936(GBK) 编码 + CRLF + 命令全 ASCII（中文只在 `echo` 文本里）**，显式 `chcp 936`，结尾**无条件 `pause`**。**同时加固**：①启动器新增 `--log`（默认 `work\peg\out\launcher-log.txt`，UTF-8 追加、带时间戳与命令行，用 `Tee` 类把 stdout/stderr 同时落盘）；②`CreateProcess` 失败**自动重试 3 次**（0.7 s 间隔）后再报错并提示「先直接双击 PeG030.exe 验证游戏本身」；③新增快捷方式 `D:\Program Files\PeG\进游戏-16比9宽屏.lnk`（TargetPath＝那个 .cmd，图标取 PeG030.exe）以绕开「.cmd 关联被改/损坏」。**验证（用 `--selftest` 临时副本，未真启动游戏）**：`cmd /c <临时.cmd>` ✅、`Start-Process <临时.lnk>` ✅、日志 ✅（均以「✅ 内存补丁完成：141 条已写入并回读一致」结束）。docs\66 新增 §5.5 记录此事。61. ⭐ **悬停「小说明框」品红面板：根因定案 + E 组补丁（2026-10-14）**。用户实机跑启动器后确认 16:9 成功但品红带＋黑空洞仍在（m02533/m02534），并给出三条线索（逐字）：m02547「原版汉化后没有冒品红，但是英文版的时候，所有文字都是有一圈品红轮廓的。」／m02553「4.会出现小说明框，说明按钮作用。」／m02559「"小说明框"和那条 1019 像素宽的品红带很可能是一个矩形，因为他们里面显示的文字就是按钮的作用提示文字。」
    * **像素实测**（用户 m02533 截图，1920×1080）：品红 = `y=120..179`（高正好 60）、`x=800..1818`（宽 1019）的**单一实心矩形**（中途行只有一个 run），另有两个孤立像素（噪声）。
    * **只读逆向**（报告 `work\peg\out\report-hintbox.md`，379 行）：全 exe 唯一文本 API = `USER32!DrawTextExA`（IAT `0x6AA5B0`），唯一文本函数 `0x47010B`（`0x470151 mov ecx,[0x676904]` = **总是画到后台缓冲** → `call [eax+0x44]` GetDC → SetTextColor(`0x6AA3E8`) → SetBkMode(1)(`0x6AA3E4`) → SelectObject(`0x6AA3F8`) → `DrawTextExA`(flags `0x410`) → `call [edx+0x68]` ReleaseDC；行高 = `idiv 0xe`(14)），9 个调用者（`0x43BBFA`/`0x43BCCD`/`0x43C3D0`/`0x44CE4A`/`0x452F0C`/`0x453909`/`0x46DEFA`/`0x4700FC`/`0x4716CF`）。文本**不在 exe 内**（cp936/UTF-16LE/UTF-8 搜「步兵」「布雷德利」全 0 命中）⇒ 来自外部数据文件。
    * **面板本体** = `[0x62CE10]` **300×60**（`CreateSurface` `0x441E6C..0x441E88`，`dwWidth=0x12C`/`dwHeight=0x3C`），`SetColorKey` `0x441ECE..0x441F02`（`push 8` = `DDCKEY_SRCBLT`，键值 `word[0x6769B0]`；唯一写点 `0x441BB7`(0x7C1F, RGB555)/`0x441BCC`(0xF81F, RGB565)）。绘制函数 `0x44CD3A`：`0x47DFA0(面板, 色键色)` 把整面涂成品红 → `0x47170C` 画立体边框 → `0x47010B` 文字画到后台缓冲 → `0x44CE52` 写 RECT(0,0,300,60) 进 `[0x676300..0x67630C]`。随后 `0x44C7BE` 段取位置 `word[0x686541]`(左)/`word[0x686543]`(上) → `[0x6769A0]`/`[0x6769A4]`，`+0x12C`/`+0x3C` 得右/下；先保存底图（`Blt([0x61F3E0], dst=[0x685FF0], src=[0x676904])`），再 `call 0x41EB70`（flags `0x1008000` = `DDBLT_WAIT|DDBLT_KEYSRC`）把面板抠图上传。同款第二处 `call` 在 `0x44CD27`。
    * **★根因**：通用位块助手 `0x41EB70(x=[ebp+8], y=[ebp+0xC], src=[ebp+0x10], RECT* rc=[ebp+0x14], 0, flags)` 内部按硬编码屏宽裁剪，`0x41EBF8 cmp dword [ebp+8], 0x320`（我们的补丁已改成 `0x780`）命中「**x ≥ 屏宽 ⇒ mov al,1; ret 直接放弃**」。面板目标 x=800 正好等于母本屏宽 ⇒ **母本 800×600 里这两条面板位块从不执行**（所以母本既无品红、也无它留下的残留）；补丁把判定放宽到 1920 后它开始执行，而当前显示层（Svens 包装）在这条路径上不执行色键抠图 ⇒ 品红整块露出，宽 1019 = 鼠标横移时 300 宽面板的并集。旁证：用户回忆**原版英文版「所有文字都有一圈品红轮廓」**⇒ 该包装对色键抠图本就不完全可靠（汉化版做过处理）。
    * **E 组补丁（已落地 + 自测通过）**：`work\peg\peg_launcher.py` 新增 `TOOLTIP_SITES`：`0x44C929` 的 `e8 42 22 fd ff` 与 `0x44CD27` 的 `e8 44 1e fd ff` 各改 5 个 `90`（nop）——等价于**恢复母本 800×600 的实际行为**；文字仍由 `0x47010B` 直画后台缓冲，说明文字照常显示。新增 `--keep-tooltip` 用于 A/B。`--selftest` 输出：**143 条站点**（尺寸 96 + 代码侧 imm32 10 + A 组 4 + B 组 1 + D 组 30 + E 组 2），母本 md5 一致、全部写入并回读一致、exe 文件未改动、进程被终止（游戏未跑一帧）。
    * **黑空洞线索（未证实，下一轮）**：保存端用 `[0x61F3E0]`(300×60)，恢复端目标数据 RECT `0x4A2728`=(0,0,80,60)，两端尺寸不一致 ⇒ 错位贴回未初始化（全 0=黑）区域。需动态证据：断点 `0x44C8CB`（保存）/`0x44C5F0`（恢复）记录 dst/src RECT 与 dwFlags；dump `[0x6769A0]`/`[0x6769A4]`/`[0x676300..0x67630C]`/`[0x685FF0..0x685FFC]`/`[0x4A2728..0x4A2734]`/`[0x6769B0]`；检查 Blt 是否丢 `0x8000`。
    * **落档**：`docs\66` 新增 §5.6（机制＋证据＋E 组），§7「下一步」改写（A/B 隔离、上面那条黑空洞线索、显示层对照暂缓）。报告 `work\peg\out\report-hintbox.md` §6 覆盖缺口清单：3 条裁剪算术未改（`0x41EC11`/`0x41EC2C` = `e0 fc ff ff`(−0x320)、`0x41EC94` = `a8 fd ff ff`(−0x258)）；未改 800 立即数 14 处（`0x405C1F`/`0x408835`/`0x414529`/`0x414649`/`0x414668`/`0x4146E8`/`0x417703`/`0x42041E`/`0x45E741`/`0x46B2AB`/`0x46CF45`/`0x4700DD`/`0x4888F9`/`0x491118`）、600 共 7 处、571 共 2 处；`0x40187F` 是 `sub esp,0x258` 栈帧（**误报不要改**）。
    * **新工具**：`work\peg\hint_pe.py`（PE 解析/is_bss/va_to_fo/字节搜索/逐条 capstone 重同步）、`work\peg\d.py <lo> <hi> [--exe|--PORT]`（区间反汇编）、`work\peg\xr.py call|dword|push|near|diff|find`（交叉引用）、`work\peg\imports.json`（184 条导入名）。
    * **教训**：①判断站点是否被补丁覆盖，必须取**立即数首地址**的字节（取指令首地址会把「已改的站」误判成未改）；②`.text` 里夹有跳转表数据（`0x43BB39` 起 48 字节 `07 07 07…`），线性反汇编会失步，必须逐条解码＋重同步；③我提出的「`0x456xxx` 混合基准 = 提示框矩形」被报告否决（那段是**滚动判定**，`[0x4A42EC]` 是滚动条滑块补偿）⇒ 假设要等静态证据再动手。
62. ⭐ **「画面破碎」根因＝通用位块助手 0x41EB70 的裁剪算术仍用旧基准（F 组，2026-10-14 修复）**。用户 `m02666` 逐字：「出了新问题，移动到按钮上无法点击，也没有说明文字，在地图上扫，鼠标倒是不会出现拖影了，但是运行一下后，移动鼠标，会出现现在截图上的画面破碎。」
    * **像素实测**（脚本 `.workbuddy\tmp\analyze_stripes.py`，用户 m02665 那份 1920×1080 截图）：品红 bbox = `y=580..821`、`x=800..1918`（**恰好从旧屏宽 800 开始**），共 90,873 px；横向锯齿步长 ≈101 px（列边界 800/901/1002/1104/1205/1306/1408/1510/1611/1712/1814/1915）、纵向周期 7 px；品红与地图绿交替。
    * **根因**：通用位块助手 `0x41EB70` 内部按硬编码屏宽裁剪请求矩形。它的**外层判定常量**早已被我们的补丁改成新值（`0x41EBF2`/`0x41EBF9` = `0x780`、`0x41EC75`/`0x41EC7C`/`0x41ECA7` = `0x438`），但**减法还是旧基准**：`0x41EC11`、`0x41EC2C` = `e0 fc ff ff`（−0x320 = −800）、`0x41EC94` = `a8 fd ff ff`（−0x258 = −600）。后果两条：① `x+w > 1920` 的矩形执行 `w -= (x+w−800)`（减数远大于宽度）⇒ **宽度变负、右边界倒退到 800** ⇒ 位块斜着搬运一大片内存（101 px/行的锯齿就是它）；② `x+w ∈ (800,1920]` 的矩形被这道减法钳在 800 ⇒ **x>800 的区域永远得不到重绘**，只剩陈旧的品红/旧帧内容 ⇒ 用户看到的「画面破碎」。
    * **F 组补丁**：`0x41EC11`/`0x41EC2C` → `80 f8 ff ff`（−1920）、`0x41EC94` → `c8 fb ff ff`（−1080），让裁剪边界与新屏宽一致。
    * **E 组改为可选（默认不打）**：`work\peg\peg_launcher.py` 的 `--no-tooltip` 才 nop 那两处面板位块。理由：nop 掉之后拖影虽然没了，但**按钮说明文字一起消失**（用户 m02666 实测），而且保存/恢复那套机制仍在跑，会把旧内容（含品红）沿鼠标轨迹反复盖回屏幕。默认保留面板 ⇒ 说明文字与按钮反馈恢复正常，品红交给显示层解决。
    * 站点总数：**144 条**（96 尺寸 + 10 代码侧 imm32 + A 4 + B 1 + D 30 + F 3）；`--selftest` 输出「✅ 内存补丁完成：144 条已写入并回读一致（exe 文件未改动）」。落档：`docs\66` 新增 §5.7、§5.6 更新、§7「下一步」改写（下一步＝DDrawCompat v0.7.1 显示层对照，dll 收档在 `archive\ddraw\`，md5 `26275ed572a4df16141b26e952b50106`）。
    * **教训**：①一个代码路径的常量必须**成套**改（判定 + 算术），只改判定会造出负宽度位块；②把某个绘制调用 nop 掉、却留着配对的保存/恢复机制，会比原来更糟（陈旧内容沿轨迹反复盖回）；③「nop 面板」不是好解法——面板的品红是**显示层不执行 DDBLT_KEYSRC** 造成的，正解在显示层。
63. ⭐ **G 组＝战略地图视口/贴边滚动 + 子界面文本矩形与居中基准；H 组＝候选（2026-10-14）**。用户 `m02724` 报三件事（图1「更多选项」面板回旧位置、图2 战略地图一动鼠标就破碎、图3 未动鼠标正常、图4 子界面仍居中在旧 800×600 区域）。逆向报告 `work\peg\out\report-secondary-ui.md`（14 处确证 + 8 处候选，逐条带 VA/字节/推断链）。
    * **S2 战略地图撕裂**：视口设置器 `0x424C73` 的两个调用者 `0x45A0AF`/`0x45A945` 仍传旧 799/571（`0x45A0F2`/`0x45A0F7`、`0x45A94B`/`0x45A950`），而同一矩形的代码孪生 `0x41C4D7/DB` 与数据副本 `0x4A4DE8` 早已打成 1919/1052 ⇒ **只补了一半**；再加「鼠标贴边滚动」判定仍比 799/599（`0x4567C4`/`0x4567DE`/`0x4568E2`/`0x4568FC`/`0x456984`/`0x456A3E`），鼠标到 x=799 就误触发滚动。**用户截图指纹**：图2 里 x≈775（＝旧屏宽 800 附近）出现竖直接缝、左侧与右侧是不同滚动位置。
    * **S3 子界面居中**：全 exe 唯一文本路径 `0x4700C6` 把 RECT `(0,0,800,600)` 交给 `DrawTextExA`（flags 0x410，38 个 UI 站点共用）⇒ `0x4700DD` 800→1920、`0x4700E4` 600→1080；`0x43BCF7` 用 `400 − 文本宽/2` 硬居中、`0x43BCAB` 写 right=400 ⇒ 两者 400→960（＝w/2）。
    * **S1「更多选项」面板位置（本轮未打）**：按钮表 `0x4A22xx` 已补，面板表 `0x4A96E8`（stride 15B、0x110 条、12 个消费点）一个字节未补；几何自证映射＝右对齐 `+1120`、中部面板 `+560`（idx97 (345,23)-(778,585)、idx9 (10,576)-(790,594)），但该表运行期被 `0x45E4B1`（`mov word[ecx+0x4A96E8],dx`，ecx=idx*0xF）改写，且 `0x41407A` 还会加运行期偏移 `[0x4AF320]` ⇒ **必须先用运行期断点取证**（记录号 + 是否被覆盖），不能盲打。
    * **H 组候选（默认打，`--no-extra` 可关）**：`0x42E497`/`0x42E49C`（登记整屏重绘区，留 599/799 会让 y>599 永不重绘）、`0x46CF45`/`0x46CF4E`（25×25 格子绘制器边界剔除，`jge` 独占上界故用 w/h 而非 w-1/h-1）。
    * **误报排除（不要动）**：`0x414649`/`0x414668`/`0x4146E8`（截图步幅）、`0x46B2AB`（memset 字节长）、`0x4250EC`（jmp rel32 位移）、`0x43BBC4` 提示框 `(100,10)-(700,590)`（当前无此症状）。
    * **更正第 59/60 条里的说法**：`0x45696D` 写的 `[0x4A42EC]` 全 exe **只有 2 个引用、都是写、没有任何读取点**，是废弃的日志 int 槽（值 799），因此已落地的 799→1919 **无害也无用**，不回滚、也不再当作 UI 坐标。
    * 站点总数 **162 条**（96 尺寸 + 10 代码侧 + 4 A + 1 B + 30 D + 3 F + 14 G + 4 H）；`--selftest` 输出「✅ 内存补丁完成：162 条已写入并回读一致（exe 文件未改动）」。落档：`docs\66` 新增 §5.8。
    * **方法论**：判断「某个常量是否已经补过」要连同**同矩形的孪生（代码孪生 + 数据副本）**一起查——S2 就是只补了一半（`0x41C4D7/DB` 与 `0x4A4DE8` 补了、`0x45A0F2/F7` 与 `0x45A94B/50` 漏了）才出现接缝。
64. ⭐ **I 组：0x4A96E8「面板布局表」右对齐记录 +1120（2026-10-14，静态可打已确证）**。为修「更多选项」这类弹出面板仍留在旧位置，逆向产出 `work\peg\out\report-panel-table.md` + 机器可读清单 `work\peg\out\panel_table_manifest.tsv`（272 行，列：idx/VA/x1/y1/x2/y2/w/h/+8/+a/+c/role/dx）。
    * **表结构**：`0x4A96E8` 起，**stride 15 字节、0x110=272 条**记录；每条 `x1@VA`、`y1@VA+2`、`x2@VA+4`、`y2@VA+6`（word）。
    * **静态可打的确证**：全 exe 对该表基址只有 **1 处写**——`0x45E4AE mov word[ecx+0x4A96E8],dx`（函数 `0x45E334`），其 idx 只可能取 **264/265/266**（`0x45E487`/`0x45E49D`/`0x45E495` 三条 `mov word[ebp-0x30],0x10x`），偏移 +2/+4/+6 的绝对引用也全在同一写入块 ⇒ **idx 0..263 的几何字段运行期绝不被写**。另：运行期 x 偏移 `[0x4AF320]` 只有 {0,7,8}（19 写 7 读），不影响锚定。
    * **只打 37 条**：`role=RIGHT(+1120)` 且宽 ≤ 500（右边缘小元素：菜单/标签/提示框，含 idx97 `(345,23)-(778,585)`），它们必须和已补的工具栏按钮一起 +1120 才对齐；宽 > 500 的跨屏长条（idx2/7/9/112/203）不动；`MID(+560)` 93 条与 `PANEL(+560)` 3 条**不动**（它们与面板内部按钮成组，只移背景会把按钮从面板上拆下来）。清单文件 `work\peg\out\panel_table_v1.tsv`（生成脚本 `work\peg\_gen_panel_table.py`）。
    * **站点总数 236 条**（96 尺寸 + 10 代码侧 + 4 A + 1 B + 30 D + 3 F + 14 G + 4 H + 74 I）；`--selftest` 输出「✅ 内存补丁完成：236 条已写入并回读一致」。开关：`--no-panel` / `--no-extra` / `--no-tooltip`。
    * **若还要精确定位**：报告给了断点方案 `0x47053F`／`0x4709B0`（函数 `0x4704D2`/`0x47097A` 内 `add eax,0x4A96E8` 之后，抓 EAX 与 `[ebp+8]`，`idx=(EAX-0x4A96E8)/0xF`；`0x470545` 可直接读实画矩形），一次运行即可定案；因为 `0x4704D2` 有 233 个调用点、idx 多为运行时变量，静态无法唯一确定「更多选项」属于哪几条。
65. ⭐ **K 组：res_diff_v4.tsv 里被跳过的 165 条 dx/dy 位置行（2026-10-14；用户「没任何变化」后的转向）**。
    * 事实：`work\peg\out\res_diff_v4.tsv` 共 259 行 = 96 尺寸行 + **163 dx + 2 dy**。`patch_res_wh.py`（默认 `--keep-dx`）与最初的 `peg_launcher.py` 都跳过了这 165 行。
    * 这 165 行**全在 .data**（`0x490000` 段 70、`0x4A0000` 段 95），`old` 集中在 **750–790**（`762`×73、`787`×71＝工具栏按钮 x/right 的**副本表**），另 2 条底部值 576/594。
    * 推论：D 组把 `0x4A22F8` 记录表的真按钮搬到了 1882/1907，但副本表仍是 762/787 ⇒ 读副本定位的代码（弹出面板/菜单/提示框）仍画老位置，与用户「打开更多选项后面板回到原位置」一致。
    * 映射：`dx` ⇒ `old+(w-800)`（1920 ⇒ +1120）、`dy` ⇒ `old+(h-600)`（+480）。`peg_launcher.py` 的 `add()` 自带去重＋冲突检查：与尺寸表/D 组重叠且目标一致 ⇒ 自动合并（实测一致，无冲突；这是一次额外的交叉校验）。
    * **站点总数 372 条**（96 尺寸 + 165 dx/dy 中的 136 条新站点 + 10 代码侧 + 4 A + 1 B + 2 D + 3 F + 14 G + 4 H + 74 I），`--selftest` 通过：『✅ 内存补丁完成：372 条已写入并回读一致（exe 文件未改动）』。回滚开关 `--keep-dx`。
    * 背景取证：用户 19:15 实机跑 162 条版、19:33 实机跑 236 条版（`work\peg\out\launcher-log.txt` 两次都记『✅ … 已写入并回读一致』『▶ 已放行』），但反馈『对比之前，没任何变化，之前有的问题全部还在』⇒ 说明 G/I 两组定位的那些站点**并不是**这三个症状的实际控制点；日志同时证明启动器与补丁机制本身有效（A/B/D 组效果肉眼可见：16:9、按钮到 1882）。
    * 下一步（若 K 组仍无变化）：做 `--trace` 探针（`DEBUG_ONLY_THIS_PROCESS` + `Wow64GetThreadContext`，在 `0x41EB70`/`0x424C73`/`0x4704D2`/`0x44C66E` 下 INT3，把实参写进启动器自己的日志），一次运行拿到「实际画的矩形/记录号」，不再静态猜。
66. ⭐ **宽屏方案从「逐常量盲测」转为「分层策略 + 运行时几何拦截 + 证据驱动」（2026-10-14，用户 m02941 要求出靠谱方案）**。落档 [`docs\67-PeG宽屏方案（分层策略与实施路线）.md`](docs/67-PeG宽屏方案（分层策略与实施路线）.md)。
    * **判断依据（务必记住）**：G/H/I 三组补丁实机**零可见变化**，K 组（165 条 dx/dy 整批 +1120）造成左栏文字右移 + 大黑洞，**已回退默认不打**（`--dx` 才开）。⇒ 战略地图接续绘制、子界面居中、「更多选项」面板位置这三类症状的**控制点不在常量上，而在函数行为上**；继续扫常量是死路。
    * **分层**：L1 显示层＝DDrawCompat v0.7.1（`26275ed572a4df16141b26e952b50106`，i386，已收档 `archive\ddraw\`）当默认 ddraw.dll，`--ddraw` 启动前换入/退出还原 ⇒ 整类消灭色键/透明/拖影；L2 分辨率常量＝现有 236 条（**冻结，不再加**）；L3 几何策略层＝**拦截函数改实参**（`0x41EB70` 位块、`0x424C73` 视口、`0x4704D2` 布局表读取、`0x44ACDA` 控件绘制、`0x4700C6` 文本矩形、`0x41FF8A` 视口上屏），按元素类别（右栏 +1120／左锚不动／全宽拉右端／居中 960/540／面板容器连子项）制定唯一策略表；L4 输入一致性＝鼠标屏幕→格子换算必须与渲染共用同一套视口全局（`[0x4AF2F8]`/`[0x4AF2FC]`，鼠标缓存 `[0x4AF2E8]`/`[0x4AF2EC]`），修用户 m02926 报的「x>800 点选错位/点不中」；L5 特殊画面归入 L3；L6 每次运行自动留日志、一次只改一类、无证据不算完成。
    * **实现 α（先做）**：`CreateProcessW(DEBUG_ONLY_THIS_PROCESS)` + 目标 VA 写 `0xCC` + `Wow64GetThreadContext`/`SetThreadContext` 读写寄存器与栈 ⇒ 纯 Python、免汇编、免注入、exe 零改动、天然带日志。**β**（性能不够时）：`VirtualAllocEx` 代码洞 detour。
    * **社区对照结论**：宽屏修复 DLL/ASI 的「hook 引擎几何函数」模式最贴合 PeG；MultiCAD 不适用（无独立图形模块）；OpenGen/VCMI 是重实现；DDrawCompat/cnc-ddraw 只管 API 语义；十六进制改常量+启动器只能解决常量类问题。
    * **路线**：P0 拦截器+trace（只记录不改写，自测用 32 位进程）→ P1 带 DDrawCompat 采证据 → P2 分类实施 → P3 输入一致性 → P4 特殊画面与分发。


67. ⭐ **运行时取证器 `peg_trace.py`（停止盲测；P0 落地，2026-10-14）**

* **背景判读**：236 条常量补丁连跑两轮实机，用户两次反馈「没任何变化 / 还是老样子」（m02865、m02892）。结论：**常量猜谜路线停止**，改用运行时取证（`docs\67` §6）。
* **脚本**：`work\peg\peg_trace.py`（约 720 行）。`CreateProcessW(DEBUG_ONLY_THIS_PROCESS)` 直接创建游戏进程当调试器；`CREATE_PROCESS_DEBUG_EVENT` 时读 32 位 PEB 取模块基址；校验母本 md5 `c462e897b3aa1c384870c857ce9e01df`；先用与 `peg_launcher.py` 同一套 `build_plan` 写 236 条尺寸补丁（先全量校验→统一写入→回读一致）；再在探针函数入口写 `0xCC`。
* **探针（`POINTS`）**：`0x41EB70` 位块助手（x,y,src面,RECT*,color,flags）· `0x424C73` 视口设置器（left,top,right,bottom,flag）· `0x43CDCE` 屏幕→地图坐标（战斗图）· `0x44B1D7` 战略图映射 · `0x41C342` 视口右边界 · `0x41FF8A` 视口窗口→后备 · `0x4700C6` 文本排版 · `0x448E94` 选格判定。每次命中记录「函数 / `[esp]` 调用方返回地址 / 栈上参数 / 鼠标·滚动·视口快照」；每断点上限 `POINT_CAP=24` 次，到顶撤断点防拖慢。
* **三个已实测的坑（重要，勿重犯）**：① 64 位调试器看 WOW64(32 位) 进程时 **INT3 命中码是 `0x4000001F`（STATUS_WX86_BREAKPOINT）**，单步是 `0x4000001E`；不认就表现为「断点没命中」，继续执行时 `0xCC` 还在 ⇒ 死循环 + `0xC0000005` @ 断点+2。② **`DEBUG_EVENT` 字段偏移在 64 位调试器下不同**：事件头 12 字节 + 4 字节对齐，联合体从 +0x10 起（EXCEPTION：code@+0x10、addr@+0x20）。③ **Dr 硬件断点在 WOW64 下不可用**：两种上下文写法都「成功」但不触发且弄崩被调试线程（`work\peg\_dr_test.py` 证据）⇒ 默认不用 Dr，改 INT3 + 状态快照。
* **自测**：`python peg_trace.py --selftest-debug`（用 SysWOW64 的 32 位测试进程，脚本未启动游戏）→ `① INT3 断点 ✅`、`② Dr 跳过`，连跑 3 次稳定。
* **用户入口**：`work\peg\_make_forensics_cmd.py` 生成 `D:\Program Files\PeG\诊断-16比9取证.cmd`（GBK + CRLF + 命令全 ASCII），另建快捷方式 `诊断-16比9取证.lnk`；日志 `work\peg\out\trace-log.txt`，窗口实时滚动命中。
* **教训**：静态推断「某个字面量 → 某个症状」在 269 个站点规模下不可靠；两条证据链（静态清单 + 运行时参数）必须闭合才动补丁。

68. ⭐ **DDrawCompat 换层实测：画面能出、输入全死；启动器 --dx 重复参数已修**（2026-10-15）
- 事实：换入 DDrawCompat 0.7.1（`archive\ddraw\ddraw-DDrawCompat-0.7.1.dll`，md5 `26275ed572a4df16141b26e952b50106`）后游戏能启动、能渲染 1920x1080，但**鼠标完全不动**（用户实测）。换回 Svens 包装（md5 `337866f0c870384f5a16c8a11c46a963`，159,232 B）即恢复。
- 取证收获：DDrawCompat 留下 17.7 MB / 149,621 行**逐次 DirectDraw 调用日志**（`D:\Program Files\PeG\DDrawCompat-PeG030.log`）：`SetDisplayMode(1920,1080,16)`、`SetColorKey(&surf, 8, {0xf81f,0xf81f})` 3795 次、`CreateSurface` 3800 次（多为 caps 0x840 的系统内存小块）、`Lock/Unlock` 3791 对、`Blt` 655、`BltFast` 190、`Flip` 仅 2 次、`GetDC/DrawTextExA` 各 6-7 次。关键形状：`BltFast(&P,0,0,&P,{0,0,800,600},16)`（2 次）、`Blt(&P,{0,0,80,60},&P,{1209,565,1289,625},0x1000000)`（186 次，保存/恢复 80x60）、`Blt(&P,{1209,565,1219,583},&P,{0,0,10,18},0x1008000)`（186 次，与取证器抓到的那次命中一致）。
- 输入死的判断：DDrawCompat 默认 `FullscreenMode = borderless`（自建无边框窗口盖住游戏窗口 ⇒ 游戏收不到鼠标消息）。已加 `--play` 试玩配置（ini = LogLevel=info + FullscreenMode=exclusive(0) + MouseSensitivity/MousePollingRate=native + GdiInterops=all），入口 `D:\Program Files\PeG\进游戏-16比9-DDrawCompat试玩.cmd` + 同名 .lnk；应急还原入口 `还原显示层.cmd`；已删除三个失效的「诊断-*」入口。
- 启动器：`peg_launcher.py` 的重复 `--dx/--keep-dx` 参数已修；现默认 **236 条**、`--dx`（仅水平位移的 163 条 dx 行，去重后）**372 条**；自测均通过（先校验、再写入、回读一致，exe 未改）。
- 纪律：换层脚本必须「换入前校 md5，无论怎么退出都 finally 换回」；窗口被强关会漏还原 ⇒ 保留 `--restore` 入口；调试器路线（DEBUG_ONLY_THIS_PROCESS）在 32 位进程上会让游戏建不出窗口，已废弃。

69. ⭐ **DDrawCompat+独占全屏 首次拿到「输入+文字+无色键异常」**（2026-10-15，用户 m03523 实测）
- 配置：DDrawCompat 0.7.1 + `FullscreenMode = exclusive(0)` + `MouseSensitivity/MousePollingRate = native` + `GdiInterops = all`，其余同 236 条内存补丁。
- 结果：①**鼠标可以动、可以点**（输入问题由 `borderless` → `exclusive` 解决，证实「borderless 自建窗口盖住游戏窗口」的判断）；②**悬停按钮出说明文字**（GDI 文本在这层是好的）；③**完全没有品红**（色键在这层是真正生效的）；④**地图不显示，且带上一屏残留**；⑤**截图全黑**（独占全屏截不到，borderless 能截）。
- 意义：色键（品红）+ GDI 文字这两类问题**在显示层这层就解决了**，不需要再改 exe；剩下的是「地图层不显示/残留」。
- 下一步：同入口改 `--mode borderless`（画面/截图已知正常）+ 原生鼠标，验证「鼠标死」到底是 borderless 本身还是 DDrawCompat 的鼠标模拟；若 borderless+原生鼠标输入正常 ⇒ DDrawCompat 路线四要素（画面/输入/文字/色键）齐活。
- 工具：`work\peg\diag_ddraw.py` 现有 `--play [--mode exclusive|borderless]`、`--restore`、`--selftest`；入口 `D:\Program Files\PeG\进游戏-16比9-DDrawCompat试玩.cmd`。
70. ⭐ **M 组：地图面/地图绘制界 1920 → 4096（2026-10-15，根因定位；默认开打）**。治「进场景后地图不显示 / 移动两下就全黑 / 再动几下又有几率正常」。
    * **根因（反汇编确证）**：`0x41FF8A` 是每帧「地图上屏」——`src.left = x = [ebp+8]`、`src.top = y = [ebp+0xC]`、`src.right = x + ([0x498D40] - [0x4AF300]) + 1`、`src.bottom = y + ([0x498D44] - [0x498D3C]) + 1`，随后 `BltFast(dst=[0x676904] 后备缓冲, dstX=[0x4AF300], dstY=[0x498D3C], src=[0x655574] 地图面, &rect, 0x10)`；失败**只记日志**（`0x42000B` push `0x491308` / push `0x420` / call `0x437420`），不回退。源窗口 = 滚动坐标 + 视口宽高，而地图面只有 1920x1920（母本给 800x600 视口留了 1120 余量）；我们把视口补成 **1920x1031 后余量归零**（x>0 或 y>889 立刻越界）⇒ 这一笔整笔失败 ⇒ 地图区域保留黑/旧内容。
    * 同理，31 处绘制界的 `cmp …, 0x780` 会把世界坐标 >1920 的地块/直写剔除 ⇒ 右侧成片锯齿状空洞。
    * **地图面描述符**：面 A `[0x655574]` 在 `0x441BE5-0x441C22`（dwSize=0x7C、dwFlags=7、dwHeight 立即数 `0x441BFD`、dwWidth 立即数 `0x441C04`、caps 0x840 = OFFSCREENPLAIN|SYSTEMMEM），`CreateSurface([0x6761E0])`；面 B `[0x622A10]` 同构，立即数 `0x441C90`（高）/`0x441C97`（宽），`push 0x622A10` 在 `0x441C9E`。
    * **31 处 0x780 清单**（扫描器 `work/peg/_find_map_sites.py`；`work/peg/_plan_vs_780.py` 核对：与 236 条计划的立即数地址**零交集** ⇒ 全是母本原有，不是我们补出来的）：`0x41F3FA`；`0x424AD3`/`0x424ADA`/`0x424B31`/`0x424B38`/`0x424BA6`/`0x424BB1`/`0x424BE9`/`0x424BF4`；`0x43D733`/`0x43D747`/`0x43DB03`/`0x43DB72`/`0x43DB83`(imul 行距)/`0x43DEC7`/`0x43DF37`/`0x43DF48`/`0x43E2F0`/`0x43E360`/`0x43E371`/`0x43E6B5`/`0x43E725`/`0x43E736`；`0x441BFD`/`0x441C04`/`0x441C90`/`0x441C97`；`0x455BB6`/`0x455BBD`/`0x455BE1`/`0x455BE8`。全部字节 80 07 00 00 → 00 10 00 00（1920 → 4096），让面与所有界/行距自洽，滚动余量恢复 2176。
    * **落地**：`work/peg/peg_launcher.py` 新增 `MAP_SITES`（31 条 (va, note)）+ `build_plan(..., mapmargin=True)` 第 11 组 + CLI `--no-map`；`--selftest` 输出 **267 条**已写入并回读一致（236 + 31）。试玩链 `diag_ddraw.py --play --mode borderless` → `diag_run.launch_patched` → `build_plan(tooltip=False, extra=True, panel=True, dxdy=False)`，**默认就带上 M 组**，不需要新入口。
    * **B 组语义澄清（推翻旧猜测）**：`patch_fullrepaint.py` 在 `0x4489D8` nop 掉的是 `je`，语义是**改成每帧都走整屏刷新**——原始逻辑 `if(word[0x498D74]!=0 && byte[0x4AF360]==0){ call 0x44AC45 整屏刷新(顶栏 0x44C50A + 底栏 0x44C57B + 控件循环 0x423CD6); word[0x498D74]=0 } else { call 0x423CD6 控件增量 }`（标志置 1 于 `0x425CA8`）；所以「B 组导致黑」不成立。
    * **DDrawCompat 旁证**：`D:/Program Files/PeG/DDrawCompat-PeG030.log`（borderless + LogLevel=info 那次，190 行、12:50:42→12:53:09）只有配置与钩子记录、**无任何 Blt 失败行**；确认 `FullscreenMode=borderless`、`GdiInterops=all`、`MousePollingRate=native`、`MouseSensitivity=native` 都生效，`Using resource format: D3DDDIFMT_R5G6B5, plain, sysmem`（R5G6B5 离屏面被支持）。
    * **纪律**：`diag_ddraw.py --restore` 必须在下一轮测试前跑（本次实测后 ddraw.dll 停在 DDrawCompat v0.7.1 = 3,612,672 字节、ini 还在，已手工还原成 Svens 159,232 字节 / md5 337866f0c870384f5a16c8a11c46a963）。
    * **待验证**：请用户重开同一入口看地图滚动是否还黑；若仍黑，把 play ini 的 `LogLevel` 改成 `trace`，统计失败的 `BltFast` 调用（含源矩形）即可定案。
