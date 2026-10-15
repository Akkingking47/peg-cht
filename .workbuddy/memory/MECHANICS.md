# OpenPG 汉化工程 · 机制与坑详情（**非自动注入**，需要时读）

> 配套 `MEMORY.md`（索引级，自动注入）。本文件放"怎么运作 / 踩过什么坑"的细节。
> 2026-09-24 从 `MEMORY.md` 拆出（原文件 19.6 KB 会被注入截断）。

---

## 1. L8 位图文字（全库 18386 图，**仅 3 张**含文字）

| 图 | 尺寸 | 内容 |
|---|---|---|
| `hex_text.png` | 60×950（19 格，步长 50，格 i ↔ 地形 ID i） | 地形标签 |
| `mouse_build.png` | 60×182（14 格，行距 13） | 工兵/运输模式 + 图标 |
| `mouse_missions.png` | 60×104（7 格） | 任务指派 + 红点 |

- `EFILE_Clu\hex_text.png` 是 16×16 灰底圆形象形图标（**非文字**）⇒ 故意不动。其余全是纯图形
  （`buttons_*`/`menu_*`/`climate`/`unitclass`/`uniticovector*`/`attachments*`/`unit_stats`/`mouse_nums`/
  `unitinfo`/`hex_types`/`box_*`/`dlg_*`/`hex_*` 贴图与 `fire_*`/`explosions` 特效）。
- **透明＝色键**（全局 `#F8E4D8`、OPENPG 等 `#FF00FF`、鼠标标签 `#FFFFFF`）；**原图都没有 `tRNS`**（不是 alpha）。
- 工具：`work\gfx\redraw-hextext.ps1` + `terrain-labels-zh.txt`；`work\gfx\localize-mouse-labels.ps1` + `mouse-labels-zh.txt`。
  备份：`backup\hextext-orig\`(9)、`backup\mouse-labels-orig\`(7)。

### 重绘六铁律（违反必出问题）
1. **尺寸/步长一模一样**，否则 blit 坐标全错。
2. 输出仍是 **8bpp 索引 PNG**，且**调色板 index 0 的 RGB 与原图逐字节一致** ⇒ 无论引擎按索引还是按像素值做色键，透明都继续有效。
3. 文字型**关抗锯齿**（或调色板预置混合色），否则边缘像素落在色键外 ⇒ 地图上出现粉/品红毛边。
4. `System.Drawing` 索引格式的坑：**不能** `Graphics.FromImage()`、**不能** `SetPixel()`
   → 画在 32bpp 临时图上再用 `LockBits` + `Marshal::WriteByte` 写索引；`new Bitmap(path)` **会锁文件**，`Save()` 前必须 `Dispose()`。
5. 两道护栏：外接矩形**平均宽度 < 20 px ⇒ 判图标型 SKIP**；成品调色板 256 项 vs 原图 8–17 项 ⇒ `SKIP: already converted`（防二次转换）。
   判据：**主色像素/外接矩形面积 ≥ 0.55 ⇒ 底牌型**，否则文字型。
6. **重跑前必须先从 `backup\hextext-orig\` 还原**（脚本读的是当前文件，不是原图）。

### 鼠标标签两条铁律
1. **只换字，不动框**；擦除区**不能一刀切** —— 带图标的格擦到 x=56 会把图标一起擦掉。
   正解＝**按列剖面检测图标**：该格「文字色」逐列计数得连续段，若**末段与上一段空隙 ≥6 px 且起点 ≥42**
   ⇒ 末段是图标，擦除止于图标前 2 px（字母间距仅 1–2 px，不会误判）。
2. ⚠️ **PowerShell 大小写不敏感**：参数 `[string]$Labels` 与局部 `$labels = @(...)` 是**同一个变量**，
   赋数组时被参数类型约束**强制转成字符串** ⇒ 只处理到第 1 格。**参数名与局部变量名必须严格不同**（`$COLS`/`$cols` 也踩过）。

---

## 2. L9 `.xscn` 场景数据（顶栏地名的真正来源）

现象：鼠标移到格子上，顶部中部显示 `Gan River (Only passable with boats) [10 10]`。

```
[场景数据] <N:0001> [标题: u16 长度+内容] [组1: u16 数量 + 若干(u16 长度+内容)] [组2: …]
```
- **组 `-1` = 场景标题**；**组 0 = 地图地名 / 通行说明**（顶栏整串 = `地名 + (括号说明)`）；**组 1+ = 部队番号编成**。
  编码按 `CP_ACP=936` ⇒ 写 **GBK**。
- **字符串区在文件尾部、文件正好以串结束**（186/187 解析恰好到 EOF）⇒ **改长度无需修补任何偏移**。
- 「会不会溢出」：**不会**。① 全 187 文件指向串区起点的指针 = 0（引擎扫描 `<N:` 定位）；
  ② 24 个文件的"命中串起点" u32 都是 `0x9800`/`0x10000` 类圆整常量，出现率低于随机期望；
  ③ 实测 GBK 中文普遍更短（**91/125 变短**），仅番号类 31 条略增（均 +4）。
- 口径：`Div./Bde./R./Corps` 用**中性** `师/旅/团/军`（同一模板用于中日双方）；日方专有单位用通行译名。
- **OPENPG 特例**：**无番号组**（组 1+ = 0）⇒ 不需编制名对照表与「第 N」规则，`Norm()` 无实际作用。
  ⚠️ PGForever 地图地名表有 **14 条被 19 字节定长槽截断**（`Aix-en-Provence`→艾克斯、`St. Mere Eglise`→圣梅尔…），
  `.xscn` 是变长存储故 OPENPG 侧改用完整译名 ⇒ **两工程这 14 条口径刻意分叉**。
- `jh3ceut.xscn` 布局特殊（解析 0 条目，只处理标题）。
- 数据：`work\xscn\POLICY.md`(风格指南) · `NORMALIZE.md` · `work\xscn-all-map.tsv`(唯一回写依据) ·
  `work\xscn-openpg\`(openpg-map.tsv / overrides.tsv / build-map.py / verify.py / dump-one.py) ·
  `backup\xscn-names-orig\`(187) · `backup\ORIGINAL-EFILE_OLGWW2\SCENARIO\`(1033，**官方整包＝最强还原源**)。

### 标准流程
```
1) 导出 tools\xscn-tool.ps1 -Action export   2) 分块 400 条/块
3) 子代理翻译（每批 ≤4 个，并发过高会导致客户端不断自动重连）
4) 机械校验（行数 / 每行 1 TAB / TAB 前原文逐字节相等 / 括号斜杠数一致）
5) 合并 xscn-build-map.ps1   6) 干跑 -DryRun   7) 写入（预检+备份+回读）  8) 回滚 xscn-rollback.ps1
```

### 三个坑（已修）
1. **`Object[]` 交给 `BinaryWriter.Write()` 会静默只写 1 个字节**。根因：
   `$x = if(cond){ <byte[]> } else { <byte[]> }` —— **if 表达式把数组重新包成 `Object[]`**，
   `[byte[]]` 强转在表达式求值后失效；`Write(Object[])` 不报错、只写 1 字节。
   **正解：用 if/else 语句分别赋值；每个 `Write()` 都显式 `[byte[]]` 强转。**（本项目已两次踩此坑）
2. **脚本里出现中文 ⇒ 无 BOM 时 PS 5.1 按 GBK 误读**。即使"纯 ASCII 脚本"只要**参数默认值含中文路径**就翻车：
   备份写进乱码目录，而 `Test-Path` 查的也是乱码路径 ⇒ **断言查不出来**。
   **正解：脚本彻底纯 ASCII，中文路径作必填参数从命令行传入。**
3. **写完再回读太晚**（校验失败时文件已坏）。**正解：先重建到临时文件 → 回读校验 → 通过才写正式文件。**

> ⚠️ **返工纪律**：合并前必须核对「所有分片的最后修改时间 ≤ 映射表生成时间」，并把每个分片与映射**逐串比对**，
> 有差异就判定「规范化差异 vs 真陈旧」。本项目靠这一步抓到 `part-13` 的 147 条过期译文
> （另发现手工译样板 RSCHI03/MAO1 的 161 条漏进合并）；返工后重写 **13,352** 处（较首版 +129）。

### 写入器不可重入 ⇒ 二次修正用「字节级定点替换」
`tools\xscn-patch.ps1` 的 `orig` 列必须等于**当前**文件内容 ⇒ **对已汉化文件一律 SKIP**。
正解（`work\efile-nashornpbem\fix_alias_dup.py`）：
```
解析出每个条目的 (长度字段偏移, 原始字节)
→ 只对目标条目改写「2 B 长度字段 + 内容」，其余字节一个不动
→ 从后往前替换（避免偏移失效）
→ 写 temp → 回读解析 → 校验 data_end / groups / 条目数 / 标题逐字节 → 通过才写正式
```
好处：**其余字节保证逐字节不变**，结构不可能被破坏；天然可重入（匹配"当前文本"）。
**用 Python 比 PowerShell 稳**（避开 `Object[]` 只写 1 字节 + 非 ASCII 源码被按 GBK 误读两大地雷）。

### ★ 判「两侧译名是否一致」的零歧义硬桥（2026-09-24，`docs\18`/`docs\19`）

判两组中文字符串是否"同一处"时，**绝不能用位置对齐**——实测 `.xscn`↔`.txt` 偏移会漂移：
`MAO14_2` 整体偏移 1 行（`.txt` 首行是场景标题）、`n42s12a` 中途从 +1 变成 0（`.xscn` 多插了一条「湖」）。
低对齐场景（`RSCHI07` 8%）用锚点插值会给出**假不一致**。

正解：**用原始英文当桥**（`backup\ORIGINAL-EFILE_OLGWW2\`）：
1. `orig\<n>.txt`(cp1252) ↔ `cur\<n>.txt`(gbk) 是**同一名单的两个语言版**，逐行平行 ⇒ 建 `en→zh` 字典；
   **必须优先用同场景那份**（全局字典会把 B 场景改成 A 场景的译名；实测改用同场景后 46 行取值被纠正）。
2. `orig\<n>.xscn` ↔ `cur\<n>.xscn` 组0 **索引天然对齐**（同格式同结构）。
3. `cur.xscn[i] != dict[orig.xscn[i]]` ⇒ 不一致，**对应关系由索引直接锁定，零对齐风险**。

工具：`bridge_check.py`（判定）· `triage_mismatch.py`（分类：S_SUF/S_SUB/N_VAR/E_DIS）·
`make_unify_plan.py`（白名单裁定）· `apply_unify.py`（按 文件+索引 定点写）· `verify_unify.py`（重建复核）。

**白名单四条**（保留 `.xscn`，不采 `.txt`）：
`A` 括号别名政策（`.xscn` 有别名而 `.txt` 无，如 `根特 (Gand)`）；
`B` 手工反例（阿尔贝特运河、砥平里、海参崴、萨尔姆河）；
`C` `.txt` 自损（`哈拉哈河（哈拉哈河）` 自重复）；
`D` `.txt` 侧未译（新值无汉字而 `.xscn` 有）⇒ 防「中文换英文」倒退。

### 写入器的四条铁律（踩过才知道）

1. **被 `import` 的脚本底部必须 `if __name__ == "__main__":`** ——
   `apply_residual.py` 原本裸调 `main()`，被 `from apply_residual import parse` 时执行；
   外层若带 `--apply` 会**连带触发误写**。
2. **`tee out/x.txt | head -N` 会 SIGPIPE 杀掉 tee，把输出文件截断** —— 有一回因此误判"清单不完整"。
3. **新值要加「不含汉字」守卫**：写入后残留审计里「含汉字 −1」与「疑似漏译 +1」是**成对出现的联动信号**，
   可据此定位那处「中文换英文」的倒退。
4. **备份别用 shell `while read` 循环**（170 个文件时被 SIGTERM 中断）⇒ 改用 Python `shutil.copy2` + 全量 md5 校验。

---

## 3. `.ply` 场景简报层（全库 116 个漏译）

- `<efile>\SCENARIO\*.ply` = **场景开场简报正文**（可滚动弹窗）。
- 结构：纯文本 CRLF；**可含 1∼2 个语言块**，用一行 ≥8 个 `-` 分隔（OLGWW2 作者是西语团队，故 ES+EN 双写）。
- 编码 **ASCII / Latin-1**；引擎按 `CP_ACP=936` 解释 ⇒ 西语重音 `á é ñ` 变方块并**吃掉后一字符**（实机已见：
  `alemán`→`alem□`、`situación`→`situac□`；机理：`0xE1`+`0x6E`(=n) 恰好构成一个合法 GBK 双字节）。
- 全库 **156 个**：ascii 108 + high-bytes 8 + **empty 40**（501 B 纯 `\x00` 占位，跳过）⇒ **实需译 116**（合计 38,403 B）。
- 分布：**OPENPG 43**、AO 25、BASEKORP 18、LUPO 7、KAISER 6、**OLGWW2 5**、OPENAK 5、OLGCW 5、AG 1、Clu 1。
- 含高位字节、今天就在乱码的 8 个：`canalalbert_i`(12)、`getteriver`(12)、`tiger05/06/07_i`、`tornio_landing`、`chaco1`、`uspanwar4_i`。
- ⚠️ 与 `.txt` 简报族（`*i/*int/*v/*l/*bv/*tv`，如 `18days0i.txt`/`dak1int.txt`）**是两套载体、互不替代**；
  `canalalbert.txt` 只是"名称清单"（地名+番号），简报在 `canalalbert_i.ply`。
- 修法：**GBK 无 BOM CRLF**，部署到 **`TEXT-ZH\SCENARIO\`**（`.ply` 走 LangDir 优先）；两处同写更稳。

---

## 4. `strings-zh.txt` 复核（2026-09-24）

- 与官方 `strings-es.txt` **逐行对齐、无串位** ✅（917 行合法：es=916 / de=917 / hu=915 / pl=916 / zh=917）。
  766 行含汉字；与西语版逐行相同的仅 114 行（多为 `*` 开头的模板结构注释）。
- **漏译 2 处**：第 **834** 行 `* Special attributes`（西语版也是英文 ⇒ 模板级）、
  第 **879** 行 `* Leaders`（西语版已译 `* Lideres` ⇒ 我们的漏译）。
- 已排除伪问题：`\n`/`\r\n` 字面转义 40+ 处 = **引擎约定的换行转义**，非错误；
  纯 ASCII 行绝大多数是 `*` 开头的模板结构注释，设计上不翻译。

---

## 5. L7 exe 硬编码（已打补丁）

- `RT_DIALOG` **37 个对话框 / 279 条**译文已写入（性能坑：逐条重新解析超时 → **按对话框分组、每个只解析一次**，1.5 秒完成）。
- 代码内字符串 5 条 ＋ 面板标签 3 条（`Efile：`/`作者：`/`文件：`）＋ 表头 6 ＋ 筛选标签 4。
- **内置地形名表 `0x5842A0`（21 项 × `0x100`）已汉化**，运行时内存确认一致
  （服务"地形数据/工具提示"，**不是**地图标签来源）。
- ⚠️ **含格式符（`%d`/`%s`）的串一律"写副本到空洞 + 改指针"，不要原地替换**
  （曾把 `File: %s   [%d scenarios]` 原地改短 → 显示成 `[4[6]20456 个场景]`，已回滚）。
- 对话框文本是 **UTF-16LE**，原地替换须满足 `新 UTF-16 长度 ≤ 原长度`。
- 备份链：`backup\OpenGen.exe.original` / `.before-dlg136` / `.before-panellabels` / `.before-dialogs279` / `.before-terrain`。
- 工具：`work\exe\exe-patch.ps1`(scan/apply/verify/rollback/holes)、`rtdialog-apply-all.ps1`、`mem-scan.ps1`/`mem-dump.ps1`。

### ✅ 2026-09-24 实机截图新增：单位面板归属标签 `Main`→「主国」

- 位置 `.rdata` **FO `0x513A38` / VA `0x914838`**，`Main\0` 共 5 字节。
- **原地等长替换**：`4D 61 69 6E 00` → `D6 F7 B9 FA 00`（`主国\0`），文件长度不变。
- 引用唯一（全 exe 仅 `push 0x914838` 一处 @ FO `0x419A0A`；4 字节小端模式全库仅 1 命中）。
- 上下文：`movzx edx,[unitdata+0x26c]` → `jmp [ecx*4 + 0x81ba9c]` switch 0..3；
  case 0 标签 = `Main`、case 1 = `OTP`（3 B，装不下中文 ⇒ **保留**）、case 2 = 取 `0xBFF068 + n*0x100` 国名表。
- 语义＝**单位归属国家类别**（与 `Switch Main / Supporting country` 同义）。台账见 `work\exe\ledger.md` 第 6 条。
- exe MD5：`2F4A4BA7…` → **`1640811C1EE34CC42D462D0968FCE9C7`**；备份 `backup\OpenGen.exe.before-unitlabel`。

### ⬜ 未做：地图提示 / 单位信息格式串块（2026-09-24 新发现）

- 位置 `.rdata` **VA `0x911F80–0x912230`**（FO ≈ `0x511180`），≈**40 条连续成块**。
- 截图实证：
  - tooltip `VH to take by Both sides` = `'VH to take by '`@`0x9120E0` ＋ `'Both sides'`@`0x9120F0`
  - 底栏 `5/5 Exp:0 Ent:0 Fuel:60 Mov:0 Mnt:6 Ammo:4` = `' %s%d/%d Exp:%d  Ent:%d'` ＋ `'  Fuel:%d %s'`
    ＋ `' Mov:%d Mnt:%d'` ＋ `'  Ammo:%d '`
- 同块还有：`Press ESC key to close this intro and continue`、`Odds: %d-%d`、`AP:%d  Fort:%d  Port:%d  Station:%d  Bridge:%d pp`、
  ` %s (%s)`、`  Ammo:- `、`  Ammo:%d/%d `、`KeepAir `、` Mov:%d`、` {Sab}`、` OH(%d,%d)`、` OH(%d,%d)>U:%d`、
  ` Map: %d x %d`、` [S:%d H:%d]`、`><`、`* Until T%d`、` (Friends)`、` (Enemy)`、`Out of map boundaries`、
  `EH: Land, Naval & Air` / `EH: Land & Naval` / `EH: Air`、`Enemy`、`Friends`、`SH for Owner`、`SH for `、`Both`、`  ***  `。
- **不在 `strings-zh.txt`**（官方 es/de/hu/pl 版也没有，仅 `VH ` 一词命中别处）⇒ **只能改 exe**。
- ⚠️ 长度陷阱：`'  Ammo:%d/%d '` 仅 14 B，加「弹药」需 15 B ⇒ **超 1 字节**；逐条核算长度，含格式符的不可原地改短。

---

## 6. 事故档案

1. **`.xscn` 被截断成 2042 B**（`Write($keep)` 绑错重载静默只写 1 字节）
   → 从 `backup\ORIGINAL-EFILE_OLGWW2\SCENARIO\` 还原。
2. **`Object[]` 静默只写 1 字节**（见上 §2 坑 1，已踩两次）。
3. **BOM 缺失 / 多余都出过事**：
   ① `xscn-patch.ps1` 无 BOM `.ps1` 被 PS 5.1 按 GBK 解析 ⇒ 中文路径变乱码 ⇒ 备份写进
   `D:\DSH\鍐涗簨娓告垙姹夊寲`，`Test-Path` 查的也是乱码路径 ⇒ **断言没拦住**；
   ② 2026-09-24 Write 产出的 `.tsv` 带 BOM ⇒ 键名变 `\ufeff…`（生成器须剥 BOM 或用 `utf-8-sig` 容错）。
   **结论：交给脚本按字节比对的文件必须显式确认 BOM** —— `.ps1` 存 BOM 或纯 ASCII；数据文件一律无 BOM。
4. **备份与覆盖未分离**（2026-09-20：一条命令语法错误 ⇒ 脚本整体拒执行 ⇒ 备份没跑、覆盖跑了，
   807+190 场景文本被无备份覆盖，后从官网重下救回）。
5. **写完再回读太晚** ⇒ 正解：先重建到临时文件 → 回读校验 → 通过才写正式文件。
6. ⚠️ **空洞选址没查 PE 数据目录 ⇒ 游戏窗都出不来（2026-09-24，09-28 补记）**
   unitpanel 的空洞原选 `FO 0x51CB31`（VA `0x91D931`）。该址**落在 `IMAGE_LOAD_CONFIG_DIRECTORY` 内**
   （实测数据目录 `LoadConfig` = RVA `0x51D930–0x51D970`，FO `0x51CB30–0x51CB70`，40 B）。
   写入偏移 +16（RVA `0x51D941`）命中原生 `GlobalFlagsSet` 字段 —— 加载器把它 `|=` 进
   `ntdll!NtGlobalFlag`，打开 loader snaps 等调试标志 ⇒ 进程初始化阶段在 ntdll 里 `0xC0000005`，
   **游戏窗都出不来**（当时误判成别的层）。
   **修**：迁到 `FO 0x4B1A9A`（VA `0x8B289A`，54 B，实测不与任何 PE 数据目录相交、区内全 NUL、0 引用），
   同步改 5 处引用立即数（`0x412D26` `0x41ADCF` `0x41ADC6` `0x41801D` `0x419A3E`）。
   **固化**：`pelib.check_hole()` 三项检查 = ① 区内全 NUL ② **不与任何 PE 数据目录相交** ③ 0 引用。
   ⚠️ **仅「全 NUL + 0 引用」不够** —— 前两项都过、第三项才是致命的。选空洞前必查数据目录表。
   ⇒ 详见 `work\exe\ledger.md` §第三批。

---

## 7. 环境坑

- 本机 `Active code page: 936`（GBK）—— 与 PGForever 的 **UTF-8 manifest 方案完全不同，切勿串用**。
- `[Text.Encoding]::Latin1` 在 PS 5.1 不存在，用 `GetEncoding(28591)`。
- **PowerShell 工具无 stdout 回显**（exit 0 取不到输出）⇒ 需看结果时用 Bash + 前置 `export PATH="/usr/bin:/bin:$PATH"`。
- **Python 分工**：审计/截图用系统 `C:\Python314`（有 Pillow）；反汇编用**托管** Python 3.13.12（有 capstone 5.0.7）。
- Git Bash 里没有 `file`/`strings`，用 Python 读字节代替。
- 启动 SDL 游戏：`subprocess.Popen` 会被沙箱挡掉（进程 rc=0 立即退出），**必须用 PowerShell `Start-Process`**。
  截图用 `PrintWindow(hwnd, memdc, 2)`（不受遮挡）+ 手写 PNG。

---

## 8. 译名统一（B 类）的四个坑 —— `docs\22`

### 8.1 投票源混入「派生副本」= 重复计票
`EFILE_NASHORNPBEM` 是本工程的 POC，其 `TEXT-ZH` 根文件**取自 OPENPG**（实测 names.txt
588 个同名里 560 个译文完全一致 = **95%**）。把它计入「多数票」等于给 OPENPG 记两票，
把本应 1:1 平票的对决伪造成 2:1 的"多数"，让平票裁决规则彻底失效（实测翻转约 63 组）。
**⇒ 投票前必须确认每个 efile 的译文是否同源；派生副本只作对齐目标、不投票。**
（判定手段：按英文名对齐后比「同英文名的中文一致率」，>80% 即判同源。）

### 8.2 权威基准的键是**姓氏**，游戏里是 `von Kluge`
基准表按 `Kluge`/`Manteuffel` 建键，而游戏写 `von Kluge`/`von Manteuffel`
⇒ 著名将领一律漏过基准、被普通投票改成少数派音译（实测 `冯·克鲁格→冯·克卢格`、
`冯·曼陀菲尔→冯·曼托伊费尔`）。**查表前必须剥贵族介词**：`von/van/de la/de/del/della/di/da/le`。

### 8.3 `max(key=...)` 的元组是**升序**比较 —— 偏好位要给「大」值
规则栈写成 `(票数, 0 if z in NORM else 1, -pref, len)` 时，在规范清单中的候选拿到 **0**，
反而输给不在清单中的（拿 1）—— 症状是「规则看着对、结果全是反的」，且只有 1/20 命中。
**⇒ 偏好类布尔位一律写成 `1 if 满足 else 0`。** 修完命中数从 1 变成 20（与探针吻合）。

### 8.4 番号订正**必须排除组 0**
`.xscn` 组 0 是场景 `.txt` 名清单的**镜像**（docs19 已定 `.txt` 为规范本地化）；
组 1 才是部队番号链。对组 0 套用「`N Arm`→师级」规则，会立刻造出 `.xscn`↔`.txt` 不一致
（实测 DAK5 `g0#5` `3旅/1装甲师/[第30军]` → `第1装甲师`）。**限 `g >= 1`。**
同一坑在上一轮 `fix_division.py` 已踩过一次（2 处组 0 `第11师团`/`第57师团` 被误改「师」）。

### 8.5 `bridge_check.py` **只校验组 0** —— 组 1 是审计盲区
它只把组 0 条目与 `.txt` 字典比对（4,537 条命中）⇒ 组 1 的番号链从未被对过。
新增 `scan_g1_vs_txt.py` 才量出：`师` 应作 `师团` **261 段**、`师团`族其它 31、仅空格/标点 129。
（根因：`.txt` 侧**按阵营**用词 —— 日军 `第N师团` 763 处/35 文件、国军 `国民党军第N师`、苏军 `第N师`；
`.xscn` g1 一律用 `第N师`。备份里 `师团` 仅 3 处 ⇒ 属历史既有，不是本轮引入。）
**⇒ 任何「层间一致性」校验都要先确认它到底覆盖了哪些组/哪些层。**

### 8.6 `.txt` 侧自相矛盾的扫描必须先加**段数守卫**
`.txt` 名清单英中两侧段数常不等（中文侧多 `[军]` 标注）⇒ 按 `'/'` 段号对齐会错位，
把 A 部队的译名安到 B 部队上，量出 39 个「矛盾」里只有 4 个是真的。
**⇒ 段数不齐的整行跳过**（例：`barcelona.txt` 的 `11 div` 报成 `[第5军]`）。

## 9. 原文侧编码诊断（`docs\23`）——「乱码原文」实为两类

用户看到的「乱码」有两种，**机制与处理完全不同**，不先分类就会修错：

### 9.1 判编码：只看两行

```python
data.decode('gbk')      # 失败 ⇒ 这就是 cp1252 单字节（正常原文）
data.decode('utf-8')    # 成功但结果里残留 Ã/Â/Å ⇒ 该行是 UTF-8（真乱码）
```

- **A 类（UTF-8 混入）**：`BarrÃ³n`(`ó`=C3 B3)、`LÃ©opard`、希腊文段。引擎按单字节读 ⇒ **游戏里真乱码**。
  `EFILE_ROI\names.txt` 134 行、OLGWW2 134 行、ATOMIC/KAISER/LXF/OPENAK 共 12 行。
- **B 类（cp1252）**：`L間ion Etrang鑢e` = **用 GBK 打开 cp1252 文件**产生的**假汉字**
  （`0xE9 0x67` 被当成一个汉字 `間`）。引擎按 latin-1 读 ⇒ **游戏里正常**；4,433 行，德语 1,573 居首。

⚠️ **判据必须逐文件、甚至逐行**：`EFILE_ROI\names.txt` 是 `hi=0.013` 的**混合**文件
（整体 ASCII 占比极低，用「整文件 ASCII 占比」判会误判成 cp1252）。**UTF-8 成功 ⇒ 采信 UTF-8**。

### 9.2 中文侧（GBK）**装不下**西文变音符

`'Légion'.encode('gbk')` 直接抛 `UnicodeEncodeError`（GBK 无 `é`）。
**⇒ 往中文侧写任何含变音符的西文，必须先折写或翻译**：本轮 `Fallschirmjäger`→「伞兵」、
`Léopard`→`Leopard`、`Zsadányi-Nagy`→`Zsadanyi-Nagy`。写盘脚本要有 `safe()` 兜底（NFKD 逐字折写）。

### 9.3 修 A 类场景 `.txt`：走 `TEXT-ZH\SCENARIO\`，**不动原文**

`.txt` 的目录规则是 **LangDir(`<efile>\TEXT-ZH\SCENARIO\`) 优先 → 回退 EfileRoot**
⇒ 建同名中文侧即覆盖生效。**行数必须逐行对齐**（引擎可能按行号索引），空行位置保持。

### 9.4 「直接复用中文侧」的判定：字节完全相同

未汉化 efile 的某文件若与已汉化 efile 的同名文件 **md5 相同**，即可直接复制其 `TEXT-ZH` 版本 ——
零翻译、零风险。实测命中：`EFILE_ROI` 的 `names.txt`/`nations.txt` == OLGWW2（2264 行全对齐、零错位）。
**⇒ 新 efile 汉化前先跑一遍全库 md5 比对，能白捡的绝不重译。**

### 9.5 普查脚本的三个坑

- **整文件一刀切判编码**必错 ⇒ `restore_orig_encoding.py` 改**逐行**判。
- **排版分隔线**：`\xaf\xaf\xaf…`（`¯`）整行重复，出现 11,166 次，是画横线不是字母 ⇒ 必须单独剔除，
  否则字符频次榜被它霸占。
- **别把已汉化文件当原文扫**：`<efile>\SCENARIO\*.txt` 对已汉化 efile 已是中文（GBK）⇒
  会量出 `¯`/`÷`/`Ã` 上万次的假象。**原文侧一律取 `backup\ORIGINAL-<EFILE>\`。**

---

## 10. 字体与字距（`docs\27`）—— 拉丁字符重叠的真正原因

### 现象与根因

实机截图里 `Main`、`STOP`、能力代号**字符互相重叠**（`Main` 渲染成 `Nlain` 状），**汉字完全正常**。

根因不在编码、不在 `.xscn`，而在**字体**：`deng.ttf`（DengXian 等线）在 **11–12px 小字号下，
拉丁字形 hinting 外扩、溢出自身 advance 框** ⇒ 与下一字符重叠。

- `Main` 的**总宽是对的**（26px ≈ verdana 的 28px），坏在单字形溢出；
- **14px 及以上完全正常**；
- 与 `.xscn` 汉化无关，OLGWW2 时代同配置下同样存在。

### 实测宽度表（12px）

| 字体 | M | a | i | n | Main | 表现 |
|---|---:|---:|---:|---:|---:|---|
| `deng.ttf` | 10 | 6 | 3 | 7 | 26 | ❌ 重叠 |
| `verdana.ttf` | 10 | 7 | 3 | 8 | 28 | ✅ |
| **`simhei.ttf`** | 6 | 6 | 6 | 6 | 24 | △ 极轻微 |
| `simsun.ttc` / `simkai.ttf` / `simfang.ttf` | 6 | 6 | 6 | 6 | 24 | ✅ |
| `msyh.ttc` | 12 | 7 | 3 | 7 | 29 | ✅ |

> **规律**：**半角设计**的中文字体（宋/黑/楷/仿宋）ASCII = **汉字宽的一半**，与 CJK 混排天然吻合；
> **比例设计**（等线 / 雅黑）小字号易溢出。⇒ 中英混排 UI 优先选半角 ASCII 字体。

### 现况

`Settings.cfg` 已改为 **`Font1=Font2=simhei.ttf`**（黑体：汉字最清晰、军事 UI 气质、
拉丁仅极轻微挤压）。`simhei.ttf`/`simkai.ttf` 已复制进 `D:/OpenPG2/FONTS/`。
回滚：`backup\Settings.cfg.before-font`。备选 `simkai.ttf`（字距完美、笔画略细）。

### 换字体**必做**汉字覆盖验证

AG 全部中文侧文本共 **578 个唯一汉字**，实测 `simhei`/`simkai`/`deng` **均 0 缺字**。

⚠️ 两个陷阱：
1. **不能用 `getmask().getbbox() is None` 判缺字** —— `simsunb.ttf`（宋体扩展B）会返回非空位图，
   实际画出来是**方块**。**必须渲染成图肉眼扫**（`simsunb`/`SimsunExtG` 全不可用）。
2. `.ttc` 游戏不支持（`simsun.ttc`/`msyh.ttc` 效果最好但用不了）；单文件 `.ttf` 中文候选＝
   `simhei` / `simkai` / `simfang`。

### 诊断工具 `work\ag-verify\`

`zoom.py`（按**比例**框选放大截图）· `fonttest.py`（多字体字距对照）·
`font-final-compare.png`（真实游戏文本六字体对照）· `ag-hanzi-coverage.png`（578 汉字覆盖对照）。

**方法**：判断"实机文字挤/叠/糊"时，**先用 PIL 以同一字号离线渲染同一串** ——
能复现 ⇒ 字体问题；不能复现 ⇒ 引擎排版问题。**全程不需要启动游戏。**

---

## 11. exe 短串改造三板斧（`docs\28`）

改 exe 内硬编码串时按「能不能原地放下」分三种，**从最安全往下走**：

### ① 原地替换（首选）
GBK 字节数 `len(dst.encode('gbk'))+1` ≤ `len(src)+1` ⇒ 直接覆盖，余量填 NUL。
**文件长度不变，零副作用。** 约 8 成条目都能这样。

> ⭐ **诀窍：中文字节是英文两倍，但显示宽度也是两倍。**
> 所以「英文单词数 → 中文汉字数」大致**减半**时，**显示宽度基本持平**，
> 排版不会溢出。折算：`显示宽 ≈ 2×CJK数 + 1×ASCII数`。

### ② 空洞 + 改指针（3–4 字节短串专用）
`Gnd`/`Air`/`TBD` 这类 4 字节串放不下「地面」的 5 字节。做法：
1. `poke_holes.py` 扫连续 NUL 空洞（**必须在节内且在 VirtualSize 之内**）；
2. **逐 VA 搜 4 字节小端模式**确认空洞区间 **0 引用**（关键！只查空洞起始是不够的）；
3. 原串引用处必须**仅 1 处**，且是 `push imm32`(`68 xx xx xx xx`)
   或 `mov dword [ebp-x], imm32`(`C7 45 xx xx xx xx xx`) ⇒ 改立即数即可；
4. 多条串可**顺序拼进同一空洞**，认领偏移。

⚠️ **别用节尾 raw 填充区**（`SizeOfRawData > VirtualSize` 的那段）——加载器不一定映射。

### ③ 多行块整块替换（含 `\n` 的消息）
`.xscn` 之外的 exe 消息常有 `\n`，且**块与块内子串互相嵌套**：
一个三行块里，每一行"也是"一个独立串（代码可能单独引用某一行的起始 VA）。

**若只改块头 → 子指针会指向中文串中间 ⇒ 乱码。**

处理流程：
1. 把每个候选 FO 的**完整原文取到 NUL**（不要按行切）；
2. 对块内**每一个可能的子起始 FO** 查引用数；
3. **子指针 0 引用 ⇒ 可整块覆盖**（本例 6 个子指针全部 0 引用）；
4. 子指针非 0 ⇒ 必须把所有被引用的子串**分别搬到空洞**并逐个改指针。

### 验收清单（每次必做）
- 文件长度不变；
- PE 头前 16B 相同、签名 `PE\0\0`、节表数不变；
- **逐字节差异审计**：把所有差异区间归类，确认 `.text` 的差异**全部是指针立即数**、
  `.rdata` 的差异**全部是译文与空洞**（多出来的差异就是事故）；
- 回读：按 FO（或改后指针）重新解出译文，逐条比对；
- 脚本**幂等**：`原文不符` 分支先判「当前是否已是目标译文」，是则跳过 ——
  否则重跑一次全是错误、且改指针部分会二次改写。

### 实施顺序（每次）
`备份（独立命令）` → `干跑` → `核对零错误` → `--apply` → `回读校验` → `差异审计` → `台账`。

---

## 12. 紧凑对齐串块的改法（`docs\29`）—— 三个会毁文件的坑

上一节（§11）讲的是有空隙的串块。**`0x911F80` 起的地图提示/HUD 块是另一种形态**：
字符串池式**紧密排布**，每条占用 `ceil((len+1)/4)*4` 字节（内容 + NUL 向上对齐到 4 字节）。

```
0x511224  ' %s'             len  3  avail  4
0x511228  '  Ammo:- '       len  9  avail 12
0x511244  'KeepAir '        len  8  avail 12   ← 译文 10B > len(old)+1 = 9
0x511250  ' Mov:%d Mnt:%d'  len 14  avail 16   ← 译文 17B > avail
```

### 12.1 ⛔ 坑一：Python 切片赋值会**静默撑长** `bytearray`

```python
pad = len(old) - len(new)             # KeepAir: 9 - 10 = -1  ← 负数！
d[fo:fo+len(old)] = new + b"\x00"*pad # 右 10B 写进左 9B 切片
```

`bytearray` 切片赋值的长度**不要求相等**：右侧更长时它会**自动扩容**，
于是**其后所有字节整体后移**，全文件错乱。症状很隐蔽：干跑时**后续每一条**都报
「原文不符」，且读到的内容**前面多一个 `\x00`**。

> ✅ **正解**：写入窗口恒定 = `avail`，余量填 NUL。
> ```python
> lim = AVAIL[fo]                        # 下一串起点 - FO
> d[fo:fo+lim] = new + b"\x00" * (lim - len(new))   # 长度不变
> ```

### 12.2 ⛔ 坑二：`avail` **不能运行期动态扫描**

把「串」定义为「可打印 ASCII 段」（`0x20 ≤ b < 0x7F`）在英文文件上没问题，
但 **GBK 汉字字节是 `0xA1–0xFE`，不在这个区间** ⇒ 汉化之后中文串不被识别成串 ⇒
边界全错（表现为幂等重跑误报一大批「原文不符」）。

> ✅ **正解**：`avail` 是**原文件的静态属性**，**硬编码成常量表**。
> 若确需重扫，识别条件必须同时接受 ASCII 与 `b >= 0x81`。

### 12.3 ⛔ 坑三：幂等检查的**窗口**也要用 `avail`

若检查窗口取 `len(old)` 而译文比原文长，读到的 `cur` 会被截断到**比 `chk` 还短**
⇒ 永远比不上 ⇒ 重跑必误报。**窗口必须与写入窗口一致。**

### 12.4 这批串的「引用形态」差异

`0x911F80` 块的引用**全是 4 字节立即数**，但形态有两类：

- `68 xx xx xx xx` —— `push imm32`
- `c7 85 xx xx xx xx <imm32>` —— `mov dword ptr [ebp+disp32], imm32`（**7 字节指令**，
  imm32 落在命中位置，前导字节不是 `0x68` 而是 disp32 的末字节，容易误判为「误匹配」）

判别误匹配的正解：**看前导字节是不是 `0xE8`/`0xE9`**（`call`/`jmp rel32`，那是相对偏移碰巧同值）。
`0xFF`、`0x8B` 之类则是真实指令流的一部分，需结合 `c7 85`/`c7 45` 前缀判断。

### 12.5 ⭐ `exe_zhfix.py`：exe 侧的二次修正入口

**汉化之后再想改译名，补丁脚本没用**——它按英文原文匹配，必然 0 命中。
`work\exe\exe_zhfix.py` 按 **FO 定点**替换现有译文（对应 `.xscn` 侧的 `ag_xscn.py zhfix`）：

```bash
python exe_zhfix.py --tsv fix.tsv [--apply]     # 列: FO<tab>旧译文<tab>新译文[<tab>limit]
python exe_zhfix.py --fo 0x511408 --old "…" --new "…" [--limit 0x10] [--apply]
```

- 默认**只允许缩短** ⇒ 天然不越界；需变长必须显式 `--limit`；
- 幂等、干跑、回读校验齐备。

### 12.6 改 exe 短串前的**显示宽度**量测（必做）

中文更宽。用 PIL 以**游戏字号**离线量 `getlength(原文)` vs `getlength(译文)`：

```python
f = ImageFont.truetype(r'C:\Windows\Fonts\simhei.ttf', 12)
f.getlength(src)  vs  f.getlength(dst)
```

本轮 26 条关键译文：20 条不宽于原文，6 条短标签 +6~18px。
其中 `SH for Owner`(72px) → `SH 归属：拥有方`(90px) 偏宽，改用 `SH 归属方`(51px)。
**量完再改，比改完再看实机便宜得多**，而且**全程不用启动游戏**。

---

## 13. GBK 本地化的「乱码盲区」（2026-09-28）—— 三个操作都够不到的残留

「保留原文」的条目（`status=POLICY`）会把 cp1252 单字节直接留在 GBK 文件里。
**它不会被任何常规判据发现**，原因是三层叠加：

1. 译名库里是 `src == dst` 的**恒等映射**（实测 `standard-glossary.tsv` 23,200 条中 **4,179 条**，
   全部 `POLICY`）⇒ 流水线「处理」过它，但产出 == 输入（即 `MEMORY.md` §一 点名的「假已改」）。
2. `decode()` 的实现是「先试 GBK，解出汉字就算已汉化」。而 cp1252 高字节在 GBK 下解出
   `鋞`(0xE4=ä) / `蹹`(0xDC=Ü) / `鋝` / `鋟` —— **本身就是汉字码位**。
   ⇒ 这些条目被判为 `ENC_OUT`（已汉化），于是：
   - `apply`（`enc == ENC_OUT` 跳过）够不到；
   - `zhfix`（`enc != ENC_OUT` 跳过）够不到；
   - `verify` 的「含汉字」统计**把它们算作已汉化** ⇒ **校验被乱码骗过**。
3. 结果：游戏按 GBK 渲染成 `Pr鋞or Arrius` / `S蹹SCHAR` / `Kriegsh鋟ptling`，
   而**所有自动化检查都报「正常」**。

### 唯一可靠的发现手法：集合求交，别扫当前文件

```python
orig_hi = { 原始备份里所有「含 >=0x80 字节」的条目 }
still   = 当前文件里仍**逐字节等于** orig_hi 成员的条目      # ← 这才是残留
```

原始备份在 `backup\ORIGINAL-<EFILE>\SCENARIO\`。本轮实测：AG **7 处**、OLGWW2 **7 处**、
OPENPG / NASHORNPBEM **0 处**。

### 唯一正确的修复入口

`work\xscn\xscn.py --efile XX rawfix --map FILE` —— **显式按 cp1252 读**每个槽位再匹配词典。
`apply` / `zhfix` 对这类条目**永远 0 命中**。

### 修法二选一（GBK 装不下西文变音符）

- **译中文**：当同 efile 内已有对译时优先。AG 例：`NORDSCHAR`→北方集群 ⇒ `SÜDSCHAR`→南方集群；
  `Suebii Kriegshaeuptling`→苏维汇人战时酋长 ⇒ `Kriegshäuptling der SÜDSCHAR`→南方集群战时酋长；
  `执政官格奈乌斯马利乌斯马克西穆斯`（官职前置连写）⇒ `Prätor Arrius`→裁判官阿里乌斯。
- **折写 ASCII**：语料口径不统一、或不想做术语决策时用（`ä→a` `é→e` `ü→u` `ö→o` `ñ→n` `ç→c`）。
  OLGWW2 的 `equip.txt` 中文侧**早已全部折写**（`Möbelwagen→Mobelwagen`、`Citroën→Citroen`、
  `Bü-131→Bu-131`，实测 34 行全 ✅），故 `.xscn` 侧照办（`Aé→Ae`）与既有惯例一致。
  `glossary-orig-charset-fix.tsv` 备有 `ASCII折写` 列。

### 顺带排除的假问题

- 恒等映射含非 ASCII 者共 **29 条** —— 其中 `equip.txt` 侧属**原文侧**（本就不该动，引擎读 `TEXT-ZH\` 那份），
  中文侧已折写正确 ⇒ 这 29 条是**译名库的元数据陈旧**，不是部署缺陷。**改真源会牵连 `glossary-occ/conflicts`，须单独一批。**
- `TEXT-ZH\SCENARIO\*.xscn` 是**死文件**（引擎不读），里面的残留无害。

### ⭐ 判「是否已汉化」的正确判据（2026-09-28，`work\audit\progress.py`）

§13 的三层盲区说明：**裸 `decode('gbk')` 判汉字是不可靠的**。正确判据要叠三层：

```python
def gb2312_han(ch):                       # ① 汉字必须落在 GB2312 字节范围
    try: bs = ch.encode('gb2312')
    except UnicodeEncodeError: return False
    return len(bs) == 2 and 0xB0 <= bs[0] <= 0xF7 and 0xA1 <= bs[1] <= 0xFE

def han(ch, fake):                        # ② 再排除「实证假汉字黑名单」
    return gb2312_han(ch) and ch not in fake
```

- **① 为什么用 GB2312 而不是「有无汉字」**：cp1252 高字节解出的假汉字里，
  相当一部分（`鋞` U+92DE / `蹹` U+8E79 / `鎂` U+9382 / `鎦` U+93A6）**编不进 GB2312** ⇒ 天然被排除。
  同时 `第`（U+7B2C）/ `师` 在 GB2312 内 ⇒ 正常计入 —— 这点很关键：OLGWW2 大量番号是
  `第56 NGF` / `第12 MR师/[3A]` 这种「1–2 个汉字夹在 ASCII 里」的形态，
  用「ASCII 字母数阈值」判会全部误判成未译（实测差 **385 条**）。
- **② 为什么光 GB2312 还不够**：`耥`(U+8025) / `鲻`(U+9CBB) / `篥` / `屮` / `篾` **确在 GB2312 内**，
  会把 `Compa耥a`=Compañía / `H鲻r` / `Somosk鳅jfalu`=Somoskőújfalu 算成已译。
  ⇒ 从**纯 cp1252 原文侧**（`backup\ORIGINAL-*`，或未汉化 efile 的当前 `SCENARIO\*.xscn`）
  解出的全部汉字收进黑名单 —— 它们的唯一来源就是 cp1252，必为假汉字。
- ⛔ **黑名单必须按 efile 分别建，不能全局合并**：全局并集会把 KAISER 的假汉字（`師`）
  拿去排除 AG 的真译文 —— 实测 AG 会**少算 4 条**、BASEKORP 少 1 条、NASHORNPBEM 少 1 条。

**另外两个计数口径的坑**（都会让数字对不上旧记录）：

| 对象 | 坑 | 正确做法 |
|---|---|---|
| `.xscn` | 跳过空串 ⇒ AG 报 7148 而非 **7152** | **空串也计数**（AG 有 4 个空串；口径与旧记录对齐） |
| `.ply` | 501 B **全 NUL** 空壳，`strip()` 去不掉 NUL ⇒ 被算成"有正文" | 先 `replace(b'\x00', b'')` 再判（曾把 63 误报成 100） |
| L1 `strings-zh.txt` | `*` 开头是官方模板注释（81 行）⇒ 误报"93 行非中文" | 排除 `*` 开头行与 `[段名]` 行；实际应保留项只有 **12 行** |

**校准结果（与旧记录逐项对齐）**：`.xscn` 全库 **298,433** 条、AG **7,152**、OPENPG **2,329**、
NASHORNPBEM **249**、OLGWW2 **16,058**（85.5%）、`.ply` 有正文 **63**、L1 应保留 **12** —— 全部与既有记载一致 ⇒ 判据可信。
本脚本的输出即 `docs\00` §三，**进度表从此由脚本生成，不再手抄**。

---

## 14. ⭐ 两个漏统计的文本层：`.tmsg` 与 `.xsch`（2026-09-28 发现）

> 起因：AO 全层盘点（`docs\32`）。**全库进度表与工作量表此前都漏了这两层**。
> 判定口径：`TEXT-ZH` 副本若**逐字节等于原文** ⇒ 从未真译（"复制不算翻译"）。

### 14.1 `.tmsg`（任务消息）—— 纯文本，最易漏 ✅ 结构已定型

**位置**：**只在** `<efile>\SCENARIO\*.tmsg` —— **无 `TEXT-ZH\` 覆盖层** ⇒ 与 `.xscn` 同类，**efile 原地改**。
（OLGWW2 曾出现 `TEXT-ZH\SCENARIO\*.tmsg` 副本，实测与原文逐字节相同 ⇒ 假进度。）

**格式（极简，无二进制头）**：
```
纯文本 = 「行首 N 个 \r\n」 + 「正文（可含 \r\n 分段）」 + 「行尾 M 个 \r\n」
```
- 首尾连续 `\r\n` 是**屏幕定位 / 清屏指令**（引擎按空行数排版），N/M **逐文件不同**（实测 0–24）。
  ⇒ **必须逐字节原样保留**，增删会破坏电文位置与清屏。
- **切分不唯一但正确**：本工具按「最长首段 + 最长尾段」切，中间即正文；纯空行文件 body=b""。

**规模**：全库 **552 个**（`SCENARIO` 侧；LXF 227 / ATOMIC 86 / BASEKORP 79 最多）；
**有正文 538 / 纯空行 14**；切分自洽 **552/552**。
**真译率 0** —— OLGWW2 5 个实测 0 汉字对（**仍是英文**），其余层连 `TEXT-ZH` 都没有。

工具：`work\tmsg\tmsg.py`（`verify | verifyall | export | apply`；**apply 默认干跑**，加 `--apply` 才写）。

### 14.2 `.xsch`（分支选择屏）—— 有二进制头 + 定长槽 ✅ 结构已定型

**位置**：**只在** `<efile>\SCENARIO\*.xsch` ⇒ 同 `.tmsg`，**efile 原地改**。

**格式（全库 52 文件 / 115 记录实测 0 异常）**：
```
24B 文件头:  u16 ver=1 | u16 count | char[20] name
记录 ×count 顺序紧排（无对齐填充）:
    12B 头:  [0]u8  [1]u8  00 00  [4]u16  [6]u16  [8]u32
             ↑ 全部是**版面 / 音轨 / 字体参数**，格式无关，回写时**原样保留**
    [槽A]:   ★ 定长 **104 B**（全库实测一致），左对齐 + \0 填充；
             槽内**可含多个 \0 分隔的短串**（例：`North Africa\0Choice1_i\0PG1.mp3`）
    u16:     tail = 槽A 之后、从本字段之后起算、到「本记录结束」的正文字节数
    [槽B]:   tail 字节正文（`\r\n` 分行）
记录结束 = tail 字段后 + tail；**最后一条结束 == 文件长度**（唯一自洽判据）
```
文本为**全大写军事电报风**（`PRIORITY I DISPATCH` / `NAZI FORCES BASED ON MOON`）。

**⚠️ 踩坑 3 连（都不许犯）**：
1. **byte[0] 不是 tag**：OPENPG `choice*.xsch` 的 **rec0 = 0x00**（其余均 0x01）。
   按「rec0 tag 必须 0x01」判 ⇒ 3 个 OPENPG 文件误报。
2. **byte[8..12] 是 u32，不是魔数**：实测 `6 / 7 / 4000(0x0FA0) / 0xFE…`。
   按「`[8]==6` 为记录头」判 ⇒ `aochoice02` rec1（`07`）、`bkbkchoice` rec1（`0FA0`）误判为坏头。
3. **槽宽恒 104** ⇒ **不许扫描**：`tail` 位置 = `记录头后 + 104`，**直接取**即全对。
   早先写的「遍历候选位置找自洽 tail」**反而误判**（在正文里撞上巧合字节）——**删掉扫描逻辑**。

**替换约束**：槽 A 译文（GBK）**字节数必须 ≤ 104**（`\0` 填充）；槽 B 变长可自由增删，
但**重算 tail**，后续记录**整体平移**（结构无绝对偏移，唯一相对长度字段 ⇒ 平移安全）。

**规模**：全库 **52 个 / 27,094 B**（LXF 15 / KAISER 13 / ATOMIC 6 最多）；**真译率 0**
（OPENPG 4 个 `TEXT-ZH` 副本实测逐字节 == 原文）。

工具：`work\xsch\xsch.py`（同 `tmsg.py` 的 op 集）。**无损往返 52/52 已验**。

### 14.3 ⚠️ 一个会骗过校验的假信号

OPENPG 的 `choice2/choice3.xsch` 裸数汉字会报 **han=1**，看着像"译了一点"。实为
cp1252 字节对 `\xd4\xfe`（= `Ôþ`）被 GBK 解成 `轧`（U+8F67，在 GB2312 内）。
⇒ 又印证 §13：**判"是否已汉化"必须用 GB2312 成对判据 + 假汉字黑名单**，裸数汉字会骗人。

### 14.4 判"复制冒充翻译"的最简手法

```python
# TEXT-ZH 副本 逐字节 == 原文 ⇒ 伪进度
open(f"{ef}/TEXT-ZH/SCENARIO/{n}",'rb').read() == open(f"{ef}/SCENARIO/{n}",'rb').read()
```
本轮正是靠这一行发现两个层"有 `TEXT-ZH` 目录、内容却是原文副本"。

---

## 15. ⭐ `strings_efile.txt` 与 exe 内置表的两段式关系（2026-09-28）

> 起因：AO 盘点时问「`[classes]` 段依赖引擎默认，汉化还完整吗？」——**实测答案：不完整。**

### 15.1 引擎自述（`strings-zh.txt` 行 17–19，原文即证据）

> *These sections can be redefined **at efile level** by using **STRINGS_EFILE.txt** in efile folder,
> but **you cannot remove from this file***

⇒ **两段式**：**exe 内置英文表（fallback）** ＋ **efile 级 `strings_efile.txt`（可覆盖）**。
`strings_efile.txt` 的路径由 exe 拼出：FO `0x4F64xx` 有 `%sefile.txt` 模板（`.data` 段）。

### 15.2 exe 内置表实测（`.data` FO `0x5842A0` 起，**0x100 步长**，段界清晰）

| 区段 | FO 起 | VA | 条数 | 现状 |
|---|---|---:|---:|---|
| `[terrain]` | `0x5842A0` | `0x9858A0` | 21 | ✅ **已汉化**（`开阔地`…`浅海`）|
| `[sides]` | `0x5857A0` | `0x986DA0` | 2 | ❌ **英文**（`Axis` `Allied`）|
| `[classes]` | `0x5859A0` | `0x986FA0` | 24 | ❌ **英文**（`None` `Infantry` `Tank`…`Light Cruiser`）|

⚠️ **订正 MEMORY 旧记**：`0x5857A0`/VA `0x986DA0` 曾被记为「单位类别·移动型名表，与行号无对应」——
**实为 `[sides]` 段**（2 条 Axis/Allied），紧接着 `0x5859A0` 才是 `[classes]`（24 条）。整族从 `0x5842A0` 起按 0x100 排布。

### 15.3 结论与做法

**若某 efile 不提供 `[classes]` 覆盖 ⇒ 单位类别菜单 24 条 + 阵营 2 条显示英文。**
⇒ **每个 efile 的 `TEXT-ZH\strings_efile.txt` 必须写**（只覆盖它自己有的段）：
- `[classes]`：抄 `strings-zh.txt` 行 47–71（零新译）；
- `[requisition]`：抄同族 efile 既有译法（OLGWW2 行 38–60）；
- ⚠️ **保留原文的 `*` 注释头与行序** —— 引擎**按行索引**读（`*` 行也占位）。
- ⚠️ 每行只读**前 96 字符**（文件头注释明写）⇒ 译文长度受限。

### 15.4 ⛔ `strings_efile.txt` 的结构坑：注释块里的**裸 `\n`**（2026-09-28 实锤）

AO 的 `strings_efile.txt` 第 5–6 行之间夹着一段**跨行的裸 LF 段**：

```
*--------...--------\r\n   ← 第5行末（CRLF）
\n                          ← 裸 LF！
* (units) ... can be redefined\n
[classes]\r\n
```

**⇒ 全文件 `split('\r\n')` 后，第 6 个元素是**多行字符串 `"\n* (units) ...\n[classes]"`**，不是单行。

**正确回写方式**：`'\r\n'.join(lines)` —— 这样裸 `\n` 原样留在那个元素内部，**逐字节还原**。
**验收判据**：回写后 `LF 计数` 与 `CRLF 计数` **与原文件完全相同**（AO：56 / 54）。

⚠️ 这正是 **AG 版当初"第 6 行起整体偏移 1 行"** 的成因（AG 的 `strings_efile.txt` 按行对齐时 `align False 150/151`）—— 分片口径不一所致。
**⇒ 任何"按行对齐"的 efile 文本（equip/names/nations/strings_efile）都要先确认两个文件用同一「分片口径」**（`split('\r\n')` 是唯一安全选择）。

---

## 16. ⭐ 跨 efile line-aligned 复用（2026-09-28，AO 批的主力手段）

> 场景：新 efile 的 `equip.txt`/`names.txt`/`nations.txt` 大量条目在其他 efile 里已译过。

### 16.1 做法

1. 对每个**已汉化**的 efile，取其 `<efile>\<f>.txt`（**cp1252 解**）与 `TEXT-ZH\<f>.txt`（**gbk 解**）；
2. **先验行数相等**（`len(orig)==len(zh)`）⇒ 逐行 zip 建 `src -> dst` 表；多 efile 合并，先到先得；
3. 对新 efile 逐行查表：命中即复用，未命中 → 人工译。

### 16.2 ⚠️ 三个坑

| 坑 | 现象 | 处理 |
|---|---|---|
| **行数不齐就不许对齐** | OLGWW2 `names.txt`：orig 2261 / zh 2264（**+3 行**） | **整个 efile 弃用**（错位对齐会产出大批错译）。其余 3 efile 均对齐 |
| **中文侧必须按 `gbk` 解** | 按 cp1252 解 → 显示假汉字 → 误判"含汉字率 0%" | 一律 `gbk`；判据仍用 GB2312 字节范围 |
| **恒等映射混入** | `src == dst` 的条目是"未译"不是"已译" | 建表时 `if b and b!=a` 过滤 |

### 16.3 实测覆盖（AO）

| 文件 | 复用键 | 命中 | 需人工 |
|---|---:|---:|---:|
| `equip.txt`（`_equip-crossmap.json`） | 1165 | 77（另 policy 144） | 377 |
| `names.txt`（`_names-crossmap.json`） | 2210 | 53 | 319 |
| `nations.txt` | — | 少 | 18 |

**⇒ 复用率约 20–30%，其余仍需人工；但复用部分保证了口径一致（同一人名/装备在不同 efile 同译）。**

### 16.4 `names.txt` 的既有口径（实测）

| efile | 实名条数 | 含汉字 | 率 |
|---|---:|---:|---:|
| AG | 2418 | 1364 | 56% |
| OPENPG | 775 | 744 | 96% |
| NASHORNPBEM | 992 | 992 | 100% |

⇒ **既有 efile 实名一律音译中文**（`Smith→史密斯`），故新 efile 也音译。
**保留原文的**：`???`（占位）/ `Ant #NNNN`（巨蚁单位编号）/ `#rrggbb`（颜色串）/ `Classified`（保密占位）。
⚠️ 尾随空格（`Vogel ` `Spanknöbel `）与 cp1252 变音符（`Bäcker` `Müller` `Wójcik`）**必须按 key 原样匹配**（`strip()` 会漏配）。

---

## 17. ⭐ 场景 `.txt` 散文层：两条口径（2026-09-28，ATOMIC 批）

### 17.1 装饰线（`¯¯¯¯¯` 下划线）**必须字节透明**

场景 `.txt` 里紧跟在标题行下方的下划线 **不是 UTF-8 的 `¯`（U+00AF）**，而是**裸单字节 `0xAF`**。
另有一种形态 `Â¯`（cp1252 双重编码，字节 `C2 AF`）。两者都**不是合法 GBK**，任何 `decode('gbk')` 必然抛异常。

**⇒ 部署器必须显式识别后原样逐字节透传**：

```python
if core and set(core) <= {0xAF}:                    # 形态一：纯 0xAF
    emit_raw(core)
else:
    d = core.decode('cp1252', errors='replace')
    if d and set(d) <= {'Â','¯'} and '¯' in d:      # 形态二：Â¯ 混合
        emit_raw(core)
    else:
        emit_translate(core.decode('cp1252'))
```

实测规模：ATOMIC 约 291 个文件含此类行，共 **1498 行**（含镜像副本）；逐字节比对 **0 处不一致**。
⚠️ 控制台里这类行看起来是乱码 —— **这是正常的**（终端按 GBK 解 `0xAF`），文件本身正确。

### 17.2 标题行口径（`Battle of X` / `Operation X`）

**只约束「标题行」（文件首行）**；正文里的 `Battle of X` 按散文译为「X战役」（中文惯用）。

| 英文形态 | 译法 | 已交付实证 |
|---|---|---|
| `Battle of X` / `Battle at X` / `Battle in X` | **`X之战`** | 特纳鲁河之战 · 阿劳西奥之战 · 卡塞林隘口之战 · 鲁尔之战 |
| `YYYY Battle of X` | **`YYYY年X之战`**（年与名之间**无空格**） | AG `公元前102年 - 韦尔切利之战` |
| `Operation X`（代号） | **`X行动`** | 十字军行动 · 堡垒行动 · 天王星行动 · 费利克斯行动 |
| `X Tank Battle` | `X坦克战` | 普罗霍罗夫卡坦克战 |
| 名词性 `Manchurian Operation` | `满洲战役`（非代号，按名词短语） | — |

⚠️ **反向判据**：若标题写成 `X战役`（如 ATOMIC 原译 `柏林战役` / `苏奥穆斯萨尔米战役`），
**与已交付 3 个 efile 口径冲突，须改为 `X之战`**。

### 17.3 独立校验（agent 自述不可信）

12 批并行 ⇒ 三类必须独立复核，**不能采信 agent 自报**：

| 校验 | 手段 | 本批抓到的真问题 |
|---|---|---|
| 结构 | 按输入**骨架**比对（head 逐字节 + 每段 `\r\n` 计数 + 正文 `\n` 计数） | 批 11/12 各 32/35 处 `\r\n` 丢失（agent 写入工具归一化） |
| 内容 | **长度 vs 汉字数**启发式扫描 | `Forward23i.txt` 标题重复 + 整段丢失（行数 +1/−1 抵消，逃过计数校验） |
| 一致性 | 中文变体 → 归一（键必须是**中文**，按英文键 0 命中） | 12 agent 同句最多 12 译法；归并 912+116+67+55 处 |

---

## 18. ⭐ `.xscn` 组内「二进制项」（2026-09-28，BASEKORP 发现）

**现象**：`xscn.py verify` 报某文件 `尾部残留 1438 B`（BASEKORP `bc_it_teu.xscn`）。

**根因**：组内条目**不全是字符串** —— 存在**非可打印的二进制项**（实测 `b'\x04q~\xde\x90\x0c'`，疑为坐标/marker）。
它**同样以 `u16 长度 + L 字节` 的形式占据槽位**，但内容不是文本。
旧版 `parse()` 的 `_printable` 守卫遇到它就 **`break` 整个组** ⇒ 后续条目全部漏读。

**判据**：一个文件解析是否正确，**唯一可靠标准仍是「解析位置 == 文件长度」**。
BASEKORP 该文件：组 0 `cnt=34`（33 串 + 1 二进制项）+ 组 1 `cnt=46` ⇒ 80 条目，恰好到文件尾 ⇒ 结构自洽。

**修复**：非可打印项 ⇒ **不登记为可译条目，但 `off += 2 + L` 继续推进**（不是 break）。

```python
if all(_printable(b) for b in data[off + 2:off + 2 + L]):
    items.append((gi, k, off, L))      # 可译
# else: 二进制项 —— 跳过登记，但仍推进 off
off += 2 + L
```

**回归**：已交付 6 个 efile 条目数与残留**完全不变**（0 残留）；
BASEKORP 由 48,430 → **48,490**（+60 条，原漏读），残留 1 → **0**。
⇒ **只对原本解析失败的文件生效，严格改进，无回归。**

### 18.1 误判警告：`_printable` 不该用于「判断条目是否文本」

它是**启发式守卫**，只应用于「发现明显异常时保守退出」。
**绝不能**把它当作「组是否结束」的信号 —— 组结束的唯一信号是 **`cnt` 读完**。

---

## 19. ⭐ 场景 `.txt` 的第三层：`label`（地图标签）（2026-09-29，BASEKORP 收官）

### 19.1 层识别：`rep-list.tsv` 的 `kind` 是个**启发式**，会漏层

`work\basekorp\txt_workbench.py::is_label_file()` 判据：

```python
lab = sum(1 for l in ls if len(l) <= 40 and not SENT.search(l) and len(l.split()) <= 5)
return lab >= max(3, 0.7 * len(ls))     # SENT = [.!?,;]
```

⇒ 一整个 efile 的 `.txt` 会被切成 **三桶**：`prose` / `label` / `empty`。
**散文流程 `translate_prose.py` 只吃 `prose`** ⇒ `label` 桶被**结构性跳过**，覆盖率永远差这一块
（BASEKORP 卡在 94.4%，看起来像漏译，其实是分层遗漏）。

`label` 桶内容（**异构**，别当成纯地图标签）：

| 内容 | 例 |
|---|---|
| 场景名（`.txt` 第 1 行） | `Guadalajara` `Zitadelle` `Crossing the Dnipr` |
| 河名 / 地名 | `Dnepr River` `Volga` `Boulay-Moselle` `Stassfurt` |
| **部队番号链** | `125/21` `731/711` `2/8 FldRAA/-/9Aus [XXX]` `1,2./II/190/-/90Le [DAK]` |
| 地图设施标记 | `State Farm` `Harbour` `Blown Bridge - repair crew needed` |
| 战役说明 / 简报头（短行版） | `ROMANIAN CAMPAIGN 1941-1945` `Kustrin` `Herr General` |

⚠️ 反直觉点：**裸数字行多半是番号，不是坐标。**
`bcaen.txt` 的 `125/21` `731/711` `716` 对应诺曼底德军第 21 装甲师（第125/第192装甲掷弹兵团）、
第711/第716步兵师（第731/第744步兵团）—— 全是真番号 ⇒ **必须按「本单位/上级」链译**，不能当坐标保留。
`bseelow.txt` 的 `27/11G` `805/230` `248` `5G` 同理解作 `第27/第11近卫`、`第805/第230`、`第248`、`第5近卫`。

### 19.2 ⭐ 主力手段：复用 `.xscn` 映射表（跨层一致性的免费午餐）

`.xscn` 尾部串区**组 0 ＝ 场景 `.txt` 名单的镜像**（组 1 才是部队番号链），
因此已交付的 `bk-xscn-map.tsv`（`src→dst`）**天然覆盖 `label` 层绝大多数唯一行**
（BASEKORP 实测 **2,955 / 3,153 ＝ 93.7%**）。
⇒ **复用即自动满足跨层一致铁律**，只需人工补剩余缺口（BASEKORP 200 条）。
实例：`ac821salern.xscn` 组 1 `第1/第36`、`第3/第36`、`第751`、`美国陆军航空队` ↔ `ac821salern.txt` 逐条对应。

工具：`work\basekorp\gen_label_zh.py`
填译优先级 ＝ `label-zh.tsv`（人工）> `bk-xscn-map.tsv`（`.xscn` 镜像）> **报错**（绝不静默留英文）；
两阶段（全算完 → 无缺口才落盘）+ `--dry` + 逐行 GBK 前置校验 + 回读校验；
输出 `<efile>\TEXT-ZH\SCENARIO\<同名>.txt`，GBK / 无 BOM / CRLF。

### 19.3 ⚠️ 坑一：`bk-xscn-map.tsv` 是**三列**，误读会静默灌制表符

表头 `src \t dst \t note`，`note ∈ {det, llm, cross, det-resid, title}`，31,742 行**全部带 note**。
用 `line.split("\t", 1)` 读 ⇒ **note 被并进译文** ⇒ 每条标签行尾部多一个 `\tXXX`
（BASEKORP 会污染 **6,236 个实例**，且行数/编码校验全过 ⇒ **完全静默**）。
**正确读法**＝`line.split("\t")` 取 `c[1]`，与 `work\xscn\xscn.py::load_map` 一致。
生成器已加守卫：「译文含 `\t` / `\r` / `\n` 即报错」。

### 19.4 ⚠️ 坑二：`¯`(U+00AF) **在 GBK 无编码**

战役说明文件（`dragrom.txt` / `mussoak.txt` / `rcampdfr.txt`）有一行标题下划线 ＝ 29 个 `¯`
（与 §9.5 的「排版分隔线」同源）。裸写会落进 cp1252 高字节区 —— 正是**假汉字陷阱**。
⇒ 按视觉等价换 **`─`(U+2500, GBK `A9A4`)**，生成器内置 `¯→─` 兜底 + 逐行 GBK 前置校验。
（同批不可编码字符都要这样兜底，别指望 `encode('gbk')` 会提醒你 —— 它只会在写盘时炸。）

### 19.5 战役说明文件（`.txt` 短行版）的行结构

`dragrom/mussoak/rcampdfr` 是**战役选择屏**的说明文本：

```
<标题行>（含尾部空格填充）
¯¯¯…（29 字下划线）
Version:  Apr-2019
Number of Scenarios: 17
Player Country: Romania
Equipment file: Basekorp
Campaign Designer: Dragdasan
Modified by Brian Gosley aka Puma
<空行×2>
<正文段落>
```

既有口径（`standard-glossary.tsv` 有先例）：`玩家国家：X` · `场景数量：N` · `战役设计者：X` ·
`版本：X`（`Version: 3.1`→`版本：3.1`）· `Factory No N`→`N号工厂` · `Blown Bridge - repair crew needed`→`被炸毁的桥梁 - 需要抢修队`。
**行数、空行位置、尾部空格填充一律保持**。

### 19.6 简报头文件（`*_i.txt` 短行版）的标题口径

`10airwar_i.txt` 原文首行 `10Air war` → 已交付译文 **`10 空战`**
⇒ 口径 ＝ **`编号 + 空格 + 译名`**（编号保留）。故 `3Bzura` → `3 布楚拉`。
同批：`Herr General`→`将军阁下`、`Good Luck`→`祝您好运`。

---

## 20. ⚠️ `progress.py` 的 `parse_xscn` **未同步 §18 的 `_printable` 守卫**（2026-09-29 发现，先报不改）

§18 的修复只落在 `work\xscn\xscn.py::parse`；`work\audit\progress.py::parse_xscn` 是**另一份实现**，
它把**每一个 `u16 长度 + L 字节` 槽都登记为可译条目**，没有非可打印判断。

后果（实测）：

⚠️ **订正（2026-09-29 晚，已修复）**：本文初稿用了一个**偏严的** `printable` 试探
（`32<=c<127 or 0x81<=c<=0xFE`），把 0x7F/0x80/0xFF 也算作非文本 ⇒ **误报 16 个**。
按 §18 真实判据（`b >= 0x20 or b in (0x09,0x0A,0x0D)`）复测，全库只有 **3 个**：

| efile | `progress.py` 条目 | 其中非文本槽（真实） |
|---|---:|---:|
| BASEKORP | 48,491 → **48,490** | 1 |
| OPENAK | 22,905 → **22,904** | 1 |
| LXF | 90,714 → **90,713** | 1 |
| **全库** | 298,433 → **298,430** | **3** |

（KAISER 初稿记 5 个，实为 **0**。）

⇒ ① 条目数偏大（BASEKORP 与 §18 记录的 48,490 差 1）；② 幻影条目会落进 `leak` 计数
（BASEKORP 35 条疑似漏译里，`bc_it_teu.xscn` 的 `\x04q~\xde\x90\x0c` 明确是此例）。
**修法**＝把 §18 的守卫照搬进 `progress.py`（跳过登记、仍推进 `off`）。
属**真源脚本变更**，先报不改。


---

## 21. ⭐ `progress.py` 三处判据修正（2026-09-29，用户批准）

### 21.1 `.xscn`：`parse_xscn` 补 §18 的 `_printable` 守卫

见 §20。效果：全库条目 298,433 → **298,430**（−3），leak 111,793 → **111,790**（−3）。
**已交付 6 个 efile 的条目数逐格不变**（回归为零）。

### 21.2 `.txt` 判据加「短标签」分支 —— `txt_is_zh()`

旧判据 `zh_score(中文侧) >= 3`（最长**连续**汉字段 ≥3）会**漏计 2 字短标签文件**：
`bberlin.txt`＝「柏林」、`bchannel.txt`＝「海峡」、`bdenmark.txt`＝「丹麦」、`bdover.txt`＝「多佛」、
`bnether.txt`＝「荷兰」、`cm4don.txt`＝「顿河」。

新判据（保守）：

```python
def txt_is_zh(b, fake=frozenset()):
    if zh_score(b, fake) >= 3:
        return True
    return zh_score(b, fake) >= 2 and not LAT.search(b.decode("gbk", "replace"))
```

⇒ 后半段只在**全文件无残留拉丁字母**时才认，不会把半汉半英的文件算成已译。
效果：`.txt` 已中文化 5,071 → **5,078**（BASEKORP +6、OLGWW2 +1，其余 efile 不变）。

### 21.3 `.txt` 分母剔除空壳（与 §三 注 3 的 `.ply` 同口径）

`strip()` 后为空的 `.txt` 无正文可译，**全库仅 BASEKORP 有 50 个**。
不剔则 BASEKORP 永远卡在 `2344/2394 = 97.9%`，「完成」所需的 **>99% 不可达**。

⇒ BASEKORP `.txt` 报表 2,338/2,394(97.7%) → **2,344/2,344(100.0%)**，
并首次进入「完成 efile」列表（现 6 个：AG、AO、BASEKORP、NASHORNPBEM、OLGWW2、OPENPG）。

### 21.4 复算与投影

- 全库合计：`.xscn` 298,430 · `.txt` 14,967（剔空壳后）· `.txt` 已中文化 5,078（33.9%）
- `docs\00` §三 的生成区块已按新真源重跑覆盖；
  「其余 efile 工作量」手写投影也重算为 **15 个 efile**：
  `.xscn` **223,964 条 / 111,067 唯一**、根级四件套唯一串 **37,331**、
  场景 `.txt` **11,221 个 / 7,249 KB**、`.ply` 有正文 **14**。

### 21.5 由此暴露的独立问题（未修，待决）

**`ATOMIC` 并未真正收官。** 新矩阵显示其 `.xscn` 含汉字 16,545/17,576（94.1%）、
**疑似漏译 761**（4.3% > 0.5% 阈值）⇒ **不在「完成」列表**。
抽样确认这 761 条是 **cp1252 原文残留**而非舰名：
`F黵stenwalde`(=Fürstenwalde)、`L黚ben`(=Lübben)、`7. Fallschirmj鋑er-Division`、
`K鋠linge River (L鰀de River)`、`Kostrzyn nad Odra (K黶trin)`。
独立探针 `work\audit\_xscn_untranslated_probe.py`（只看 cp1252 变音符 + 拉丁词形）复核为 **324 条**；
同探针下 `AG`/`AO`/`NASHORNPBEM`/`OPENPG` **均为 0** ⇒ 探针有效。
与 `MEMORY.md`「L9 `.xscn`：…**ATOMIC**… 全译」的记载**冲突**。

---

## 22. ⭐ 外语罗马字条目的判读法：**邻域 + 音系**（2026-09-29，COMWW2 实战）

> 场景：`equip.txt` / `names.txt` 里大量成串的罗马字条目（`Bahitsu` / `Dtam-ruat` / `Hadimernok` / `Oszver` …），
> 既不像装备型号、又不敢猜。**不要靠「像日语」猜** —— 实测 COMWW2 的 42 条待考里日语只占约 **1/4**。

### 22.1 邻域证据（主证据）

`equip.txt` 是扁平列表（每行一个装备名），**但同类装备会成簇** —— 邻域即「国别 + 品类」证据：

| 段 | 邻域特征 | 实测例 |
|---|---|---|
| 马匹段 | `Cavallo` / `Konie` / `Caballos` / `Paarden` / `Hevonen` / `Pferde` / `Karutca` | `Bahitsu`→馬匹、`Chema`→车马 |
| 舰艇段 | `Gunboat` / `MTB` / `Kagero` / `Akagi` / `Maestrale` | `Reua`→เรือ＝舰艇 |
| 工兵段 | `Sapper`×N / `Sapeur` / `Utasz` / `Genie` | `Hadimernok`→hadmérnök＝军事工程师 |
| 驮畜段 | `Mule`×3 / `Mulas` / `Maulesel` | `Oszver`→őszvér＝骡、`Viuchny`→вьючный＝驮畜 |
| 苏军段 | `Udarnye Voiska` / `Kommissar` / `PPSh-41` | `Drushinizi`→дружинники＝义勇兵 |
| 兵员段 | `Ta-haan` / `Pon Maa` / `Sa-mak` 并列 | 士兵 / 骑兵 / 志愿兵 |

### 22.2 音系证据（辅证据，快速分国）

- **泰语 RTGS**：`aa`（Maak/Saai/Paan）、`dt-` 起首（Dtam-ruat＝ตำรวจ）、`eua`（Reua＝เรือ）、`-ik`/`-at` 结尾
- **日语**：**无闭音节**（除 `n`）⇒ `Maak`/`Saai`/`Paan` **不可能是日语**；`-tsu`/`-hei`/`-tai` 是日语特征（Bahitsu/Keishu）
- **匈牙利语**：`sz`/`gy`/`ő`（Oszver＝őszvér、Hadimernok＝hadmérnök）
- **俄语**：`vya`/`zh`/`-ny`（Viuchny＝вьючный）
- **汉语拼音**：`zh`/`x`/`q` 起首、`-jiao-`/`-jun`/`-kuaiban` 音节结构

### 22.3 ⛔ 两条硬纪律

1. **能确证才落笔，不能确证就登记**。`Chema` 可确证＝车马（chē+mǎ，且在马车型段），
   但 `Biao/Gao/Guang Chema` 的**首字**无法确证 ⇒ **登记，不瞎填**（同 AG 批「拼音实为年号/帝名」那类，但那里有原文可反查，这里没有）。
2. **`donor 恒等保留` 是弱证据，会继承 donor 自己的漏译**。COMWW2 实测：该档把
   `Building` / `Hangar` / `Milice` / `Politi` / `Trekpaarden` / `Paarden` / `Pferde` / `Chevaux` / `Caballos` 等
   **普通名词**当口径留了下来（534 行「原文＝译文且含字母」里夹着这些）。
   ⚠️ 佐证：已交付 efile 里 `Zware Paarden`→重马、`Lichte Paarden`→轻马 **都译了**，裸 `Paarden` 却留着 —— 典型 donor 不一致。
   ⇒ **该档只应用于「装备型号 / 舰名 / 舰级 / 编号」**；出现**普通名词**（小写单字词、设施名、编制名、马匹词）时**必须人工介入**。

### 22.4 复查手法（一条命令级思路）

```python
# 找出「被判保留但其实是普通名词」的行：
eq = {x.strip() for x, y in zip(src, dst) if x.strip() == y.strip() and re.search(r"[A-Za-z]", x)}
# 再看其中的 单小写词 / 设施名 / 编制名 / 各国「马」词
```
⚠️ 比较时**必须 `strip()` 两侧** —— `names.txt` 的源行带**尾部空格填充**，直接 `x == y` 会漏掉一整批。

### 22.5 一条错译的教训

`Ta-haan` 曾被译成「登陆」。泰语 **ทหาร (thahǎn)＝士兵**。
⇒ 外语词**宁可不译也不要望文生义**；错译比保留原文更有害（读者无从察觉）。

---

## 23. ⭐⭐ 装备名的**图标码反查**：`equip.xeqp` → `OpenIcons.keep` → `OpenIcons.csv`（2026-09-29，COMWW2 实战）

> 用途：当 efile 的 `equip.txt` 出现**罗马字外语名/生造名**（`Keishu`/`Bahitsu`/`Jitensha`/`Mutuski`…）而全库无任何文档可查时，
> 用它把条目**至少归到确定的功能类别**，并偶尔直接读出词义。
> 这是继「邻域＋音系」（§22）之后的**第三条判据**，且是唯一可**完全机械化**的。

### 23.1 链路与结构

```
equip.txt 第 N 行  ↔  equip.xeqp 第 N-1 条记录  →  记录内 4 个图标槽（相对偏移 72/80/88/96）
                                              →  假码（可能不在图标表里）
                                              →  OpenIcons.keep（假码;真码）  →  OpenIcons.csv 的 Description
```

| 对象 | 结构 |
|---|---|
| `equip.xeqp` | **4 字节头**：`u16[0]=2`、`u16[1]=记录数`（COMWW2 为 4054）；其后 `记录数 × 120 字节` |
| 记录 | 图标槽在记录内相对 **72 / 80 / 88 / 96**，每槽 8 字节＝「码（≤5 字符）+ NUL 填充」（4 槽通常同值） |
| `equip.txt` | **第 1 行是版本头**（如 `VERSIONOpen Composite v1.02F`，非装备）；末行空 ⇒ 行 N ↔ 记录 N−1 |
| `OpenIcons.csv`（游戏根） | 17,908 条，列 `IconID;Description;Color;IconClass;Nation;Chassis;IconStyle` |
| ⭐ `OpenIcons.keep`（游戏根） | 2,723 条 **`假码;真码` 回落表**（表头 `*Fake;Real`） |

⚠️ **两个坑**：
1. **不先过 `OpenIcons.keep` 会误判**：COMWW2 大量引用「假码」（`WDF77`/`H41P`/`SBC22`/`TD79`/`KKT1`/`JK44`…），
   它们在 `OpenIcons.csv` 里**查不到**，乍看像「悬空引用」；经 keep 还原成真码后全部有解。
   （例：`WDF77→JKT18`、`SBC22→JKS95`、`TD79→BNC90`、`KKT1→JCN64`、`JK44→JCI52`。）
2. **图标是「最接近可用」而非精确对应** ⇒ 图标只能给**类别**（步兵/骑兵/装甲车/牵引车/舰船…），
   **不能当词义**。少数情况图标描述里**直接写了该单位**（`JKS93 Jiaotache (Bicycle x3)`、`FZ150 Type 97-Kai Shinhoto Chi-Ha`），
   这时才算「词义级」证据。

### 23.2 本轮据此定案的 3 条（COMWW2）

| 原文 | 图标码 | 图标描述 | 结论 |
|---|---|---|---|
| `Shin Hoto` | `FZ150` | Type 97-Kai **Shinhoto** Chi-Ha | ＝「新砲塔型」⇒ **新炮塔**（同文件另有 `T97 Chi-Ha` = `FZ149`） |
| `Hara Kamei` | `JK331` | Sanbo Honbu (HQ Command Infantry x3) + Radio | ＋ KAISER `README\_UNIT_NAME_TRANSLATIONS.txt` L226 明写 `Hara Kamei: Field Command` ⇒ **战地指挥部** |
| `Jiaotache` | `JKS93` | **Jiaotache** (Bicycle x3) / WW2 China Nationalist | 脚踏车 ⇒ **自行车** |

其余 27 条**只拿到类别**（畜力车 3 / 马拉机枪车 3 / 马拉炮兵 4 / 骑兵类 2 / 驮骡 1 /
步兵类 7 / 架桥工兵 1 / 摩托车 1 / 装甲车 1 / 牵引车 3）⇒ 按「**类别 ≠ 词义，不落笔**」登记。

### 23.3 顺手确认的两条事实

- **`Osaka` 不是地名泛指**，而是 `WDG06` = **Type 92 HoKoKu-Go Osaka 装甲车**；`SNLF` → `WDG05` = **Type 93 Sumida**
  （上海海军特别陆战队确用过九三式装甲车 ⇒ 图标分配是有意为之，不是乱指）。
- **IJN 古国名舰级确实存在**：L1931–1946 一簇里有 `Ise Class`（伊勢）、`Nagato`（長門）、`Fuso`（扶桑）等令制国名，
  但**只在这一簇**，且形如 `X Class` 或单名；同簇的 `Mutuski` 是**驱逐舰「睦月」**（月名法，非国名）。
  ⇒ 判断「某名是不是舰级名」的正解＝**看它落不落在这簇**，而不是看它像不像日语。

### 23.4 复用价值

全部 15 个未开工 efile 都有 `equip.xeqp`，而 `OpenIcons.csv`/`OpenIcons.keep` 是**游戏根级共享**的。
⇒ 这套反查对**其余 15 个 efile 的根级 `equip.txt`（含 223,964 条 `.xscn` 之外的 4 万余行装备名）同样适用**，
是后续大块装备名汉化的**第一判据**。
工具已落地：⭐ **`work\comww2\probe_equip_icons.py <EFILE>`**（`--lines A-B` / `--grep 串` / `--todo 文件`；
COMWW2 实测 30/30 有解、0 悬空）。换 efile 直接用：`python probe_equip_icons.py KAISER --lines 400-430`。

---

## 24. ⭐⭐ 跨 efile `.xscn` 词典：**备份原文 ↔ 已交付件** 逐条配对（2026-09-29，COMWW2 实战）

> 用途：新 efile 的 `.xscn` 有大量串与已交付 efile **同源**，直接复用即自动满足跨层/跨 efile 一致。
> ⚠️ **不要用各 efile 的 `*-xscn-map.tsv` 当唯一来源 —— 那些表不完整。**
> 实证：`EFILE_BASEKORP` 部署件里有「丘陵」，但 `bk-xscn-map.tsv` **查不到该行**（该表是部分回填）。

### 24.1 方法

```
backup/ORIGINAL-<EFILE>/SCENARIO/<f>.xscn   （纯净原文，7 个 efile 已备）
        ↕ 按 (文件, 组号 gi, 序号 idx) 逐条配对
D:/OpenPG2/<EFILE>/SCENARIO/<f>.xscn        （已交付中文件）
⇒ src→dst 全量记录（含恒等对），按 efile 投票
```

工具：⭐ **`work\xscn\build_dict.py`** → 产出
- `work\xscn\_xscn_dict.tsv`（`src \t dst \t #efile \t 实例数`；多译法时每个 dst 一行，按支持数降序）
- `work\xscn\_xscn_conflicts.tsv`（**只列真冲突，不自动择一** —— 承「冲突并存可接受、擅自择一不可接受」）
- `work\xscn\_xscn_dict_stat.txt`

### 24.2 实测（2026-09-29）

| efile | 配对文件 | 真译文对 | 恒等对 |
|---|---:|---:|---:|
| AG | 86 | 7,147 | 1 |
| AO | 38 | 188 | 0 |
| ATOMIC | 277 | 16,550 | 1,026 |
| BASEKORP | 647 | 47,861 | 628 |
| NASHORNPBEM | 1 | 248 | 0 |
| OLGWW2 | 187 | 13,730 | 2,328 |
| OPENPG | 54 | 2,329 | 0 |
| **合计** | **1,290** | **98,053** | 3,983 |

**词典唯一 src 47,731；多译法冲突仅 50 条（0.1%）**，且多为细微变体（`CLEAR` 空地(63)/开阔地(1)、`LAKE` 湖(36)/湖泊(1)）。

### 24.3 ⚠️ 与官方 UI 词的冲突（需裁定，不擅自定）

游戏的 `OPENGUI\strings-zh.txt` **L22–41 是官方 `[terrain]` 中文名表**：
`开阔地/城市/机场/森林/树篱地/丘陵/山地/沙漠/沼泽/海洋/河流/要塞/港口/溪流/断崖/不可通行河流/崎岖地/自定义/公路/铁路`。

- `CLEAR`：官方＝**开阔地**，但已交付 `.xscn` 主流＝**空地（63 票）** ⇒ 本层可复用则沿用上游「空地」，**冲突登记待裁**。
- `FOREST`→森林 ✓一致、`HILL`→丘陵 ✓、`STREAM`→**溪流**（取官方）、`LAKE`→湖 ✓。

### 24.4 ⚠️ 坑：批次数据文件**必须无 BOM**

`xscn-new-*.tsv` 一旦带 BOM，`utf-8-sig` 只吃掉**文件首个** BOM；
若脚本又按「第 0 行是表头」跳过，会把首条数据行连 BOM 一起当表头丢掉 ⇒ 首条静默失效
（本轮 `COUNTRYSIDE` 就是这样被吞掉，靠「残留清单」才发现）。**写批次文件后必须验字节。**

### 24.5 复用成效（COMWW2）

COMWW2 `.xscn` 唯一串 **9,066** ⇒ 词典/旧表命中 **3,120 条（34.4%）**；
再用「图鉴＋番号链口径」人工补批次 1（freq≥8 共 152 条）后合计映射 **3,272 条**，apply 后：

| 指标 | 前 | 后 |
|---|---:|---:|
| `.xscn` 含汉字条目 | 0 / 18,030 | **8,273（45.9%）** |
| `.xscn` 唯一非中文串 | 9,066 | **5,821** |
| 结构偏差文件 / 尾部残留 | 0 | **0**（`verify` 逐文件核过） |

剩下 5,821 条唯一串以 freq<8 的长尾 + 9 条**按口径保留**（`[55A]`/`[44A]`/`[51A]` 方括号代号、`FC`/`NG`/`BC`/`LLv.24`/`1Ft/4AF`/`X/TF Rasanen` 未知缩写）为主。

### 24.6 批次 2（freq≥5，298 条）与三条口径纪律（2026-09-29）

**工具链**：`work\comww2\gen_xscn_batch2.py`（**规则引擎 + 人工表**，比手打稳）→ `build_xscn_map.py` → `xscn.py apply`。

规则引擎要点（全部有先例）：
| 规则 | 例 |
|---|---|
| 纯数字 / 纯罗马(≥2 位或 `I`/`V`) → `第N` | `CCXXVIII/116`→第228/第116 · `MXIX/70`→第1019/第70 |
| **数字 或 罗马数字** + 英文序数后缀（可省）+ **已知后缀** → `第N+中文` | `DXCI/176th Rifle Div.`→第591/第176步兵师 · `XXIVPz`→第24装甲 |
| 「缩写 + 空格 + 数字」→ `第N+中文` | `StuG.Brig. 303`→第303突击炮旅 |
| **后缀未知 ⇒ 整 token 保留**（绝不半译） | `1/CA`→第1/CA · `CXXXVI/TB`→第136/TB |
| **纯字母 token 一律不拆罗马** | `L` 不译 50、`CA` 不译 100集团军 |

⚠️ **三个必须记住的教训**：
1. **单字母 `L`/`C`/`D`/`M`/`X` 不是罗马数字** —— 首版把 `L` 译成 `第50`、把 `CA` 拆成 `第100集团军`，纯属灾难。
   规则：bare Roman 只在 `len>=2` 或 ∈{`I`,`V`} 时认。
2. **罗马数字上限要留到 ≥2000**（首版卡 1000 ⇒ `MCXCV`(1195)/`MCCCXXXI`(1331) 全被丢弃）。
3. **英文序数后缀 `th/st/nd/rd` 必须先剥**，且注意后缀词前的空格（首版漏剥 ⇒ `70th Rifle Div.` 原样留下）。

### 24.7 ⭐ 纪律：**词典优先于人工批次**（承上游口径）

`build_xscn_map.py` 的优先级已固化为 **词典（已交付件实证）> 归一化（词典派生）> 人工批次（只填空缺）**，
并**打印冲突**。实测本轮抓到 **6 条我「自造」的译法与既有译法冲突**，一律取既有：

| 原文 | 既有（采用） | 我自造（弃） |
|---|---|---|
| `Destroyed Bridge` | 被毁桥梁 | 被摧毁的桥梁 |
| `STEEP HILL` | 陡坡 | 陡峭丘陵 |
| `Kroptin Tank Factories` | 克罗普廷坦克工厂 | 克罗普京坦克工厂 |
| `Voltic Caves` | 沃尔季克洞穴 | 沃尔蒂克洞穴 |
| `The Barrowlands` | 古墓岗 | 巴罗兰兹 |
| `Labinski  Jewish Quarter` | 拉宾斯基  犹太区 | 拉宾斯基犹太区 |

⇒ **归一化匹配（折叠大小写/空白/尾点）是发现这类冲突的关键手段**，别只当"多捞几条"用。

### 24.8 COMWW2 `.xscn` 累计（两批）

| 指标 | 起点 | 批次1后 | 批次2后 | **批次3后** |
|---|---:|---:|---:|---:|
| 映射表条目 | 0 | 3,272 | 3,603 | **6,695** |
| 含汉字条目 | 0 / 18,030 | 8,273 | 10,044 | **14,958（83.0%）** |
| 唯一非中文串 | 9,066 | 5,821 | 5,489 | **2,410** |
| 结构偏差 / 尾部残留 | 0 | 0 | 0 | **0 / 0** |

- 批次 2＝`xscn-new-2.tsv`（freq≥5 共 298 条，改写 1,771 个实例 / 132 文件）。
- 批次 3＝`xscn-new-3.tsv`（**规则引擎跑全部余量**：输出 3,092 条 / 跳过 2,397 条，改写 4,927 个实例 / 129 文件）。
  ⭐ 关键做法：把规则引擎**参数化**（`gen_xscn_batch.py --todo F --out F --minfreq N`），
  一次跑遍全部余量——**能规则化的全拿下，规则化不了的一律不输出（保持原文）**，零猜测零返工。
- **残留 2,410 唯一串（3,166 实例）构成：含字母 2,401 / 纯数字符号 9** ⇒ 剩下全是**专有名词**
  （地名/单位名/SS 师名）与**按口径保留的未知缩写**（`[55A]`/`FC`/`NG`/`BC`/`LLv.24`/`1Ft/4AF`/`4GDNO`/`L`/`X`/`SSPol`/`FA`/`GM`/`RF`/`1SA`/`SSDR`/`2AF` 族）。
  ⇒ 后续批次只能靠**人工译名**（地名对齐既有译名库、SS 师名用通行译名），不再有机械红利。

### 24.9 ⚠️ 未解异常（**待查，不猜**）

`Labinski  Jewish Quarter` / `Kroptin Tank Factories` / `Voltic Caves` / `The Barrowlands` 这 4 条
在 **apply 之前**的 `xscn-uniq.tsv` 里查不到，却出现在 **apply 之后**的清单里（`grep -c Kroptin xscn-uniq.tsv` = **0**）。
apply 只会把命中项替换成中文，不可能"造出"未命中的英文串 ⇒ **导出侧可能漏算过部分条目**（原清单 9,066 或许偏低）。
**影响**：历史覆盖率读数可能略被低估；不影响已写入结果。**未深查，登记待查。**

### 24.10 批次 4/5：**宽松复用**与**通名合成**，以及残量的真实构成（2026-09-29）

机械档跑完后残 2,410 条，本轮又用两条**仍需证据**的路子拿下 153 条：

| 档 | 做法 | 产出 | 依据 |
|---|---|---:|---|
| **A 词集等价** | 与词典某条 src 的**单词多重集相同**（词序/标点差异） | 17 | 同一条地名（`Wkra River`↔`River Wkra`→弗克拉河） |
| **C 去括号/前缀** | 去掉 `[ ]`、序号前缀后命中 | 5 | 同上 |
| **通名合成** | `专名 + 通名` → **词典里的专名译名** + 中文通名 | 119 | **POLICY.md 规则 5 明许**（River→河、Airfield→机场、Lake→湖…） |
| **标准译名库** | `glossary\standard-glossary.tsv`（21,327 条）精确/归一命中 | 12 | 译名真源 |

⚠️ **B 档（整词包含）必须弃用**：它会「丢名字」或误配 ——
`Lake Velencei`→「湖泊」（只剩通名）、`Mor Airfield`→「机场」、`92nd Infantry Brig.`→「步兵」、
`Stronghold`→「英国皇家海军 斯特朗霍尔德」（错配 HMS Stronghold）。**只保留 A/C 与通名合成。**

⚠️ **译名库的单/双字母条目不可照搬**（上下文相关）：库中 `FA`＝巴斯克自治区空军、`RM`＝意海军、`L`＝教导部队，
但本 efile 语境不同 ⇒ **一律不复用**。库中大量命中的其实是**恒等映射**（`FC`→FC、`BC`→BC、`Z`→Z…），
它们是对「口径保留」的**确认**而非译文，已单独记录。

⚠️ 合成档的通名需**去重**：`Rhein river` 因词典 `Rhein`→莱茵河 而合成出「莱茵河河」⇒ 加「译名已含该通名则不再追加」守卫。
合成结果仍需**承上游**：`Grozny Airfield` 合成＝格罗兹尼机场，但既有＝**格罗兹尼（机场）** ⇒ 取既有。

### 24.11 残量 2,259 条（2,965 实例）的**真实构成**与后续作业面

| 类 | 条数 | 实例 | 性质 |
|---|---:|---:|---|
| 单词专名 | 987 | 1,226 | ⚠️ 半数以上是**按口径保留的缩写**（`FC`/`NG`/`BC`/`L`/`SSPol`/`FA`/`GM`/`RF`/`SSDR`/`X`…）＋单词地名（`Gromoslavka`/`Arad`/`Kovel`/`Malgobek`…） |
| 番号+字母（未知后缀） | 671 | 959 | **口径保留**（`4GDNO`/`77STG/2AF`/`2Ft/4AF`…），按政策不译 |
| 多词专名/编成 | 322 | 390 | 需人工（`Baltic Fleet`/`Northern Fleet`/`Volga Fleet`/`Krim-Front`/`Coal Freighter`/`Stalag VI C`…） |
| 专名+通名 | 244 | 295 | 需人工译专名，通名按政策（`Lake Velencei`/`Tyrrhenian Sea`/`Donest River`…） |
| 含斜杠链 | 28 | 33 | 需人工 |
| 方括号代号 | 7 | 62 | **口径保留** |

⇒ **真实待译 ≈ 1,300 条**（其余 ~950 条属政策保留）。**机械红利彻底耗尽**，且**多词名不得机械拼词**
（会造出「煤货船」式夹生译名）⇒ 批次 6 起是**纯人工译名批**：先 `专名+通名` 244 + `多词专名` 322（高频优先），
再单词地名 987（音译，须与 `standard-glossary.tsv` 既有译名对表）。

---

## 25. ⛔⛔ 跨 efile 词典的**污染源**：把「待译清单」误读成「映射表」（2026-09-29 发现并修复）

> 这是本工程迄今**最危险**的一类 bug：**静默错位、且优先级压过正确译法、直写游戏文件**。

### 25.1 病例

`work\comww2\measure_xscn_cov.py::load_maps()` 的 glob 是

```python
MAP_GLOBS = ("*/*xscn*map*.tsv", "*/*xscn*.tsv", "*/*-map*.tsv", "*/*map*.tsv")
```

`*/*xscn*.tsv` 会命中 **`work\efile-nashornpbem\xscn-todo.tsv`** —— 而那是**待译清单**，
格式是 `序号 \t 原文`（`104 \t Labinski  Jewish Quarter`）。
于是 `104 → Labinski  Jewish Quarter` 被当作「已交付件实证译法」载入，
经 `_xscn_covered.tsv` 进入映射表，**优先级高于人工批次**，最终写入 15 个场景文件。

同类被误读的还有：`ao\xscn-uniq.tsv`、`glossary\ag-xscn-uniq.tsv`、
`atomic\xscn-full.tsv`（`文件名 \t 0`）、`basekorp\bk-xscn-full.tsv` 等 ——
它们的 `c[1]` 是 **freq / 行号**，不是译文。

### 25.2 后果（实测）

| 表现 | 详情 |
|---|---|
| 错位译法 | `104→拉宾斯基 犹太区`、`135→克罗普廷坦克工厂`、`180→沃尔季克洞穴`、`167→古墓岗` |
| 单段数字被吞 | `100→连`（若上游表已污染则连带传播） |
| 静默性 | 行数/编码/结构校验**全部通过**，只有语义体检能发现 |

⚠️ 注意 `104`/`135` 在 `.xscn` **组 1（部队番号链）**里是**师级番号**，正确译法是 `第104`/`第135`。
错位映射把它换成了地名，**且看起来像正常中文**，肉眼极难发现。

### 25.3 两条修复（缺一不可）

1. **收窄 glob**：只认真正的 map 命名 —— `("*/*xscn-map.tsv", "*/*xscn-map*.tsv")`。
2. **内容守卫**（更根本）：载入时要求 `dst 含汉字` 或 `src == dst`（口径保留），否则**拒收并计数**。
   实测拒收 510 条。

`build_xscn_map.py` 同步加 `ok_dst()` 守卫（三档入口都过），
并新增「译文含 `\t`/`\r`/`\n` 即报错」。

### 25.4 体检工具

⭐ `work\comww2\audit_map_quality.py`（映射表模式体检：空译文/控制符/GBK 不可编码/中英混排成词/
连续重复字/长度异常/空白异常/恒等映射）
⭐ `work\comww2\audit_pollution.py`（**定位污染源**：逐 glob 命中的表统计「贡献了多少条非词典非真表条目」）
⭐ `work\comww2\verify_pollution_hits.py`（**核验污染是否已写入文件**：备份原文 ↔ 现状逐条配对）

### 25.5 教训

**「读别的目录的表」必须同时校验内容形态，不能只靠文件名 glob。**
所有「从多个来源聚合译法」的脚本都应默认带内容守卫。

---

## 26. ⛔ BASEKORP 历史误译：**纯数字被当成罗马数字**（`100 → 连`）

### 26.1 病例

`work\basekorp\bk-xscn-map.tsv` 有 **20 条**把纯数字段译成了「连」：

```
100/25        → 连/第25            （应为 第100/第25）
100//76MD     → 连//第76摩托化师
1/100/83MD    → 第1/连/第83摩托化师
I/100/50th Tk → 第1/连/第50坦克
397/100       → 第397/连           （应为 第397/第100）
100           → 连
```

**根因**：`C`（Company＝连）被正确译作「连」，但**纯数字 `100` 也被当成了罗马数字 `C`**。
⇒ 与 §24.6 的「单字母 `L`/`C`/`D`/`M`/`X` 不是罗马数字」是**同一类错误的两面**。

### 26.2 影响面与修复

- 全库体检：**只有 BASEKORP 受影响**（26 处实例 / 17 个文件）；AG/AO/ATOMIC/OPENPG/OLGWW2/NASHORNPBEM 全干净。
- 工具 ⭐ `work\xscn\audit_number_segments.py`（全 efile map 表扫「数字段 → 非『第N』」）
- 工具 ⭐ `work\xscn\fix_number_segments.py --target map|files [--apply]`
  - `map` 修真源表；`files` 以备份原文为对照**按位置**精确改写（用 `write_checked` 回读校验）
  - ⚠️ **单段情形要单独处理**：首版 `if "/" not in s: return None` 漏掉了裸 `100 → 连`，
    导致它存活并**继续经词典传播到 COMWW2**（第二轮才抓到）。
- 修复后复扫 = **0 处**；词典重建后 `100 → 第100`。

### 26.3 为什么「按串替换」不行

`连/第25` 既可能是 `100/25`（错）也可能是 `C/25`（对）的译法 ——
**同一个译串对应两个不同原文** ⇒ 必须**按位置**修，不能按串替。

---

## 27. 规则引擎的三个坑（`gen_xscn_batch.py`，2026-09-29 修）

1. **`strip()` 制造伪译文**：`tok()` 会 strip 段落前后空格，`"/".join()` 又不恢复 ⇒
   `I.R. 136/ 46. I.D.` → `I.R. 136/46. I.D.`（**只去掉一个空格、没有任何翻译**）。
   它逃过了 `d == s` 判定混进批次表（13 条）。
   修：`tr()` 要求**至少一段真被改动**，否则原样返回（主逻辑随即跳过）。
2. **方括号失守**：`54A]` 被译成「第54集团军」—— **丢掉 `]`**（原文是 `[54A]` 的变形）。
   修：**含 `[` 或 `]` 的串一律口径保留**。
3. **后缀词表必须分级**：整段（`Tank Bn.`）→ 逐词（`Bomber` + `Grp.`）→ 长度守卫。
   逐词要求**每个词都命中且拼完不剩字母**，否则整条保留（绝不半译）。
   ⚠️ 长度守卫（`len>=4` 或多词）是必需的：否则 `Div`/`G`/`M`/`A` 这类**单词后缀会被独译**
   （`X/Div` → `第10/师`）。

---

## 28. COMWW2 `.xscn` 收官读数（2026-09-29）

| 指标 | 起点 | 终值 |
|---|---:|---:|
| 含汉字条目 | 0 / 18,030 | **17,678（98.0%）** |
| 唯一非中文串 | 9,066 | **282** |
| 映射表条目 | 0 | **8,802** |
| 结构偏差 / 尾部残留 | 0 | **0 / 0** |
| 配对校验（17,267 条改动） | — | **0 错位** |

批次构成：词典复用 3,087（34%）→ 规则引擎 3,343（批 3/7）→ 人工精译 2,065（批 1/2/6a/6b）→
归一化/合成/译名库 148。

残留 282 条**全部为口径保留**：方括号代号（`[55A]`/`[44A]`/`[8A]`…）· 未知大写缩写
（`FC`/`NG`/`BC`/`FA`/`GM`/`RF`/`X`/`L`/`P`/`Z`/`CF`/`FF`/`TNG`/`DG`/`RSG`/`SWF`/`FNAF`…）·
未知编号缩写（`LLv.24`/`1Ft/4AF`/`4GDNO`/`77STG/2AF`/`1CavD`/`1BL`/`13E/14P/4P`…）。

## 29. ⛔⛔ 待译清单**带行号前缀**：`  N|` 不是原文的一部分（2026-09-29，COMWW2 prose 批）

**现象**：`_prose_narrative_todo.txt` 逐行长这样——

```
  1|Thanx for playing Stalingrad playtest! Any comments, ...
  2|Historical Note: Malta was one of the most heavily bombed ...
```

直接拿整行当 TSV 的键 ⇒ `gen_prose_zh.py` 干跑报「未覆盖」**纹丝不动**（799→799），
看起来像「译文没生效」，实际是**键 0 命中**。实测对比：

| 取法 | 命中权威键集 |
|---|---:|
| 整行（含 `  N\|`） | **0 / 715** |
| `re.sub(r"^\s*\d+\|", "", 行)` | **715 / 715** |

**根因**：清单是按频次排序后 `nl -ba` 式编号导出的，**编号是展示前缀**，不是原文。
`prose-miss.tsv`（生成器自己写的）才是裸原文。

**两层陷阱（比前缀本身更容易中招）**：

1.  **`prose-miss.tsv` 不能当权威键集**——`gen_prose_zh.py` 每次干跑都会把它
   **重写为剩余项**，键集会随进度**缩水**（715→470→270…）。拿它校验，先跑几批之后会
   误报「245 条不在权威键集」。
   ⇒ 必须**固化**一份：`_prose_authority.txt`（715 条，唯一，一次性从清单剥前缀生成）。
2. ⚠️ 已写入文件的坏键要用 `--purge` 剔除（按 `NUM_PREFIX` 匹配），不能靠重跑覆盖。

**修复后的三条硬纪律**：

- 键**永远**由「待译清单按行号取 + 剥前缀」得到，**不手抄**；
  译文单独写 `prose-dst-bNN.txt`，由 `merge_prose_block.py` 按**行号一一配对**。
- 每条键**逐条**校验 ∈ `_prose_authority.txt`，有一条不在就 `SystemExit`（不写盘）。
- 权威键集**固化**；`prose-miss.tsv` 只当「剩余清单」读，**不当基准**。

**脚本**：`work/comww2/merge_prose_block.py`（`--block/--from/--to`、`--check`、`--purge`）
· `work/comww2/build_prose_zh.py`（合成 `prose-zh.tsv`，原表优先、报冲突）。

## 30. ⭐ COMWW2 prose 层口径（2026-09-29，LLM 精译批）

**先查既有再落笔**（`将军阁下` 943 处、`历史注记` 24 处、`同志`、`胜利点`、`部署格` 均已定型）：

| 原文 | 定译 | 依据 |
|---|---|---|
| `Herr General` / `Herr Feldmarschall` | 将军阁下 / 元帅阁下 | 已交付件 943 处 |
| `Comrade Marshal` / `Comrade General` / `Comrade Zhukov` | 元帅同志 / 将军同志 / 朱可夫同志 | 苏方一律「同志」（既有 0 例「元帅同志」但有大量「同志」） |
| `Historical Note:` / `Note:` / `NOTE:` | 历史注记：/ 注：/ 注意： | BASEKORP 既有 |
| `VH` / `VHs` / `DHs` | 胜利点 / 部署格 | 既有 |
| ⭐ `BV` / `DV` / `V` / `TV` / `MV` | 辉煌胜利 / 决定性胜利 / 胜利 / 战术胜利 / **险胜** | ⚠️ **以本 efile 的 `strings_efile.txt` `[results]` 为准**：COMWW2 原文＝`Decisive Victory / Victory / Marginal Victory / Loss`，我已译「决定性胜利/胜利/险胜/失败」；`OPENGUI\strings-zh.txt` 是另一套（含「战术胜利」）。**跨 efile 不通用，按 efile 查** |
| `STAVKA` | 最高统帅部 | — |
| `Wehrmacht` / `Fuhrer`(原文拼错) | 国防军 / 元首 | — |
| 番号 | `4th Panzer Army`→第4装甲集团军、`XXXXX Korps`→第N军、`N Pz`→第N装甲师 | §五 |

**专名折写**：`Großdeutschland`→大德意志（ß→ss）；`Miklós`/`Szálasi`/`Ungvár`/`Martonvásár` 的
á/í/ó **GBK 可编码**，无需折写（`gen_prose_zh.py` 的 `gbk_safe` 亦有兜底）。
