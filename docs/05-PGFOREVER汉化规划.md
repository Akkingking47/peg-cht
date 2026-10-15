# PG Forever 1.021 汉化规划（侦察完成，待你决策）

- 目标：`D:\PGForever1.021`（PG Forever 1.021）
- 侦察日期：2026-09-20　·　**本报告阶段为只读侦察，未修改游戏任何文件，也未创建工作空间**
- 状态：**等待你确认范围与工作空间方案后再动工**

---

## 一、结论速览：它和 OpenPG2 不是一个东西

| 对比项 | OpenPG2（已完成） | **PGForever 1.021** |
|---|---|---|
| 引擎 | OpenGen 26.3.30.0，SDL2 + FreeType | PG Forever，`PGForever.exe` + **htmlayout.dll** |
| UI 实现 | 引擎绘制，字符串来自 `strings-xx.txt` | **HTMLayout 渲染 `*.htm` + CSS** |
| 多语言框架 | **有**（`strings-xx.txt` + `TEXT-XX\` 隔离目录） | **没有**（exe 内无 `strings-` / `TEXT-` / `UI_Lang` 任何痕迹） |
| 文本编码 | GBK(936)，依赖系统 ACP | **原生 UTF-16LE**（`.pgeqp` `.pgscn` `.pgcam` 均带 `FF FE` BOM） |
| 汉化方式 | 新增中文文件，原文零改动 | **必须直接改原文**（无隔离、无回落机制） |
| 一键回滚 | 删 `TEXT-ZH\` 即可 | **不支持** → 全量备份是硬性前置条件 |

> **一句话**：编码上它比 OpenGen 更友好（原生 Unicode，彻底摆脱 GBK 与 ACP 依赖）；
> 但工程上更危险——**没有官方隔离机制，改错了没有回退键**。

---

## 二、技术画像

- 主程序 `PGForever.exe`（753 KB），UI 引擎 `htmlayout.dll`（Terra Informatica HTMLayout）
- 启动方式：`PGForever.exe /game <名称>`（见 `pg.bat` `ag.bat` `kaiser.bat` `kuk.bat`）
- 模组（game）共 **38 个**：`PG`（原版二战）、`AG`、`waw`、`wss 1.5`、`Kaiser General`、`Elite Core`、`Pacific War *` 等
- 大多数 game 无自己的 `UI\`，共用 `Default\UI\`（103 个文件）→ **UI 汉化一次，全局受益**
- exe 内含 `UTF-8` / `UTF-16LE` / `UNICODE` 转换逻辑与 `CreateFontW`，Unicode 链路完整

---

## 三、文本分层地图（汉化对象清单）

| 层 | 内容 | 路径 / 格式 | 体量 | 编码 | 可译性 |
|---|---|---|---|---|---|
| **L1** | UI 界面文本 | `Default\UI\*.htm`（main / menu / settings / briefing / purchase / unit / result / casualties / hotkeys / options / about / choosegame / msgbox / savefile / deploy / newturn / neweqp / combatlog） | 约 20 个 htm，数百条 | ASCII（HTML） | ✅ 直接改 |
| **L2** | 装备表（单位名 + 类别） | `<game>\Scenario\equipment.pgeqp` | 39 个文件 / **34,797 行** | **UTF-16LE** TSV | ✅ 只译 Name / Class 列 |
| **L3** | 场景名与描述 | `<game>\Scenario\*.pgscn` | **999 个** | **UTF-16LE** 键值对 | ✅ |
| **L4** | **战役简报** | `<game>\Scenario\*.pgbrf` | **3,446 个 / 1,005,117 字符** | UTF-8/ASCII（`<p>…</p>` HTML 片段） | ✅ **最大工作量** |
| **L5** | 战役定义与胜负条件标签 | `<game>\Scenario\pg.pgcam` | 38 个 / 129 行 | **UTF-16LE** TSV | ⚠️ 标签是内部键，全文件需一致 |
| **L6** | 地形名与地名 | `<game>\Scenario\MAPNAMES.STR` | 38 个 / 约 22 KB | **定长二进制** | ⚠️ **高风险，需先探测** |
| **L7** | 引擎硬编码文本 | `PGForever.exe` 的 `.rdata` | 974 个宽串 / 约 **150–250 条**可见文案 | **UTF-16LE 宽字符** | ✅ **可汉化**（原地替换，见第九节） |

### L7 盲区实测样例（原以为不可译，现已确认为可翻译）

```
Air Defense   Last Turn   Effective Attack: %d   Effective Defense: %d
Close defense: %d   Air defense: %d   Ground defense: %d
Naval attack: %d   Hard attack: %d   Soft attack: %d
Rugged defense chance: %d%%   Can't attack: =0
ERROR: Could not open scenario file: '%s'
```

> 全部为 **UTF-16LE 宽字符串**，存储于 `.rdata` 节 → 可原地替换，详见**第九节**。

### 各 game 体量（节选）

| game | pgbrf | pgscn | equipment.pgeqp |
|---|---|---|---|
| **PG**（原版二战，推荐起步） | 178 | 38 | 479 行 |
| AG | 151 | 49 | 492 行 |
| Elite Core | 178 | 38 | 550 行 |
| waw | 375 | 103 | **4,790 行** |
| wss 1.5 | 182 | 39 | **4,571 行** |
| **全库合计** | **3,446** | **999** | **34,797 行** |

---

## 四、工作空间方案（需你拍板）

### 方案 A（推荐）：本工作区下建独立子工程 `pgforever\`

```
D:\DSH\军事游戏汉化\
  ├─ docs\            01–04 已有 + 05 本规划
  ├─ tools\           现有 txt-tool.ps1 等
  ├─ work\openpg\     （已完成）
  ├─ work\olgww2\     （已完成）
  └─ pgforever\       ← 新增，与 OpenGen 那条线物理隔离
       ├─ docs\
       ├─ work\       UTF-8 工作稿与映射表
       ├─ tools\      UTF-16LE 专用转换/校验脚本
       └─ backup\     原文件全量快照（必须）
```

**理由**：引擎与文件机制完全不同，且是覆盖式修改——独立子工程能把风险圈在笼子里；同时仍在同一个工作区，术语表与翻译口径可复用。

### 方案 B：并入现有 `work\pgforever\`

结构最简，但和"原文零改动"的 OpenGen 那条线混在一起，**容易误用 `TEXT-ZH` 的思路**——不推荐。

### 方案 C：另起顶层目录 `D:\DSH\PGForever汉化\`

彻底独立。适合你打算把它当作另一个项目长期运营；代价是术语资产要复制一份。

> 我的建议是 **A**。

---

## 五、备份策略（硬性前置，先于一切）

因为**没有隔离机制**，动工前必须做一次不可变快照：

```powershell
# 1) 全量镜像（39 个 game + Default\UI，约几百 MB，远小于全盘）
robocopy D:\PGForever1.021 D:\DSH\军事游戏汉化\pgforever\backup\origin /E /COPY:DAT /R:1 /W:1

# 2) 对文本层单独建 Git 仓库，保证每次改动可 diff、可回退
cd D:\DSH\军事游戏汉化\pgforever
git init && git add . && git commit -m "origin snapshot"
```

原则：**改一个文件前先确认该文件已进快照**；禁止批量脚本在未备份目录上直接写。

---

## 六、POC 冒烟验证（必须，成本约 30 分钟）

在动任何批量翻译之前，逐项验证——尤其 R1（`MAPNAMES.STR`）是整个方案唯一的硬拦路石。

| # | 验证项 | 方法 | 判定 |
|---|---|---|---|
| P1 | 中文在 UI 正常渲染 | 改 `Default\UI\settings.htm` 几个英文标签为中文，启动 `pg.bat` | 无方块/乱码 |
| P2 | 中文在简报渲染 | 改 1 个 `pgbrf` 为中文，进场景看简报框 | 正常显示、不截断 |
| P3 | UTF-16LE 中文被正确读取 | 改 `equipment.pgeqp` 前 3 条 Name 为中文（用记事本另存为 Unicode） | 单位名显示中文 |
| P4 | **`MAPNAMES.STR` 定长结构** ⚠️ | 改 1 条地形名（`Clear`→`开阔地`），看是否乱码/错位/崩溃 | **决定 L6 能否汉化** |
| P5 | 字体与字号 | htm/CSS 指定 `Arial` / `Tahoma`，观察中文是否过糊；必要时加 `Microsoft YaHei` 字体族 | 可读 |
| P6 | 布局溢出 | 重点看 `main.htm` 单位格（125×55px）、按钮标签 | 不裁切 |
| P7 | `game\UI\` 是否覆盖 `Default\UI\` | 在 `PG\UI\` 放同名 htm 测试 | 明确优先级 |

> P4 若失败，L6（地形名/地名）放弃汉化，仅保留英文——不影响其余各层。

---

## 七、分阶段路线图

| 阶段 | 内容 | 产出 | 前置 |
|---|---|---|---|
| **0** | 决策（工作空间方案、起步 game、范围） | 本规划签字 | — |
| **1** | 备份 + Git 快照 + POC（第六节 7 项） | 备份目录、`docs\06-POC报告.md` | 阶段 0 |
| **2** | **UI 层**（L1）：提取 20 个 htm 的英文串 → 映射表 → 回填；CSS 补中文字体族 | `work\ui\*.tsv` + 应用脚本 | POC 通过 |
| **3** | **装备层**（L2）：起步 game 的 `equipment.pgeqp`，只译 Name / Class | `work\<game>\equip-map.tsv` | 阶段 2 |
| **4** | **场景层**（L3+L5）：`*.pgscn` 的 Name/Description、`pg.pgcam` 标签 | 映射表 + 脚本 | 阶段 3 |
| **5** | **简报层**（L4）：起步 game 的 `*.pgbrf`（最大头） | 分组并行译文 | 阶段 4 |
| **6** | LQA：编码/BOM/行数/乱码/残留英文/禁用词/术语一致性全检 | 质检报告 | 每阶段末 |
| **7** | 扩展到第二个 game（机制已复用） | — | 单 game 完成 |

**起步 game 建议：PG（原版二战）** —— 文本量适中（178 简报 / 38 场景 / 479 装备），题材与你已完成的 OPENPG、OLGWW2 完全一致，**术语与译名可直接复用**，边际成本最低。

---

## 八、工作量估算

| 范围 | 体量 | 估算 |
|---|---|---|
| L1 UI（全库共用，一次搞定） | 约 20 个 htm | 0.5–1 天 |
| 单 game 核心（L1+L2+L3+L5，以 PG 为例） | 479 装备 + 38 场景 + 178 简报 | **1–2 周** |
| 单 game 完整（含全部简报译文精校） | 同上 + LQA | 2–3 周 |
| 全库 38 个 game | 3,446 简报 + 34,797 装备行 | **不建议**（数人月级） |

---

## 九、exe 硬编码文本的汉化可行性（已实测，结论：**可行**）

### 9.1 决定性事实

| 项目 | 实测结果 |
|---|---|
| 字符串编码 | **UTF-16LE 宽字符**（非 ANSI）——按 ASCII 搜索全部 0 命中，按 UTF-16LE 搜索全部命中 |
| 存储位置 | `.rdata` 节，VA `0x0007F000`，文件偏移 `0x7E200`，RawSize 115,200 |
| 节属性 | `40000040`（INITIALIZED_DATA / READ），磁盘可写 |
| 数字签名 | **无**（SECURITY 目录 size=0）→ 可自由修改，不会被系统拒绝 |
| 排布方式 | 紧凑排列，串间仅隔 `\x00\x00` 终止符，**几乎无余量**（实测每条之后仅 2–8 字节空位） |
| 字符串总量 | 去重 974 条；排除驼峰内部键（671）后，含空格/HTML/冒号的自然语言文案约 **390 条**；真正用户可见的 UI 文案约 **150–250 条** |

### 9.2 为什么这是最理想的情况

中文在 UTF-16LE 里每个汉字占 2 字节，**与英文每个字符占 2 字节完全相同**。
而中文表达通常比英文简洁，因此：

> **译文字符数 ≤ 原文字符数时，可以逐字节原地替换，长度只会缩短，绝不溢出。**

验证样例（`.rdata` 偏移 `0x82BF4` 起）：

```
Close defense: %d<br/>   →   近距防御: %d<br/>     (19 → 8 字符，安全)
Rugged defense chance: %d%%  →  顽强防御概率: %d%%   (27 → 9 字符，安全)
Tactical Bomber        →   战术轰炸机              (15 → 5 字符，安全)
Air Defense            →   防空                    (11 → 2 字符，安全)
```

### 9.3 三条铁律（违反即出问题）

1. **译文 UTF-16 字符数必须 ≤ 原文字符数** —— 脚本强制校验，超长的一律拒绝并报警
2. **只改 `.rdata` 的数据字节，绝不改动代码、指针、长度表** —— 因此**完全不受 ASLR / `.reloc` 重定位影响**
3. **白名单制，禁止批量无差别替换** —— 以下内容绝对不可动：
   - 文件名与路径：`deploy.htm` `unit.htm` `equipment.pgeqp` `pg.pgcam` `mscoree.dll` `.wav` `.mp3` `\log.txt`
   - 内部键名（驼峰无空格）：`ClassShort` `CloseDefName` `TargetType` `SoftAttack` `HardAttack`
   - 格式串占位符：`%s` `%d` `%u` `%%` `<br/>` `<img …>` `<table …>` 必须原样保留

### 9.4 实施步骤

```
① 备份 PGForever.exe（强制，另存 PGForever.exe.orig，且不得删除）
② 建立术语/条目表 work\exe\strings.json
     { offset, original, translation, ok_len, category }
③ 脚本按条目写入：长度校验 → UTF-16LE 编码 → 覆写 → 尾部补 0 到原长度
④ 重算 PE OptionalHeader.CheckSum（原值 0x000BC2B5；简单起见可置 0，Windows 对普通 EXE 不强校验）
⑤ 分小批(10~20 条)替换 → 启动 pg.bat 实测 → 通过再进下一批
```

### 9.5 残存风险

| 风险 | 等级 | 说明与对策 |
|---|---|---|
| 个别位置存在**长度硬编码依赖**（如 `sizeof(L"…")/2`） | 低 | 静态无法完全确证；靠"小批量替换 + 每次实测"兜底，出问题用备份回滚该批 |
| 极短英文缩写（如 `AT`=2 字符、`BB`）中文更长 | 低 | 正好符合既定口径——`AT` `FlaK` `BB` 本就保留原文，无需处理 |
| 误改内部键/文件名导致崩溃 | 中 | 白名单 + 分类审查 + 逐批实测三重控制 |
| 杀毒软件对修改过的 exe 误报 | 低 | 自用环境加白名单即可 |

### 9.6 工作量

约 **150–250 条**可见文案 —— 翻译 1 天 + 脚本与分批实测 1 天，**合计 1–2 天**。
相对整个工程是小头，但能补齐 htm 覆盖不到的动态战斗信息与单位属性标签，**性价比很高**。

> **建议执行顺序**：放在 UI 层（阶段 2）之后。因为 htm 是改文件、零风险、工作台账清晰，
> 先把能看见的静态界面做完，最后再动 exe 这块硬骨头。

---

## 十、风险登记册

| ID | 风险 | 等级 | 对策 |
|---|---|---|---|
| **R1** | `MAPNAMES.STR` 定长二进制，中文可能破结构 | **高** | POC P4 必测；失败则放弃 L6 |
| **R2** | 无语言隔离，改错无法一键回滚 | **高** | 备份 + Git 双保险；脚本一律先写副本再替换 |
| **R3** | exe 硬编码文本：虽可原地替换，但改 exe 风险高于改文本 | 中 | 见第九节；小分批 + 逐批实测 + exe 备份；放在最后阶段做 |
| **R4** | htmlayout 字体指定 Arial/Tahoma，中文可能糊 | 中 | POC P5；CSS 增加中文字体族 |
| **R5** | 固定像素布局（单位格 125×55px）溢出 | 中 | POC P6；必要时压缩译文 |
| **R6** | `pg.pgcam` 标签是内部键，误译导致路径匹配失败 | 中 | 只译展示文本，键名保持原样并做一致性校验 |
| **R7** | UTF-16LE 文件被普通编辑器另存为 UTF-8/ANSI 即损坏 | 中 | 脚本统一处理，禁止手工另存 |
| **R8** | 版权：同为 Luis Guzman freeware | — | 公开发布需书面许可，纯自用不受限 |

---

## 十一、决策记录

| # | 议题 | 你的决定 |
|---|---|---|
| 1 | 工作空间方案 | ✅ **方案 A** —— 本工作区下建独立子工程 `pgforever\` |
| 2 | 使用性质 | ✅ **纯自用**（版权不构成障碍，见 R8） |
| 3 | exe 硬编码是否汉化 | ✅ **要汉化** —— 经实测为 UTF-16LE 宽串，可原地替换（第九节） |
| 4 | 起步范围 | ✅ **先做 UI，再做 PG 单 game 完整文本** |
| 5 | 是否先跑 POC | ✅ 已跑 —— 中文渲染可行，编码定为 **UTF-8 with BOM** |

### 执行进度

| 层 | 状态 | 说明 |
|---|---|---|
| POC（中文渲染/编码） | ✅ 完成 | 报告：`pgforever\docs\01-POC报告.md` |
| L1 UI 层 | ✅ 完成 | 51 个 htm / 943 处；说明：`pgforever\docs\02-UI汉化说明.md` |
| L2–L5 PG 单 game 文本 | ⏳ 下一步 | equipment.pgeqp / *.pgscn / pg.pgcam / *.pgbrf |
| L6 MAPNAMES.STR | ⏳ 未验证 | 全项目唯一高风险项 |
| L7 exe 硬编码 | ⏳ 待做 | 方案已定（原地替换 UTF-16LE 宽串） |
| 图像烘焙标题 | ⏳ 待做 | `casualties.png` / `purchase_header.png` / `upgrade_header.png` 等 |

---

## 附：侦察期已确认的技术事实（供后续复用）

- `.pgeqp` / `.pgscn` / `.pgcam` 均为 **UTF-16LE + BOM(FF FE)**、TAB 分隔、以 `#` 开头为注释、空行分隔段（官方注释明示："It is a UNICODE tab-separated text file"、"Empty lines separate sections … DO NOT DELETE THEM!"）
- `.pgbrf` 为 UTF-8/ASCII 的 `<p>…</p>` HTML 片段
- 文件名规律：`%03d.pgscn`（场景）、`%04d.pgbrf`（简报）
- `equipment.pgeqp` 列头：`ID / Name / Class / Soft Attack / Hard Attack / Air Attack / Naval Attack / Ground Defense / Air Defense / Close Defense / Movement Type / Initiative / Range / Spotting / Targe…`
- exe 读取路径含 `Scenario\MAPNAMES.STR`、`DAT\MAPNAMES.STR`、`\equipment.pgeqp`、`\pg.pgcam`

### exe 二进制结构（`PGForever.exe`，用于硬编码汉化）

- PE32（`machine=014C`，`magic=010B`），**5 个节**，SizeOfImage 774,144，**无数字签名**
- 节表：`.text`(VA 1000) / **`.rdata`(VA 7F000, 文件偏移 0x7E200, RawSize 115200)** / `.data`(VA 9C000) / `.rsrc`(VA A8000) / `.reloc`(VA B1000)
- OptionalHeader.CheckSum = `0x000BC2B5`（改完需重算或置 0）
- UI 文案为 **UTF-16LE 宽串，集中于 `.rdata`**，紧凑排列，串间仅 `\x00\x00`，**无余量**
- 字符串沉淀池：去重 974 → 排除驼峰键名后 671 → 自然语言文案约 390 → 可见 UI 文案约 150–250 条
- 相邻串紧密相连，故**必须遵守"译文字符数 ≤ 原文字符数"**。典型条目示范：

```
0x82BF4  Close defense: %d<br/>      →  近距防御: %d<br/>
0x830C0  Air Defense Fire            →  防空火力
0x83300  Rugged defense chance: %d%%  →  顽强防御概率: %d%%
0x81D48  Last Turn                   →  最后一回合
0x80304  Tactical Bomber             →  战术轰炸机
```
