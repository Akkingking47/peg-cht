# 子工程：PGForever（`D:\PGForever1.021`，自用）

> 2026-09-24 从 `MEMORY.md` 拆分（主文件超长被注入截断）。**处理 PGForever 前必读本文。**
> 工作区 `D:\DSH\军事游戏汉化\pgforever\`（docs/work/tools/backup/poc）。
> 配套文档：`pgforever\docs\05-中文长文本截断修复.md`、`06-新回合横幅英文残留定位与汉化.md`、`07-全库汉化完成报告.md`。

---
- 与 OpenGen **不是同一引擎**：`PGForever.exe`(753KB) + `htmlayout.dll`，UI 由 HTML 渲染 `Default\UI\*.htm`（及各 game 自有 `UI\`）。**无多语言框架** → 必须就地替换原文，无回滚键，`backup\origin\` 是唯一回滚依据。
- 工作区：`D:\DSH\军事游戏汉化\pgforever\`（docs/work/tools/backup/poc）。
- **编码铁律：UI 的 .htm 必须写 UTF-8 with BOM**（无 BOM 会被按单字节解析 → 中文全变 `?`）。数据文件 `.pgeqp`/`.pgscn`/`.pgcam` 为 UTF-16LE+TAB；`.pgbrf` 为 UTF-8/ASCII 的 `<p>` 片段。
- 界面文字有三种来源，改文件无效时先辨别：① htm 静态文本（已汉化）② **exe 按元素 id 运行时注入**（`PurchaseText`/`WhatIsFinished`/`UnitCloseDefName` 等）③ 图片烘焙标题（`casualties.png`/`purchase_header.png`/`upgrade_header.png`）。
- 修改流程：改 `work\ui\translations.json` → 跑 `tools\apply_ui.py`（自动从 backup 取原文、校验、写 BOM）。**不要直接编辑游戏目录的 htm**。
- 译表要点：`per_file` 处理同词不同义；按 en 长度降序替换；纯字母串加词边界；`%%` 是 HTMLayout 转义须保留。
- ★★ **同词不同义不要用 `per_file`（文件级粒度不够）**——同一文件内可能有不同语境的同名词。
  **正解：用「含 HTML 标记的短语规则」锁定语境**。本例：
  ```json
  "global": {
    "Close": "关闭",                 // 兜底：独立词 → 菜单按钮
    ">Close</span>": ">抵近</span>",  // 限定 span 内 → 属性面板 Close Def = 抵近防御
    "</span> Def": "</span>防御",
    "Close Defense:": "抵近防御:",
    ">Close<": ">关闭<"
  }
  ```
  配套：`apply_ui.py::replace_all` **仅对纯字母词加 `(?<![A-Za-z])` 词边界**；
  含标记/空格的短语**直接字面替换**（否则 `<` `>` 导致规则失效）。`_` 开头键视为注释跳过。
- ★ **一词两义必须按语境拆分**（用户明确要求）：菜单按钮的 `Close`=关闭；部队属性面板 `Close Def`/`Close Defense`=抵近防御（军事用语，**不要译「近距」**）。
- **exe 硬编码可汉化**：UI 文案是 UTF-16LE 宽串，集中在 `.rdata`（VA 7F000 / 偏移 0x7E200），无数字签名；铁律「译文字符数 ≤ 原文字符数」即可原地替换，只改数据不动指针 → 不受 ASLR 影响。
- **环境限制**：本机 GUI 自动化不可靠（窗口尺寸/位置漂移、桌面浏览器覆盖、合成输入失效）→ 用「换位渲染验证」`tools\verify_dialogs.py` 验证对话框。
- 进度：POC ✅、L1 UI 层 ✅（51 htm / 943 处）；下一步 L2–L5 PG 文本；未决高风险项 `MAPNAMES.STR`（定长二进制）。

## ★ PGForever 关键技术结论（2026-09-21，极重要）

### 数据层中文乱码的根因与解法（已解决）
- **根因**：exe 导入 `HTMLayoutSetElementHtml`（**窄字符版，HTMLayout 按 UTF-8 解析**）。
  引擎读 UTF-16 数据文件得到宽字符后，用 `WideCharToMultiByte(CP_ACP=936)` 转成 **GBK 字节**再交给它
  → HTMLayout 按 UTF-8 解析 GBK 字节 → 中文乱码（1:1 错字映射，如"西线"→"η↓"）。
- **解法**：给 **exe 的嵌入 manifest** 追加 `<activeCodePage>UTF-8</activeCodePage>`，
  使该进程 `CP_ACP = 65001(UTF-8)` → 转换输出 UTF-8 → HTMLayout 正确解析。
- **注意**：`PGForever.exe.manifest` 外部文件**无效**（exe 已有内嵌 RT_MANIFEST，系统忽略外部）。
  内嵌 manifest 在文件偏移 **0xAC27C**，数据区 **Size=346**；压成单行并去掉 `trustInfo`（默认就是 asInvoker）
  后为 246 字节 ⇒ **等长就地替换**、文件大小与资源结构零改动。脚本 `pgforever\tools\patch_manifest.py`。
- 只影响该进程，不动系统设置、不影响其他程序。

### ⚠️ 已废弃结论（勿再沿用）
**「UTF-8 缓冲区按字符数分配（P2 @0x6CA3E）」是错误诊断**。
`0x6CA3E` 位于 **`fwrite` 内部**（`0x46D05C`）的 W2M，**与屏幕显示完全无关**，只影响写文件的长度计算。
这就是 P2 施加后中文截断依旧的原因。**建议评估后回退 P2。**

### ★★ 中文长文本截断真因与修复（P4，2026-09-21 最终定位）
- **症状**：战役列表前 3 条正常 → **第 4 条描述变 `伯body>`** → **第 5 条整条消失**；
  超长中文更糟（只显示 3 条，第 3 条中间截断）；**英文原版完全正常**。
- **加载路径**：`pg.pgcam` → `0x4517E0` 生成 HTML（`sprintf 0x48DA60` → `std::wstring::append 0x413EB0`）
  → `0x4014C0` 按 id 遍历设置（`HTMLayoutVisitElements`, id=`ScnList`）→ 回调 `0x4031B0` → vtable `0x482104[0]`
  → **`0x401680`**。简报 `*.pgbrf` → `briefing.htm`+id`BrfText` → `0x4475C0` → **`0x4476A0 call 0x4014C0`** → 同一函数。
- **根因**：`0x401680` 里 `push 3(CP_UTF8); call 0x402B50`（W2U8，宽字符→局部 std::string 的 **UTF-8 字节流**），
  但长度 `mov eax,[edx-0xC]` 取的是**源宽串的字符数**，且 `htmlLength` 官方要求 **UTF-8 字节数**
  ⇒ 接口只解析前 N 字节 ⇒ 标签不闭合、后续项丢失、回落默认模板泄漏 `body>`。
  **英文无碍**（ASCII 字节数==字符数）；截断比例随中英混合比浮动（观测 ~2/3）。
- **修复（P4，6 字节等长 NOP）**：`0x402B50` 返回时 **eax 恰为实际写入的 UTF-8 字节数**（尾部只改 ebx），
  故把 `0x4016A0` 的 `8B 56 04 8B 42 F4`（`mov edx,[esi+4]` / `mov eax,[edx-0xC]`）整体 NOP 即可。
  文件偏移 **0xAA0**，大小恒 753664。脚本 **`tools\patch_exe_all.py apply-p4|revert-p4|status`**。
- **验证**：未打补丁＝3 条 + 第4条body> + 第5条消失；**已打补丁＝5 条全正常**。
  超长中文（95字/249字节）对照：未修 3 条且截断 vs **已修 5 条完整折行**。截图 `poc\cam_shot_*.png`。
- **全调用点审计**（`tools\audit_sethtml.py`）：11 处 `SetElementHtml` + 11 处 `SetElementInnerText16` 中，
  **只有 `0x4016B6` 一处内容来自 W2U8** ⇒ 只需修这一处。其余内容为内存既有 UTF-8 串/常量，长度正确。
- **教训**：① 别反复猜栈偏移，看转换函数**返回值语义**更可靠；② 传 `-1` 给 `SetElementHtml` **会崩**（实测）；
  ③ 该调用点执行过早，调试器附加来不及 ⇒ **放弃调试器，用「改1处+截图」对照闭环**最高效。
- 文档：`pgforever\docs\05-中文长文本截断修复.md`
- 新增可复用工具：`iat_dump.py`（PE 导入表，节表换算）、`dis_at.py`（任意 VA 强制反汇编）、
  `audit_sethtml.py`、`cam_shot.py`、`len_probe.py`、`stress_pgcam.py`。

### ★ P3：L7 exe 硬编码文案（已做 77 处）
- 提取 `.rdata/.text/.data` 宽串 815 条 → 可见文案 188 条 → 翻译 **77 处**（单位类别、战斗结算、
  场景设置、提示、错误信息）。
- 铁律：译文字符数 ≤ 原文，不足补 `\0\0`；写前校验偏移字节 == 原文；白名单保护命令协议
  （`purchase %d %d %d` 等）、文件名（`SCENSTAT.BIN`/`unittypes.pgeqp`/`PG Forever`）、格式符（`%d`/`%%`/`&nbsp;`）。
- 脚本 `tools\extract_exe_strings.py` + `tools\patch_exe_strings.py`；译表 `work\exe\translations.json`。

### ★ P5：新回合横幅英文残留（已做 22 处，2026-09-21）
- **现象**：进战役后横幅半中半英 —— `Axis 回合 1` / `September 1, 1939` / `Clear(Dry)`。
- **定位**：`回合` 是 `newturn.htm` 模板静态文字（已汉化）；英文残留由 exe `0x4074A0` 横幅函数
  **按元素 id 运行时注入**（→ `0x4016E0` → 6 个 `<span id=Side/CurrentTurn/Time/Date/Weather/TurnsRemaining>`）。
  **改 htm 对残留无效。** 日期 `0x406C95 push 0x482B24`（`%s %d, 19%d`）+ 月份指针表 `0x482AF0`；
  天气 `0x404ADA push 0x482A24`（`%s(%s)`）+ 标志表 `0x49DA40/0x49DA50`。
- **之前漏掉的原因**：L7 的 77 条只覆盖单位类别/战斗结算/场景设置/提示/错误，**不含阵营/月份/天气**。
- **P5 译法**：阵营 `Axis→轴心` `Allied→盟军`；12 个月份 → `1月`~`12月`；
  日期格式串 `%s %d, 19%d` → `%s%d日, 19%d`（**恰好 11 字符等长**，参数序 `%s`月/`%d`日/`19%d`年）；
  7 个天气 → `冰冻/泥泞/干燥/降雪/降雨/阴天/晴朗`。天气模板 `%s(%s)` 保留 → 显示 `晴朗(干燥)`。
- 脚本 `tools\patch_banner.py`（**幂等**，可重复运行）；文档 `docs\06-新回合横幅英文残留定位与汉化.md`。
- ★ **查重必须加 NUL 终止符**：短串（`Axis`/`May`/`Dry`）必然作为子串出现在长串中，
  裸字节查会误判「多处命中」而不敢改；加 `\x00\x00` 后每个都恰好唯一。

### exe 补丁与回滚链（文件恒 753664 字节）
| 备份 | 内容 |
|---|---|
| `backup\origin\PGForever.exe` | 原版 |
| `backup\PGForever.before-w2m-patch.exe` | +P1 manifest |
| `backup\PGForever.before-L7.exe` | +P1+P2 缓冲区 |
| `backup\PGForever.before-len-fix-P1P2P3.exe` | +P1+P2+P3（P4 前） |
| `backup\PGForever.before-banner-P1P2P3P4.exe` | +P1+P2+P3+P4（P5 前） |
| **现行** | +P1+P2+P3+P4+**P5 横幅**（md5 `da216eadceb3149f41ab98d9f90bfdfb`） |

### 环境与验证方法（务必遵守）
- **截图用 `PrintWindow`**（flags=2），**不要用屏幕 BitBlt**：桌面浏览器会遮挡游戏窗口。
- 窗口固定 **500×600 @ (710,220)**，`SetWindowPos` 改尺寸会被游戏改回。
- ⚠️ **GUI 自动化在本机彻底不可用**：即使最小化全部其它窗口，`SetForegroundWindow` 仍失败、
  `GetForegroundWindow()` 恒不为游戏窗口；合成鼠标/键盘到达不了游戏（点后画面不变）。
  **⚠️ 更正：这不是"只能用截图"。`PostMessage(WM_LBUTTONDOWN/UP)` 可直接合成点击、
  绕过前台焦点限制（见下「PostMessage 突破」）。"任何需点击的验证必须交给用户"为错误结论。**
- 替代目视：`tools\ink_scan.py` 按行统计"文字墨迹"像素判断文本是否完整
  ⚠️ **有噪声**（同一 exe 两次测得 3573/2458），仅作定性参考。

### ★★ 三条硬结论（2026-09-21 新增，务必先读）
1. **凡引擎按 `CP_ACP` 解码的单字节资源，一律写 UTF-8，不写 GBK**。
   因 exe 内嵌 manifest 已设 `activeCodePage=UTF-8` ⇒ 该进程 `CP_ACP=65001`。
   适用于：`MAPNAMES.STR`、`*.pgbrf`。⚠️ `.pgeqp/.pgscn/.pgcam` 是 UTF-16LE，另一套机制。
2. **`apply_ui.py` 替换绝不能碰 `<...>` 标签内部**（否则 `id="Experience"`→`id="经验"`，
   exe 注入失效 → 单元格空 → **行高塌陷 → 左右列错位**）。已加 `shield()/unshield()` 屏蔽区。
   译文也不得引入原文没有的半角空格（会改变列宽）。
3. **`PostMessage` 合成点击可用**：不需前台焦点，先发 `WM_MOUSEMOVE` 再 DOWN/UP，
   客户区坐标 `lp=(y<<16)|x`。已实测可进战斗，配合 `PrintWindow` 完成端到端验证。
   ⚠️ 后台启动的进程会随父命令退出 → 「启动+扫描/截图」必须同一脚本完成。

### 数据层进度
- L1 UI（51 htm / 943 处）✅ ／ L2 装备名 283 处 ✅ ／ L3 场景 38 个 ✅ ／ L5 战役 ✅ ／ L4 简报 178 个 ✅
- L7 exe 文案 77 处 ✅ ／ P6 装备表列头 32 字段 ✅ ／ P6b 目标类型+移动方式取值 11 处 ✅
- P7 单元栏 `燃料:%d`+`弹药:%d` ✅ ／ P7 地形名（38 个 MAPNAMES.STR × 记录 0..13）✅
- **★ 河流名 ✅（4229 处）／ 地名（城市名）✅（51401 处，全 38 文件，超长 0）**
- P1 manifest ✅ ／ **P4 中文长文本截断修复 ✅（已实机验证）** ／ P2 缓冲区（方向错误，建议回退）
- 待做：图片烘焙标题（casualties.png / purchase_header.png / upgrade_header.png）；
  单位类别名（`unittypes.pgeqp`）；`Extras\Modifications\Solid background for text\` 备用 UI；
  「防卸」字形（小字号渲染问题，改文本无效，需换字体/调字号）
- 待用户实机验证：**地图上的地名渲染**（合成点击进不了具体场景）、多回合稳定性、装备编辑器整体观感

## ★★★ MAPNAMES.STR 地名汉化（2026-09-21，全部完成）

### 范围与口径
- 记录 **0..13** = 通用地形名（此前已汉化）；**14+ = 河流名 + 地名 + 区域名混合**
- 译表 **4575 条**：`work\mapnames\place_A.py` … `place_Z.py`（A–Z 26 段，覆盖全部）
  + `place_cyber.py`（Cyber General 专属 96 条）＋ `river_zh.py`（河流名，并入）
- 用户口径：**全部译**；小地名 = **音译 + 通名后缀**；
  **加后缀会溢出时降级为纯音译**（不加后缀，直接按通用规则音译）
- 硬约束：UTF-8 **≤19 字节（6 汉字）**，槽内左对齐 + 空格补满

### ★★★ 核心：`Cyber General` 的「偏移 17 字节」结构（曾误判为连续缓冲区）
**错误旧模型**：把该文件当「连续名称缓冲区」用正则 `[A-Z][A-Za-z0-9\-\.\' ]{0,19}` 扫描。
→ 能取名字，**但定位不了写回位置**，且据此写的 `patch_d()` 要求中英等长，
产生 **1391 处假「超长」**（如 `Ancona→安科纳` 9B 本可写入却被判超长）。

**正确模型（决定性实验）**：就是**标准 20B 定长记录**，但槽起点网格有断点：
```
k <= 95  :  S_k = 20 * k
k >= 96  :  S_k = 1937 + 20 * (k - 96)         ← 唯一 +17 偏移
```
**+17 来源**：记录 95 `'Proz'` 被原作者把名称补 NUL 补到了 **37 字节**（非 20），
其后所有记录整体后移 17 字节。另有记录 1119 `'PleStacja'` 占 **40 字节**（=2×20，不产生新偏移）。

**收敛验证（黄金标准）**：用该网格提取全部名称 → 与译表比对
⇒ **1700 命中 / 0 未命中 = 100%**。

**同源瑕疵**：记录 1523 `'Villedieu-les-Poeles'`（21 字符）**溢出槽位并与下一条
`Villers-Bocage` 直接粘连**（无分隔符）—— 原数据瑕疵，写入中文后自然消失。

### 交付物
- `work\mapnames\cyber_names.py` —— **重写**：`rec_start()/slot_len()/slots()/read_name()`，
  偏移以 `PIVOTS=((95,17),(1119,20),(1523,20))` 表达；**已删除错误的「连续缓冲区」模型**
- `tools\patch_place_names.py` —— 统一处理 38 文件；`patch_a_b()`（格式 A：NUL 补满）
  与 `patch_d()`（格式 D：按 20B 槽写回，**不再要求等长**）。
  **新增「读校验」**：实读字节 ≠ 译表键则跳过 —— 防网格算错时把中文写到别人槽里。
  用法：`python patch_place_names.py`（DRY-RUN）／ `--apply`（落盘）
- `tools\verify_place_names.py` —— 端到端进战役验证（PostMessage 手法）
- 备份：**`backup\mapnames-before-place\`（38 个）**；更早的原始英文备份 `backup\mapnames\`

### 校验结果（全通过）
- **38/38 文件大小完全不变**（含 `\r\n`/`\x1a` 尾料的 6 个也一致）
- 汉化记录 **4229 → 55584（+51355）**，DRY-RUN 报 **51401 处替换 / 超长 0**
- 抽样（Cyber General）：`台地 / 贫瘠丘陵 / 丛林 / 雷场 / 基地 / 格诺兹亚 /
  内奥斯特拉 / 因特斯提努姆1 / 普罗兹 / 阿尔隆 / 普莱站 / 维尔纽斯`
- 实机截图：战役列表 5 条**全部完整、无 `body>` 泄漏**

### 教训（已写入技能 `win-game-html-ui-localization`）
1. **定长表里混进「超长槽」时不要判定为「非定长」**：先统计名称起点 `mod REC` 的分布，
   找累积偏移余数 r，再反查哪条槽超长（槽长 = 名称长 + 其后连续 NUL 跨度）。
2. **正则扫描「连续缓冲区」是死路**：取得到名字、定位不了写回位置，命中率还虚高。
3. **写回前必须逐槽「读校验」**（实读 == 译表键才写）。
4. ⚠️ **本机合成点击只能到战役列表，进不了具体场景**（点「开始」只切换选中项）
   → 地图上的地名渲染**需用户实机确认**。


---

## ★★ 全库四类数据文件汉化完成（2026-09-21）

### 覆盖率
`.pgbrf` 3407/3446（98.9%，剩 39 空白占位）、`.pgscn` 1002/1006（99.6%，剩 5 个代号）、
`.pgcam` 44/44、`.pgeqp` 42/42。报告 `pgforever/docs/07-全库汉化完成报告.md`

### ★ 各类文件的「唯一可译区」（务必遵守，误改会破坏游戏）

**`.pgbrf`** — UTF-8 无 BOM 的 `<p>` 片段，段落间 `\r\n`。整体可译。

**`.pgscn`** — UTF-16LE+BOM。**只有两行可译**：`Name\t…` 与 `Description\t…`。
其余（`# Victory conditions` 的 `AXIS VICTORY`/`ALLIED VICTORY`、hex 座标、数值）**绝不能动**。
源 desc 为空（`Description\t`）时必须保持空。

**`.pgcam`** — UTF-16LE+BOM，**按位置解析的定位格式**。**只有 3 类可译**：
1. `# Entry points` 段数据行 **col 0**（入口名，如 `North Africa`→北非）
2. `# Entry points` 段数据行 **col 2**（简介）
3. `# Outcomes` 段每行 **col 0**（`MAJOR VICTORY`→重大胜利）

**绝不能译**（已实证）：
- `# Entry points` **col 1**（`Label in campaign path`）—— 恒等于 `# Campaign path` col 0，是**匹配键**
- `# Scenarios` 段 **col 0**（Label）—— 与 `# Campaign path` col 0 同一键空间
- `# Campaign path` **整段** 12 列：Label / `*.pgbrf` 文件名 / NextLabel / Prestige
- 佐证：exe 内命令协议串 `outcome %s for scenario %s`、`campaign path label %s`

⚠️ 全库 `.pgcam` 只有 **102 条**唯一可译内容（entry_name 38 / entry_desc 41 / outcome 23）。
曾误把 `# Scenarios` col0（1413 条）当可译项 —— **若译会直接断裂战役树**。

**`.pgeqp`** — UTF-16LE+BOM，每行 `ID \t Name \t Class \t 数值…`。
**唯一可译列 = col 1（Name）**；`Class` 是编号（引擎查 `OpenIcons.csv` 取类别名），**绝不能动**。

### .pgeqp 翻译口径（用户确认「功能词 + 著名装备」）
- 兵种/编制/后勤/工事/武器类别/舰船类别词 → 译中文
- 国别**短码后缀** → 译中文（Hu→匈牙利 / Po→波兰 / Bg→保加利亚 / Fi→芬兰 / No→挪威 / Ro→罗马尼亚…）
- 国别**前缀缩写**保留（US/GB/AU/CHN/CCP/RA/RN/FJ/AF/SS/MR/MN/NTRK…）
- 装备型号 / 飞机型号 / 军舰舰名 / 武器型号 → **保留原文**
- **拿不准一律保留**（保守优先）
- 全库 9417 个唯一名 → 译文 8338 条，实际写入 2586 处

### ★ 三个必须记住的坑
1. **尾随空格**：部分原文带尾随空格（`'US M18 '`）→ 生成器必须保留首尾空白，
   否则产生大量"只改空格"的无意义改动，并让 strip 比对全部误报
2. **词边界需禁数字邻接**：`Gr40` 会被当希腊国别码、`MG42` 会被拆成"机枪 42"
   → 正则必须写 `(?<![A-Za-z0-9])…(?![A-Za-z0-9])`
3. **只读文件**：`Extras\Equipment Files\Rubberduck equipment file\AG_equipment.pgeqp` 是 mode 444
   → 写前 `os.chmod(p, stat.S_IWRITE)`

### 部署脚本约定（四套统一）
- 默认 **DRY-RUN**，加 `--apply` 才写盘
- 首次写入前自动备份到 `backup\<name>-origin\<相对路径>`
- 逐条比对原文后才替换；`.pgcam`/`.pgeqp` 按**行+列装配**（同行多列互不干扰）
- `.pgeqp` 部署为**原始值比对 + 幂等**（已应用行跳过）
- 禁用词扫描：支那/鬼子/伪军/共匪/毛子（全库 0 命中）

### 工具
`extract_all_scn.py` / `extract_all_cam.py` / `deploy_all_cam.py` / `deploy_all_eqp.py` /
`gen_eqp_roots.py`（装备词根生成器，约 400 词根 + 覆盖表）/ `fix_zh_ids.py`（译文只写 id，脚本查表补 md5）

### 备份（删改即回滚）
`backup\brfall-origin\` `scnall-origin\` `camall-origin\` `eqpall-origin\`

### 目录/机制要点
- `.set`（地图配置，`..\dat\` 路径 + map0N 内部名）与 `.stm`（u16 地形/胜利点数组）**零可见文本**，不需处理
- `Default\UI` 21 个 htm 被所有战役共享；未译的 3 个是纯布局空壳
- 子代理并行翻译可用，但**会遇到 429 限流**；大批量规则化文本（如装备名）用**词根脚本**更稳
