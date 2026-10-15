# 32 · `EFILE_AO` 全层实测盘点（B1 开工基线）

> 2026-09-28 实测。**全部数字直读 `D:\OpenPG2\EFILE_AO` 文件**，不看映射表、不采信文档自述。
> 承接 `docs\30` §三 P2（B1 = AO 试点）。本轮**只盘点，不改动任何文件**；
> 唯一写盘动作为 `backup\ORIGINAL-EFILE_AO\`（新建只读备份，原文侧一字节未动）。
> 判据：汉字 = GB2312 字节范围（`0xB0A1–0xF7FE`）；原文侧按 cp1252 解码。

---

## 一、结论速览

| 层 | 规模（实测） | 状态 | 本批工作量 |
|---|---|---|---|
| 根级 `equip.txt` | 797 行 / **665 唯一** | ✅ **已译**（§5.5） | 2641 汉字对；reuse 77 / policy 144 / zh 377 / keepmodel 198 |
| 根级 `names.txt` | 993 行 / **401 唯一** | ✅ **已译**（§5.5） | 实名 372 全音译（reuse 53 + 新增 319）；`???`/`Ant #`/`#color`/`Classified` 保留 |
| 根级 `nations.txt` | 43 行 / **19 唯一** | ✅ **已译**（§5.5） | 18 实体译（`阵营 A/B`+`所有国家`+16 国名）；后 16 行 `???` 保留 |
| 根级 `strings_efile.txt` | 55 行 / **48 唯一** | ✅ **已译**（§5.5） | 46 条译（含 `[classes]`/`[requisition]` 全表）；标题块与 LF 结构原样保留 |
| `.xscn` 串区 | **38 文件 / 188 条** | ✅ **已译**（§5.5） | 188/188 含汉字，结构偏差 0 |
| 场景 `.txt` | **118 个 / 64,346 B** | ✅ **已译**（§5.5） | 118 文件落 `TEXT-ZH\SCENARIO`；93 唯一内容全译 |
| `.ply` 简报 | 28 个 = 3 空壳 + 9 占位 + **16 有正文** | ✅ **16/16 已译** | **0（本批已完）** |
| **`.tmsg` 任务消息** ⭐ | **12 个 / 5,245 B**（54 非空行） | ✅ **12/12 已译**（§5.4） | **本批新增** |
| **`.xsch` 分支选择屏** ⭐ | **2 个 / 1,124 B**（26 条串） | ✅ **2/2 已译**（§5.4） | **本批新增** |
| `.xcam` 战役文件 | 4 个 × 63,747 B | — | **无文本**（纯 `.TXT` 文件名引用表） |
| `.front` | 10 个 × 160 B | — | **无文本**（1 个非空白字节） |
| `.cfg` | 3 个 | — | **无文本**（选项注释，非玩家可见） |
| 位图 | 无自有 `hex_text.png` | — | 走根 `OPENGUI\`（已汉化）⇒ **0** |
| `efile.xml` | 512 B | ⬜ | 标题/描述（**未批准**，P3） |

**⇒ AO 本批实际待译（唯一串）**：`equip` ~271 + `names` 399 + `nations` 17 + `strings_efile` ? + `.xscn` 144 ≈ **831 条** ＋ **93 个散文文件**
（`.tmsg` 54 行 + `.xsch` 26 条 **已于 §5.4 完成**）。
**⇒ AO 已完成层**：`.ply` 16/16 ✅ · `.tmsg` 12/12 ✅ · `.xsch` 2/2 ✅ · **根级四件套 ✅ · `.xscn` 188/188 ✅ · 场景 `.txt` 118/118 ✅**（后三项见 §5.5）。

**⇒ 剩余层**：仅 `efile.xml`（P3，未批准）。**AO 全部可译层已收官。**

---

## 二、根级四件套（实测）

| 文件 | bytes | 总行 | 非空 | 非注释 | 唯一 | 汉字对 |
|---|---:|---:|---:|---:|---:|---:|
| `equip.txt` | 10,276 | 797 | 796 | 796 | **665** | 0 |
| `names.txt` | 6,949 | 993 | 992 | 992 | **401** | 0 |
| `nations.txt` | 645 | 43 | 41 | 34 | **19** | 0 |
| `strings_efile.txt` | 1,065 | 57 | 54 | 48 | **48** | 0 |

### 2.1 `equip.txt`：665 唯一，按"型号保留"口径拆解

| 类别 | 条数 | 处置 |
|---|---:|---|
| 含数字（型号疑似保留） | 394 | 型号保留原文（`M4A4 Sherman` `T-62A` `Bf-109` 类） |
| 纯字母词（需译） | **271** | 兵种/编制/舰级 ⇒ 译中文 |

**纯字母词的四类**（全部 271 条已导出，见 `work\ao\ao-equip-letters.txt`）：
1. **舰级名**：`Alaska Class` `Iowa Class` `Yamato Class` `Essex Class` … ≈ 60 条 ⇒ 口径 `衣阿华级`（著名舰级用通行译名）
2. **兵种/编制**：`Infantry` `Sappers` `Paratrooper` `Cavalry` `Ranger` `Militia` … ⇒ 译中文
3. **外语言兵种**：`Hohei`(日本步兵) `Piechota`(波兰步兵) `Strelkoviy`(苏联步兵) `Gebirgsjäger` `Fallschirmjäger` `Panzergrenadiere` ⇒ 按 §五 译中文
4. **科幻/架空单位**：`Fire Ant` `Queen Ant` `Drone Tank` `Behemoth` `Lunar Fortress` `Time Machine` ⇒ 需创译

⚠️ **含非 ASCII 的 5 条**（`Fallschirmjäger` `Gebirgsjäger` `Heckenschütze` `Kübelwagen RCL` …）⇒ GBK 装不下变音符，按 `MECHANICS.md` 口径**折写或译中文**。

### 2.2 `names.txt`：401 唯一，**实体仅 399**

| 类别 | 条数 | 处置 |
|---|---:|---|
| 占位 `???` | 527 行 | 保留（引擎占位） |
| 占位 `Classified` | 31 行 | 保留 |
| **实体：色值 `#rrggbb`** | **31** | **保留**（数据，非文本） |
| **实体：蚂蚁编号 `Ant #NNNN`** | **31** | **保留**（编号） |
| **实体：人名** | **337** | **译中文** |

**337 个人名的构成**：美/英/德/苏/日/波多语言姓氏（`Bradley` `Bayerlein` `Kuznetsov` `Yamamoto` `Kowalski` …）。
⇒ 按口径**用通行译名**，非知名者音译。
**5 条含变音符需折写**：`Bäcker` `Jäger` `Müller` `Spanknöbel` `Wójcik`。

### 2.3 `nations.txt`：19 唯一，**实体仅 17**

```
Faction A / Faction B / All Nations / United States / Soviet Union / Giant Ants /
Nazi Germany / Pegasus / Confederate States / Cult of the New Dawn / Unknown Force /
Japanese Empire / Poland / German-American Union / Socialist States / Ashes / Arm /
Phoenix Guard        （+ 后 16 行 ???）
```
⇒ 17 条实体全部需译（含架空势力 `Giant Ants`=巨蚁、`Cult of the New Dawn`=新黎明教团 等）。

### 2.4 `strings_efile.txt`：48 条 ⚠️ **必须覆盖（答复见 §四之二）**

结构与既有 efile **不同** —— 它只有一个 `[classes]`（24 条）+ `[requisition]`（24 条）：

| 段 | 内容 | 与 `strings-zh.txt` 的关系 |
|---|---|---|
| `[classes]` 24 条 | `None/Infantry/Tank/Recon/…/Light Cruiser` | **与 `strings-zh.txt` 行 47–71 逐条一一对应**（`无`行48 / `步兵`行49 / `坦克`行50 …）|
| `[requisition]` 24 条 | `Switch Ground+Air…` `Select Tank` `Name Unit` `Reassign Unit` `Exit` | **不在 `strings-zh.txt`** ⇒ `strings_efile.txt` 是**唯一落点** |

⚠️ 根级 `strings_efile.txt` 只读**前 96 字符/行**（文件头注释明写）⇒ 译文长度须受限。

---

## 四之二、⭐ 「用引擎默认」是否等于完整汉化？—— **否**

> 用户问：`[classes]` 段若依赖引擎默认，汉化还完整吗？**实测答案：不完整，必须覆盖。**

### 4-2.1 证据链（exe 内置表实测）

按 `strings-zh.txt` 第 17–19 行原文自述：

> *These sections **can be redefined at efile level by using STRINGS_EFILE.txt** in efile folder,
> but **you cannot remove from this file***

⇒ 引擎逻辑是 **两段式**：exe 内置英文表（fallback）+ efile 级 `strings_efile.txt`（覆盖层）。

**exe 内置表实测**（`.data` FO `0x5842A0` 起，0x100 步长，段界清晰）：

| 区段 | FO 起 | 内容 | 是否已汉化 |
|---|---|---|---|
| `[terrain]` 21 条 | `0x5842A0` | `开阔地` `城镇` … `浅海` | ✅ **已是中文**（历史已 patch）|
| `[sides]` 2 条 | `0x5857A0` | **`Axis` / `Allied`** | ❌ **仍是英文** |
| `[classes]` 24 条 | `0x5859A0` | **`None` / `Infantry` / `Tank` … `Light Cruiser`** | ❌ **仍是英文** |

### 4-2.2 结论

| 若 AO 不提供 `[classes]` 覆盖 | 结果 |
|---|---|
| `[terrain]` | 显示中文（exe 内置已是中文，`strings-zh.txt` 亦有）|
| `[sides]` | **显示英文 `Axis` / `Allied`** |
| `[classes]` | **显示英文 `None` / `Infantry` / `Tank` / `Destroyer` …（24 条全英文）** |

⇒ **「用引擎默认」= 单位类别菜单 24 条 + 阵营 2 条保持英文 ⇒ 汉化不完整。**
⇒ **`TEXT-ZH\strings_efile.txt` 必须写**：`[classes]` 沿用 `strings-zh.txt` 行 47–71 既有译文（零新译，仅同步），
`[requisition]` 24 条复用 OLGWW2 成熟译法（`docs\32` §2.4）。

> 附注：AO 的 `strings_efile.txt` **只含** `[classes]` + `[requisition]` 两段（无 `[sides]`）⇒
> 阵营名走 `strings-zh.txt` 行 44–45（已中文）或 `nations.txt`，**本批不动**。

### 4-2.3 待办（已并入本批）

1. `[classes]`：从 `strings-zh.txt` 行 47–71 抄 24 行中文 ⇒ `TEXT-ZH\strings_efile.txt`。
2. `[requisition]`：从 OLGWW2 `TEXT-ZH\strings_efile.txt` 行 38–60 抄 24 行（**需核 AO 的 24 条是否逐条同名**）。
3. ⚠️ 保留 AO 原文的 `*` 注释头与行序（引擎按行索引读）。

---

## 三、`.xscn` 串区（38 文件 / 188 条）

`work\xscn\xscn.py --efile AO verify` 实测：

| 指标 | 值 |
|---|---|
| 文件数 | 38 |
| 条目数 | **188**（备份 188 / 现状 188，**一致**）|
| 结构偏差文件 | **0** |
| 尾部残留分布 | `[(0, 38)]` ⇒ 38 文件全部 0 残留 ✅ |
| 现状含汉字 | **0** |

**条目的类型**（抽样）：

| 类型 | 样例 |
|---|---|
| 场景标题（g-1） | `[标题] Squash You Like A Bug` `Appropriation` `Not You Again` `Dying Embers` |
| 地名（g0） | `Holloman AFB` `Los Angeles` `Sverdlovsk` `Small Town` `Time Machine` `Storage Facility` |

**⚠️ 注**：`.xscn` 首次为 AO 建立原文备份 `backup\ORIGINAL-EFILE_AO\SCENARIO\`（38 `.xscn` + 2 `.xsch` + 4 `.xcam`），先前缺失。

---

## 四、场景 `.txt`（118 个 / 64,346 B）

| 指标 | 值 |
|---|---|
| 文件数 | 118 |
| 唯一内容（md5） | **93** |
| 重复组 | 3 组（覆盖 **28** 文件）⇒ 省 25 份 |
| 总字节 | 64,346 |

**按前缀分布**：`aocamp*` 63 · `embers*` 22 · `placeholder*` 3 · 其余 30 个单文件（`ant*` `ao*` `nazi*`）。

**内容类型**：场景简报/胜利文本/战役简介（`ant0i.txt` 为**巨蚁视角第一人称全大写** `<WE HAVE GROWN STRONGER.>`）。
⇒ 走 `TEXT-ZH\SCENARIO\`（原文侧不动），复用 `work\ag-scenario\deploy.py`（按 md5 铺到组内每个文件名）。

---

## 五、⭐ 两个全库盲区（本轮新发现）

> **这是本轮最重要的发现**：两个层的 `TEXT-ZH` 副本**与原文逐字节相同**，从未真译。

### 5.1 `.tmsg`（任务消息）—— 纯文本，极易漏

**格式**：`\r\n` × N（屏幕定位）+ 正文 + `\r\n` × N（清屏）。**纯 ASCII，无二进制头**。

| 项 | 值 |
|---|---|
| AO 规模 | **12 个 / 5,245 B**（54 非空行） |
| 最长 | `ao16.tmsg` 2,280 B（16 非空行） |
| 全库规模 | **547 个 / 126,025 B** |

**全库真译率 = 0**（唯一有 `TEXT-ZH` 的是 OLGWW2 5 个，实测**逐字节等于原文**，汉字对 **0**）。
⇒ **547 个 .tmsg 全部未译**，且**先前未被任何进度统计计入**。

### 5.2 `.xsch`（分支选择屏）—— 有二进制头

**格式**：`\x01\x00\x02\x00` + 名 + 定长槽 + 文本串（每串后有长度字节）。
文本为**全大写军事电报风**。

| 项 | 值 |
|---|---|
| AO 规模 | **2 个 / 1,124 B**（26 条串） |
| 全库规模 | **52 个 / 27,094 B** |

**全库真译率 = 0**（OPENPG 4 个有 `TEXT-ZH`，实测逐字节等于原文；此前的"han=1"是 **cp1252 假汉字**误判 —— `\xd4\xfe`=`Ôþ` 被 GBK 解成汉字）。

**AO 的 26 条串**（`aochoice01/02`）：`Dispatch A.O. to Thule, Greenland` / `PRIORITY I DISPATCH` / `DEVICE UNCOVERED NEAR THULE` / `NAZI FORCES BASED ON MOON` / `SPECIAL LUNAR UNIT ON STANDBY` …

### 5.3 影响面

| 层 | 全库 | 已真译 | 说明 |
|---|---:|---:|---|
| `.tmsg` | **552** | **0 → AO 12** | 15 个 efile 有；LXF 227 个最多 |
| `.xsch` | **52** | **0 → AO 2** | 8 个 efile 有；LXF 15 / KAISER 13 最多 |

⚠️ **须回填 `docs\30` §二 工作量表**（原表只统计 `.xscn` / `.txt` / `.ply`，**漏了这两层**）。

---

## 5.4 ✅ 本轮已完成：两层的结构逆向 + AO 落地（09-28）

> 用户答复「**②一并做 ③`.xsch` 逆向放行**」⇒ 本轮**同时交付结构逆向与 AO 全部译文**。

### `.xsch` 结构（全库 **52 文件 / 115 记录 / 0 异常 / 52-52 无损往返**）

```
24B 文件头:  u16 ver=1 | u16 count | char[20] name
记录 ×count 顺序紧排:
    12B 头:  [0]u8 [1]u8 00 00 [4]u16 [6]u16 [8]u32  ← 全是版面/音轨参数，原样保留
    [槽A]:   定长 104 B（全库实测一致），左对齐 + \0 填充；槽内可含多个 \0 分隔短串
    u16:     tail = 槽A 之后的正文字节数
    [槽B]:   tail 字节正文（\r\n 分行）
```
**踩坑 3 连（记录以免再犯）**：
1. **byte[0] 不是 tag** —— OPENPG `choice*.xsch` 的 rec0 = `0x00`（其余 0x01）。
2. **byte[8..12] 是 u32，不是魔数** —— 实测 `6 / 7 / 4000`；按「`[8]==6`」判头会漏判。
3. **槽宽恒 104 ⇒ 不许扫描** —— 早先写的「遍历候选位置自洽求解 tail」**会误判**，删掉；直接 `+12+104` 取 tail 即全对。

工具：`work\xsch\xsch.py`（`verify | verifyall | export | apply`）。

### `.tmsg` 结构（全库 **552 文件 / 538 有正文 / 552-552 切分自洽**）

```
纯文本 = 「行首 N 个 \r\n」 + 「正文」 + 「行尾 M 个 \r\n」
```
- **无二进制头**；首尾连续 `\r\n` 是**屏幕定位/清屏指令**，N/M 逐文件不同（实测 0–24），**必须逐字节保留**。
- **只在 `<efile>\SCENARIO\`，无 `TEXT-ZH\` 覆盖层 ⇒ efile 原地改**（同 `.xscn`）。

工具：`work\tmsg\tmsg.py`。

### AO 落地结果（14 文件）

| 层 | 文件 | 处数 | 结果 |
|---|---|---:|---|
| `.xsch` | `aochoice01` / `aochoice02` | 8（4 槽A + 4 槽B） | ✅ 槽A GBK 14–20 B / 104 B |
| `.tmsg` | `ao1,3,6,10,11,11r,12,14,16,17,18,embers7` | 12 正文 | ✅ 首尾 CRLF 原样 |

- 备份：`backup\ORIGINAL-EFILE_AO\*.{tmsg,xsch}`（本轮新增）。
- 校验：结构复核 **0 异常**；首尾段纯度（仅 `\r\n`）**全通过**；`.xsch` 槽A ≤104 **全通过**。
- 换算口径：中文 GBK 2B/字 vs 英文 1B/字 + 空格 ⇒ `.tmsg` 文件**普遍变小**（`ao16` 2,280→1,418 B）是**正常且安全**的（无槽宽约束）。

---

## 5.5 ✅ 本轮已完成：剩余层全部落地（09-28 第二批）

> 承接 §八 固定序 ①→⑧，**全部完成**。全部写盘动作均已核对（行数/Gbk/非零字节）。

| 序 | 层 | 产物 | 实测 |
|---|---|---|---|
| ① | 根级 `equip.txt` | `TEXT-ZH\equip.txt` | 797 行（原 797）；10,276→9,626 B；**2641 汉字对**；口径 reuse 77 / policy 144 / zh 377 / keepmodel 198 |
| ② | 根级 `names.txt` | `TEXT-ZH\names.txt` | 993 行（原 993）；6,949→6,758 B；实名 **372 全音译**（跨 efile 复用 53 + 新增 319）；`???`527 / `Ant #`31 / `#color`31 / `Classified`31 / 空行 1 全保留 |
| ③ | 根级 `nations.txt` | `TEXT-ZH\nations.txt` | 43 行（原 43）；18 实体译；`???`×16 保留 |
| ④ | 根级 `strings_efile.txt` | `TEXT-ZH\strings_efile.txt` | 55 行（原 55）；46 条译；⚠️ L56 头部块的**裸 `\n` 结构逐字节保留**（原 LF 56 / CRLF 54 ＝ 译后同） |
| ⑤ | `.xscn` 串区 | 就地改写 38 文件 | `verify`：**188/188 含汉字**，尾部残留 0，结构偏差 0（`apply --map work\ao\ao-xscn.tsv`，178 唯一词） |
| ⑥ | `.tmsg` | （§5.4 已完成） | 12/12 |
| ⑦ | `.xsch` | （§5.4 已完成） | 2/2 |
| ⑧ | 场景 `.txt` | `TEXT-ZH\SCENARIO\*.txt` ×118 | 93 唯一内容全译；分组内每个文件名写同一译文 |

**关键判断记录**：
- **`equip.txt` 口径**：交叉核对既有 4 efile 的 line-aligned 中英对（OLGWW2 1450 / OPENPG 331 / AG 733）建 `_equip-crossmap.json`（1165 键，0 恒等映射）⇒ **装备型号保留原文**（与 `M46 Patton`/`P-51D Mustang` 在既有 efile 里未译一致），只译兵种/编制/舰级。
- **`names.txt` 口径**：既有 efile 实名**音译中文**（AG 56% / OPENPG 96% / NASHORNPBEM 100% 含汉字）⇒ AO 372 实名全音译。`Ant #NNNN`（巨蚁单位编号）/`#hexcolor`/`???`/`Classified` 保留。
- **场景 `.txt` 两类**：`aoN.txt`（1–9）是**标签文件**（首行＝场景标题，其后是番号缩写 + 地名）——**番号缩写（`1/S` `2/12` `114/6`）保留**，地名译；`aocamp*`/`ant*`/`nazi*`/`embersao*` 是散文（简报/胜利/战役引言），全译。
- **`.ply` 12 个未处理**＝3 全 NUL 空壳 + 9 `Intro for XXX` 占位（无正文），按「该缺就缺」保留；16 个有正文的已于前批全译。
- **非文本根级**：`colors.txt`/`fronts.txt`/`weather.txt`/`TerrainEx.txt` 为纯配置（数字 + 英文注释），**无玩家可见文本**，不译。

**产物备份**：`backup\ORIGINAL-EFILE_AO\` 已含本批 4 个根级原文（`equip`/`names`/`nations`/`strings_efile`）。

---

## 六、非文本层（排除项，登记以免误算）

| 层 | 规模 | 判定 |
|---|---|---|
| `.xcam` | 4 × 63,747 B | **纯 `.TXT` 文件名引用表**（`AOCamp00i.TXT` …），无标题文本 |
| `.front` | 10 × 160 B | **1 个非空白字节**，无文本 |
| `.cfg` | 3 × 3,918 B | 全局选项注释（`pg2mode=0` `green=1` …），非玩家可见 |
| `.jpg` / `.png`（场景图） | 24 + ? | 图像 |
| 位图 | AO 无自有 `hex_text.png` | 走根 `OPENGUI\`（**已汉化**，8 份已重绘） |

---

## 七、与既有记录的对账

| 项 | 旧记（`docs\30`） | 本轮实测 | 结论 |
|---|---|---|---|
| `equip` 唯一 | 665 | **665** | ✅ |
| `names` 唯一 | 401 | **401** | ✅ |
| `nations` 唯一 | 19 | **19** | ✅ |
| `strings_efile` | 48 | **48** | ✅ |
| `.xscn` 唯一 | 144 | 188 条（唯一待 `export` 复算） | △ 条数一致 |
| `.txt` 个 / KB | 118 / 63 | **118 / 64,346 B** | ✅ |
| `.ply` 有正文 | 19 ⚠️ | **16**（3 全 NUL + 9 占位） | ❌ **旧记 19 偏高**（把 3 个全 NUL 空壳算作有正文）；本轮订正为 **16**，且 **16/16 已译** |
| `.tmsg` | **未统计** | **12 个 / 5,245 B** | ⭐ 新增，全库实为 **552** |
| `.xsch` | **未统计** | **2 个 / 1,124 B** | ⭐ 新增 |

> ✅ **`.ply` 订正**：`docs\30` §二 表 AO 行记 `19`，实测 **16**（三分类：3 全 NUL 空壳 + 9 `Intro for XXX` 占位 + 16 有正文）。**16 个有正文的全部已汉化**（`TEXT-ZH\SCENARIO\` 逐字节含汉字，样例 `ÐÂÄ«Î÷¸çÖÝ»ôÂåÂü¿Õ¾ü»ùµØ`＝新墨西哥州霍洛曼空军基地）。

---

## 八、本批建议顺序（`docs\30` §三 P2 批内固定序）

```
① 根级 equip.txt（271 条，主体）
② 根级 names.txt（399 实体）
③ 根级 nations.txt（17 条）
④ 根级 strings_efile.txt（先判 [classes] 可否沿用 strings-zh；[requisition] 24 条复用 OLGWW2 译法）
        ↓
⑤ .xscn 串区（144 唯一，独立解析器回写）
        ↓
⑥ .tmsg（12 个 / 54 行）⭐ 新增层
⑦ .xsch（2 个 / 26 条）⭐ 新增层（需先逆向定长槽）
⑧ 场景 .txt（93 唯一内容 / 118 文件）
        ↓
⑨ 位图：无自有 ⇒ 0
```

**每批三项校验**（`docs\30` §三 P2）：① GBK/无 BOM/CRLF + 逐行对齐；② `.xscn` 独立解析器（异常 0）；③ `.xscn` ↔ `.txt` 硬桥零新增。

---

## 九、开工前待决（3 条）

1. **`strings_efile.txt` 的 `[classes]` 段**：与引擎默认表（`strings-zh.txt` 行 47–71）逐条相同 ⇒ **是否需要在 `TEXT-ZH\` 里重写一遍**？
   （重写 = 与既有 4 efile 一致；不写 = 依赖引擎默认，更简洁但口径不统一）
2. ✅ **已决（用户「一并做」）：本轮即纳入 AO**，`.tmsg` 12 + `.xsch` 2 已全部汉化落盘（§5.4）。
   （建议：AO 规模小，**本轮一并做**，正好把管线的两个新落点验通）
3. ✅ **已决（用户「需要的」）：逆向完成** —— 定长 104B 槽 + u16 tail + 变长槽B；全库 52 文件 0 异常（§5.4）。

---

## 十、本轮产物

| 文件 | 说明 |
|---|---|
| `backup\ORIGINAL-EFILE_AO\` | **新建**：38 `.xscn` + 2 `.xsch` + 4 `.xcam` + 8 根级 `.txt` + `efile.xml`（**只读拷贝，原文未动**）|
| `docs\32-EFILE_AO全层盘点.md` | 本文件 |
| `work\ao\ao-equip-letters.txt` | 271 条纯字母装备词（待译清单）|
| `work\ao\ao-names-persons.txt` | 337 条人名（待译清单）|
| `work\ao\ao-scenario-reps.tsv` | 93 个散文唯一内容代表 |

*数据真源：`D:\OpenPG2\EFILE_AO` 2026-09-28 实测。*
