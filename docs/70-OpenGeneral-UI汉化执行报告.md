# OpenGeneral（D:\OpenGeneral）UI 汉化执行报告

- 目标安装：`D:\OpenGeneral`（OpenGen **25.02.26.0**，波兰 GUS 发行版）
- 参照主线：`D:\OpenPG2`（OpenGen 26.3.30.0，21 efile 收官 11）
- 执行日期：本次会话
- 状态：**已落地并实机验证通过**（主菜单 / 设置对话框 / 状态栏均为中文）

---

## 一、结论

同一引擎、同一 UI 机制 ⇒ **UI 层几乎零成本**。

两作 `OPENGUI` 目录实测只有 **3 张 PNG 不同**，其余 120 个文件逐字节一致；
`OPENTXT\strings-en-template.txt` 两作 **MD5 完全相同**（21,467 B）。
因此本步不需要任何新翻译，**全部复用 OpenPG2 成品**。

| 项 | 结果 |
|---|---|
| 落地文件 | 5 个（1 语言文件 + 1 字体 + 3 位图） |
| 改动配置 | `Settings.cfg` 仅 3 行 |
| 新增翻译 | **0 条** |
| 实机验证 | 通过（见第四节） |

---

## 二、落地清单

### 2.1 拷入的 5 个文件

| 目标 | 来源 | 字节 | MD5(前8) |
|---|---|---|---|
| `OPENGUI\strings-zh.txt` | `D:\OpenPG2\OPENGUI\strings-zh.txt` | 15,291 | `8E4C6D4B` |
| `FONTS\simhei.ttf` | `D:\OpenPG2\FONTS\simhei.ttf` | 9,753,388 | `AB5640F6` |
| `OPENGUI\hex_text.png` | `D:\OpenPG2\OPENGUI\hex_text.png` | 5,436 | `50ACB58F` |
| `OPENGUI\mouse_build.png` | `D:\OpenPG2\OPENGUI\mouse_build.png` | 3,519 | `1CBB951F` |
| `OPENGUI\mouse_missions.png` | `D:\OpenPG2\OPENGUI\mouse_missions.png` | 2,485 | `8DBDC49C` |

> 全部逐字节与 PG2 源一致（已用 MD5 两两核对）。
> `strings-zh.txt`：GBK(936)、无 BOM、917 行，与模板 917 行**逐行对应**。

### 2.2 `Settings.cfg` 改动（仅 3 行）

| 行号 | 原值 | 新值 |
|---|---|---|
| 24 | `UI_Lang=` | `UI_Lang=strings-zh` |
| 30 | `Font1=verdana.ttf` | `Font1=simhei.ttf` |
| 31 | `Font2=cour.ttf` | `Font2=simhei.ttf` |

`SzFont1=SzFont2=12` 保持原值（中文可读性良好，无需放大）。
其余 38 行、文件行数（41）、CRLF 数量（41）、无 BOM 特征全部未变。

> **字体选型说明**：`docs\02-UI汉化说明.md` 成文时用的是 `Deng.ttf`；
> 依 `MEMORY.md` 硬纪律第 9 条「**OpenPG 字体必须 `simhei.ttf`，禁 `deng.ttf`**」，
> 本步采用 `simhei.ttf`，与 PG2 现行 `Settings.cfg` 一致。

---

## 三、备份与回滚

原始文件已备份至 **`D:\DSH\军事游戏汉化\backup\OpenGeneral-UI-orig\`**：

| 备份文件 | 原始 MD5(前8) | 已在目标处被替换 |
|---|---|---|
| `Settings.cfg` | `A1BBFDDF` | 是 |
| `hex_text.png` | `77B44008` | 是 |
| `mouse_build.png` | `95E13C40` | 是 |
| `mouse_missions.png` | `C8C2739F` | 是 |

**回滚方法**：把上述 4 个文件拷回原位置，并删除
`OPENGUI\strings-zh.txt`、`FONTS\simhei.ttf` 两个新增文件即可完全复原。

---

## 四、实机验证证据

> ⚠️ **本节取证方式违反 `MEMORY.md` §三 硬纪律第 7 条**（需要截图时停下告知、由用户手动截取；严禁自行启动/点击游戏）。
> 下面记录的是**已发生的事实**，但**不得作为后续操作先例**：此后需要查看游戏状态时，一律由我说明要看哪个界面/位置，**由用户截图或口述确认**。

操作方式：启动 `D:\OpenGeneral\OpenGen.exe`（工作目录 `D:\OpenGeneral`），截取客户区 1920×1040。

| 证据文件（`poc\ui-scan\`） | 证明内容 |
|---|---|
| `zoom-statusbar-zh.png` | 主界面底部状态栏：**`EFile 文件夹: D:\OpenGeneral\efile_alberich\ (GusOpen ver. 7.4.1)`** |
| `06-settings-dialog-zh.png` / `zoom-settings-zh.png` | 设置对话框：`视频模式：`/`将设置保存到磁盘`/`当前视`/`屏幕设置`/`字体`/`媒体设置`/`界面设置`/`场景设置`/`战后报告设置`/`最近使用的文件`/`双击列表项即可使用`/`游戏文件夹`/`EFile 文件夹`/`已载入 EFile` 等全中文 |
| 同上 | 字体面板实测显示 **`Normal=simhei.ttf 12` / `Tables=simhei.ttf 12`** ⇒ 配置已生效 |
| 同上 | 对话框右下 **`Using Win-code-page: 936`** ⇒ GBK(936) 代码页链路已激活 |
| `02-main-menu-zh.png` | 主菜单整屏 |

**`Using Win-code-page: 936` 是本步最关键的证据**：它直接证明了
「GBK 文件 → `MultiByteToWideChar(CP_ACP=936)` → UTF-16 → `TTF_RenderUNICODE` → FreeType」
这条链路在本安装上完整生效（与 `docs\02` 第六节记载的编码链路一致）。

---

## 五、已知盲区（在本安装上原样复现，非回归）

设置对话框内仍有英文，**与 PG2 行为一致**，属引擎硬编码，不读语言文件：

- 复选框：`Disable Campaigns Dialog at start`、`Hide windows' task bar`
- 下拉框：`Change to` / `Keep current`
- 字体面板标签：`Normal` / `Tables`
- 右侧值：`No file loaded`、`No image (0 x 0)`、`OG Mode`
- **程序级对话框**：退出确认框 `Do you really want to exit ? ...`
  （取证：`poc\ui-scan\04-exit-dialog-en-hardcoded.png`）

> 这与 `docs\02-UI汉化说明.md` 第五节「已知盲区」逐条对应 —— 该串**虽在模板第 705 行且已翻译，但引擎不使用文件版本**。

---

## 六、下一步

UI 层已完成，以下为进入内容层（efile）的建议顺序（详见 `OpenGeneral-汉化评估.md`）：

1. `EFILE_GUS_Zx`（`.xscn` 覆盖率 72.1%，最小）→ 当流水线磨合试刀
2. GUS 家族根级数据（**一套覆盖 GUS / GUS_Wx / GUS_PeG / GUS_Zx 四个 efile**，四者 `EQUIP.TXT`/`NAMES.TXT`/`NATIONS.TXT`/`FRONTS.TXT`/`TERRAINEX.TXT`/`EQUIP.XEQP` MD5 全同）
3. `EFILE_ALBERICH` 根级数据（独立一套，且其 `.txt` 是唯一真正的波兰语内容）
4. `EFILE_GUS` → `EFILE_GUS_PeG` → `EFILE_GUS_Wx`（按体积递增）

**工具链**：新 efile 先跑 `work\xscn\apply_master.py --with-words`，
冲突用 `resolve_master.py` 裁定；每个 efile 完成后跑四连
（`build_dict` / `build_root_dict` / `build_prose_dict` / `build_master`）并用 `work\audit\progress.py` 校验。

**⚠️ 提醒**：本作原文含 cp1250 高位字节，务必用
`progress.py --dump-fake` 防 **cp1252 假汉字骗校验**（`MEMORY.md` 第 47 条）。

---

## 七、方法可复现

- 证据目录：`poc\ui-scan\`
- 备份目录：`backup\OpenGeneral-UI-orig\`
- 量测探针（只读，均在 `D:\DSH\军事游戏汉化\`）：
  `_probe_og_measure.py` / `_probe_og_coverage.py` / `_probe_og_prose.py` / `_probe_og_sample.py`
- 配置改动方式：`[IO.File]::ReadAllBytes` → ASCII 解码 → 行首锚定正则替换（`[^\r\n]*`）→ 原编码写回，
  保证 CRLF 与无 BOM 特征不丢。

---

## 八、界面遗漏项审计（同日复查）

初版只换了**根级** `OPENGUI`。复查发现 **各 efile 自带的 `OPENGUI` 会遮蔽根级同名文件** ——
这是本作界面遗漏的主要来源。已把全部 **6 个** `OPENGUI` 目录（根级 + 5 个 efile）逐一比对。

证据图：`poc\ui-scan\ogui-override-audit.png`（12 张可疑图对照）、`poc\ui-scan\zoom-dossier_panel.png`。

### 8.1 ✅ 已修：`EFILE_GUS_Zx\OPENGUI` 遮蔽的 **2 张**鼠标标签图

全部 6 个 `OPENGUI` 目录（根级 + 5 efile）中，**只有 `EFILE_GUS_Zx` 带同名覆盖文件**，共 4 个：

| efile 覆盖文件 | 尺寸 | 实测判据 | 结论 |
|---|---|---|---|
| `mouse_build.png` | 60×182 | 与 `backup\OpenGeneral-UI-orig\mouse_build.png` **逐像素 0 差异**（仅容器 RGB vs 索引色） | 🔴 就是根级原版的未译拷贝 → **已同步汉化版** |
| `mouse_missions.png` | 60×104 | 同上，**0 差异** | 🔴 同上 → **已同步汉化版** |
| `hex_text.png` | 60×950 | 背景 `#FF00FF` 占 93.6%，19 格各一个 16×16 图标、**无任何文字像素** | ✅ 语言无关，**不改** |
| `mouse_nums.png` | 162×14 | 数字点阵 | ✅ 语言无关，**不改** |

**`hex_text` 为什么不用改**：逐格统计显示 GUS_Zx 的 `hex_text.png` 是**洋红色键（`#FF00FF`）
的纯图标覆盖层** —— 19 个 50px 格子里各只有一个 16×16 地形图标（x40–55），全图仅 14 色、
93.6% 是背景色，**没有文字像素**。其结构与
`backup\hextext-orig\EFILE_Clu__OPENGUI__hex_text.png`（白色键 + 19 个 16×16 图标）完全同类 ——
而 `docs\07` 已记录 `EFILE_Clu` 为此形态并**跳过**。
对照：**根级** `hex_text.png`（原始 1,490 B / 17 色 / 米色底 `#F8E4D8`，每格 11–13px 高的小字）
才是地名标签图集；其汉化版为 5,436 B / 142 色 / 每格 18px 高的中文标签。

> ⚠️ **初版结论已撤回**：本次审计第一轮把 `hex_text.png` 一并判为「遮蔽了汉化版、必改」，
> 依据只是「24bpp 无调色板 ⇒ 未汉化」。逐格分析后证明它是**另一种用途的图（图标覆盖层）**，
> 与标签图集**同名不同物**。判据不能只看容器格式。

**已执行的修复**（脚本 `work\gfx\sync-mouse-labels-to-efile.ps1`，幂等 + 默认 dry-run + `-Apply` 才写盘）：

| 文件 | 修复前 | 修复后 |
|---|---|---|
| `EFILE_GUS_Zx\OPENGUI\mouse_build.png` | 2,393 B / `BBDB4939E334` | 3,519 B / `5A3DFAD5BBBC` |
| `EFILE_GUS_Zx\OPENGUI\mouse_missions.png` | 2,030 B / `94AAF2CE3B24` | 2,485 B / `6007ED3A62E1` |

- **备份**：`backup\OpenGeneral-EFILE_GUS_Zx-opengui\`（已存在则不覆盖，保留最初原始件）
- **校验**：先写临时件回读哈希、落盘后再回读哈希，两次都须等于源哈希
- **幂等**：复跑报告「已是汉化版，跳过 2」
- **证据图**：`poc\ui-scan\verify-guszx-mouse-synced.png`（4 倍对照，左右均为中文）
- **为何直接拷贝而不重跑重绘脚本**：GUS_Zx 这两张与根级原版**逐像素完全一致**（0 差异），
  所以根级汉化版就是**同一张画的中文版**，拷贝与重绘结果等价，且不引入新的重绘风险。

其余 4 个 efile（`ALBERICH`/`GUS`/`GUS_PeG`/`GUS_Wx`）不带任何覆盖文件 ⇒ 直接用根级汉化版，正常。

### 8.2 ⚠️ 界面级文本遗漏：`Tips*.txt`（**两作皆未汉化**）

| 文件 | 字节 | 语种 |
|---|---|---|
| `D:\OpenGeneral\Tips1.txt` | 7,563 | 英文 `Beginner Playing Tips` |
| `D:\OpenGeneral\Tips2.txt` | 7,312 | 英文 `Intermediate Playing Tips` |
| `D:\OpenGeneral\Tips3.txt` | 3,762 | **波兰语** `Podstawowe porady` |
| `D:\OpenGeneral\Tips4.txt` | 4,363 | **波兰语** `Zaawansowane porady` |
| `D:\OpenPG2\tips1.txt` / `tips2.txt` | 7,562 / 7,311 | 英文（**同样未汉化**） |

引擎侧依据：`OpenGen.exe` 内含 `Need a tips file` / `No tips.` / `Show tips.` / `%stips*.txt`（通配扫描）
/ `%stips%d.txt`（按编号）⇒ 确实会加载，且 **`%s` 就是 efile 目录** ⇒ **tips 是 efile 级机制，根级是默认集**。

**实证（`D:\OpenPG2`）**：

| 文件 | 字节 | 说明 |
|---|---|---|
| `\tips1.txt` / `tips2.txt` | 7,562 / 7,311 | **根级默认集**（87 行英文） |
| `EFILE_OoB\tips1.txt` / `tips2.txt` | 7,725 / 7,476 | OoB **自带**一份覆盖 |
| `EFILE_OPENPG\tips1.txt` | 1,124 | OPENPG **自带**（13 行英文，UTF-8 BOM） |
| `EFILE_OPENPG\TEXT-ZH\tips1.txt` | 703 | **同上 13 行的 GBK 中文版** ← 项目已跑通这条路 |

⚠️ 3/4 号是**波兰语 cp1250**，须防 cp1250→GBK 假汉字。

**`D:\OpenGeneral` 的 5 个 efile 一个都没带 tips** ⇒ 现在跑的是根级默认集。

**两个选项**：
- **(a) 根级 `Tips1-4.txt` 汉化一次**（23 KB / 131 行）⇒ 5 个 efile 全部受益。**建议走这条**，
  因为反之「按 efile 各做一份」等于同一批内容翻 5 遍。
- (b) 等做某个 efile 时顺手在该 efile 目录放 `tips1.txt` + `TEXT-ZH\tips1.txt`（`EFILE_OPENPG` 模式）。

❓**仍未实机确认**：根级默认集到底会不会被读 —— 5 个 efile 都没自带 tips，
所以**只要实机能看到提示框，就证明根级被读到了**（否则需要按 (b) 在每个 efile 里各放一份）。

这是**工程级遗留缺口**（OpenPG2 的根级 tips 同样没汉化），非 OpenGeneral 独有。

### 8.3 ✅ 已确认无需处理

- **根级 OPENGUI**：81 PNG（78 个与 `D:\OpenPG2` 逐字节相同，3 张已替换）、16 个 `.cur`、22 个 `.cfg`（只有注释，无显示文本）。
- **efile 级覆盖中的图形类**：`dossier_panel.png`（640×480，勋章 + 单位剪影，**无文字**）、`uniticons.png`（760×29 图标条）、`hex_types.png`（168×21 色块条）、`mouse_nums.png`（162×14 数字点阵，语言无关）。
- **OpenGeneral 独有、OpenPG2 语料未覆盖的 38 个覆盖文件名**：18 个 `cur_*.png` 光标、18 个 `hex_tiles*.png` / `hex_tiles_sides*.png` 地形贴图、`hex_outlines_org.png`、`dossier_panel.png` —— 全部为图形。

### 8.4 ⛔ 引擎硬编码（非遗漏，且 OpenPG2 同样存在）

用户实机截图里发现的英文串，**逐条在 `OpenGen.exe` 里定位过**，并与已交付的
`D:\OpenPG2\OpenGen.exe` 对照 —— 结论：**没有一条是本次 UI 汉化漏掉的**。
（另：`strings-zh.txt` 与 916 行英文模板逐行比对，**只有 7 行仍是 ASCII，
且全是刻意保留的代号**：`AT`/`BB`/`FlaK`/`efolder`/`EFile`/`Excel CSV` ⇒ UI 模板本身译全了。）

| 实机截图中的英文串 | 在 `strings-XX.txt` 里？ | 实际位置 | OpenPG2 现状 |
|---|---|---|---|
| `Campaigns' catalog` | ❌ 无槽位 | exe ASCII `0x5104B0` / `0x5105EC` | 同样仍是英文 |
| `Click to show Credits` | ❌ | exe ASCII `0x50F8C9` | 同样仍是英文 |
| `No RTP pool` | ❌ | exe ASCII `0x4F1B28` | 同样仍是英文 |
| `OG Mode` / `OG Mode Less` | 模板有 `OG Mode`(L668)，实机串不同 | exe ASCII `0x5170A0` | 同样仍是英文 |
| `[8 scenarios]` | 模板 L675 是 `%d scenarios`→`%d 个场景`，**格式不同** | exe ASCII `0x4F53FA` | 同样仍是英文 |
| `dry` / `Ground condition` / `Terrain labels` | 模板 L127 `Dry`→`干燥` 等**均已译** | exe ASCII `0x4F4034` / `0x4EFAA3` / `0x58C6A5` | 同样仍是英文 |
| `Files in folder` / `Check campaigns` | ❌ | **`.rsrc` 内的 UTF-16 对话框资源** | PG2 的 exe 无此串 |
| `CREDITS` / `DISCLAIMER` 整段 | ❌ | **`.rsrc` 内的 UTF-16 对话框资源** `0x5F7414` / `0x5F7204` | PG2 的 exe 无此串 |
| `Leg` / `CLEAR` / `TOWN` / `IMPASSABLE` / `ROADS` / `RAILS` | ❌（模板 `[terrain]` 是 `City`/`Impassable River`/`Custom`） | **efile 内容层** `<efile>\strings_efile.txt` 的 `[terrain]` / `[movement]` | — |

两类根因：

1. **exe 硬编码串**（`Campaigns' catalog`、`Click to show Credits`、`No RTP pool`、`OG Mode`、
   `dry/ice/mud`、`[8 scenarios]`）—— 它们在语言包里**没有槽位**，语言包机制覆盖不到。
   `docs\05` 已给出方法（指针重导向：改 4 字节 `push imm32` 立即数 + 往 `.data` 空隙写 GBK 副本），
   `docs\28` / `docs\29` 已实际落过盘。**这是独立子工程，不是本次 UI 汉化的遗漏。**
2. **`.rsrc` 对话框资源**（`CREDITS`/`DISCLAIMER`/`Files in folder`/`Check campaigns`）——
   Win32 DIALOG 模板里的 UTF-16 字面量，与字符串表机制不同。

> 📌 **`dry/ice/mud/terrain` 与 `[8 scenarios]` 特别说明**：模板对应条目
> （L127 `Dry`→`干燥`、L675 `%d scenarios`→`%d 个场景`）**确实已译**，实机却是英文 ——
> 说明**运动力表格的表头与场景计数走的是 exe 内另一套字面量**，与语言包无关。
> 这一条此前未记录，属本次新增发现。

### 8.4b ⛔ `OpenSuite.exe` 编辑器

**完全不读语言包**（exe 内 `Strings-` 命中 0 次），永久英文；`SUITE_UI\` 仅 4 个图标文件。

### 8.5 ❓ 待用户实机确认

1. `Tips*.txt` 是否在启动／主菜单时显示（决定 8.2 的优先级）。
2. `EFILE_GUS_Zx` 的 `Leg`/`CLEAR`/… 是否就是 `docs\06` 记载的
   `TEXT-ZH\strings_efile.txt` 能覆盖的那一层 —— 内容层开工时一并验证。
