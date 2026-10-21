# D:\OpenGeneral 汉化工作量评估报告（v2 修正版）

> **v1 作废原因**：v1（2026 版，264 行）是在**不知道本工作区已存在 OpenPG2 汉化工程**的前提下写的，
> 把若干**已经解决的问题**（中文编码可行性、exe 硬编码 UI）当成了未知风险，因而严重高估。
> 用户 m00208 指出：「这个和 openpg2 是同引擎，我们不是有汉化的 openpg2 么？」
> v2 以工作区既有事实（`MEMORY.md` / `docs\` / `glossary\` / `work\xscn\`）为准重写。

---

## 〇 一句话结论

**这是同一个引擎，而且我们已经有跑通的 OpenPG2 汉化工程。**
`D:\OpenGeneral` 不是「从零汉化一款游戏」，而是**「给既有流水线加 5 个新 efile」**。

| | 结论 |
|---|---|
| UI 界面层 | **≈0 工作量**。两作 `OPENGUI` 的 123 个文件**只有 3 张 PNG 不同**；`strings-en-template.txt` **逐字节相同** |
| 内容层 | 5 个 efile **全部不在** OpenPG2 的 21 个里 → 必须新做，但走既有 `apply_master.py` 流水线 |
| 体量 | 约为 OpenPG2 全库的 **35–50%** |
| 估算 | **31–58 人·天（单人 + LLM ≈ 6–12 周）**；v1 的「6–12 个月」作废 |

---

## 一 修正：可直接复用的（v1 全部误判为「未知/高风险」）

### 1.1 引擎与被汉化主线是**同一套**

| 项 | `D:\OpenPG2`（已汉化主线） | `D:\OpenGeneral`（本次目标） |
|---|---|---|
| 引擎 | OpenGen **26.3.30.0**（SDL2 + SDL2_ttf） | OpenGen **25.02.26.0**（SDL2 + SDL2_ttf） |
| efile 数 | 21（收官 11） | 5（全部未做） |
| UI 语言文件 | `OPENGUI\strings-zh.txt` 已有 | 缺 |

### 1.2 UI 层：**逐字节级同构，几乎零成本**

实测对比 `D:\OpenGeneral\OPENGUI` 与 `D:\OpenPG2\OPENGUI` 的 123 个文件：

- **PG2 仅多出 2 个文件**：`strings-zh.txt`（15,291 B）、`strings-zh.txt.bak`（21,182 B）。
- **OpenGeneral 没有任何 PG2 缺失的文件。**
- **同名文件里只有 3 张 PNG 字节数不同** —— 即需要中文重绘的全部位图：

| 位图 | OpenGeneral（原始） | OpenPG2（已汉化） |
|---|---|---|
| `hex_text.png` | 1,490 B | 5,436 B |
| `mouse_build.png` | 1,565 B | 3,519 B |
| `mouse_missions.png` | 1,494 B | 2,485 B |

> 其余 120 个文件（含 `hex_tiledecors0..21.png` 共 22 张大底图）**完全一致**，
> 且底层美术同源 ⇒ 这 3 张**直接拷 PG2 的已汉化版本**即可，无需重画。
> 位图汉化方法论见 `docs\09-位图文字全库排查与鼠标标签汉化.md`（定点改图 + 验证图流程已跑通）。

**另一关键相等**：`OPENTXT\strings-en-template.txt`（21,467 B）两作 **md5 前缀均为 `8723544D21`，逐字节相同**。
⇒ `strings-zh.txt` 的键集与本作 exe 25.02.26.0 完全匹配，**可直接拷用**。

**UI 层落地三步（≈半天）**：
1. 拷 `D:\OpenPG2\OPENGUI\strings-zh.txt` → `D:\OpenGeneral\OPENGUI\`；
2. 拷 `D:\OpenPG2\FONTS\simhei.ttf`（9.75 MB）→ `D:\OpenGeneral\FONTS\`（本作 FONTS 只有 cour/micross/Tahoma/Verdana/wine-tahoma，**无 CJK 字体**）；
3. 改 `Settings.cfg`：`UI_Lang=strings-zh`、`Font1=simhei.ttf`；
   并拷那 3 张已汉化 PNG。

> 硬纪律（`MEMORY.md` 第 9 条）：**字体必须 `simhei.ttf`，禁用 `deng.ttf`；`UI_Lang` 必须 `strings-zh`。**
> ⇒ v1 §四「引擎是否支持中文是最大风险」**已被本工作区的既成事实推翻**
> （GBK 出稿 + `simhei.ttf` + `strings-zh` 方案在 OpenPG2 上已实机跑通）。

### 1.3 词库 / 工具 / 技能：全部在位

| 资产 | 说明 |
|---|---|
| `glossary\standard-glossary.tsv` | 译名真源 23,200 条 |
| `work\xscn\master-glossary.tsv` | ⭐ 四层统一总词库 **124,270 条** |
| `work\xscn\master-words.tsv` | 词级组合 1,849 条；另有 `master-resolve.tsv` / `master-overrides.tsv` |
| `work\xscn\apply_master.py` | ⭐ 新 efile 预填主力（复用既有判据/正则/代号过滤） |
| `resolve_master.py` / `build_dict.py` / `build_root_dict.py` / `build_prose_dict.py` / `build_master.py` | 冲突裁定 + 每完成一个 efile 的「四连」 |
| `work\audit\progress.py` | 进度审计；`--dump-fake` 查 cp1252 假汉字 |
| `docs\24-*.md` | 覆盖方法、判据、场景 `.txt`/`.xscn`/`.ply`/位图各层打法 |
| 技能 `opengen-sdl2-efile-localization`（24 KB） | 同引擎专项技能 |
| `.workbuddy\memory\MEMORY.md` / `MECHANICS.md`(89 KB) | 状态真源 / 机制真源 |

---

## 二 新工作：5 个 efile，且实际只有 **2 套数据文件**

**D:\OpenGeneral 的 5 个 efile（GUS / GUS_Wx / GUS_PeG / GUS_Zx / ALBERICH）与 OpenPG2 的 21 个无一重叠。**

### 2.1 efile 数据文件哈希实测 —— 重大利好

| efile | EQUIP.TXT | NAMES.TXT | NATIONS/FRONTS/TERRAINEX/EQUIP.XEQP | STRINGS_EFILE.TXT |
|---|---|---|---|---|
| `EFILE_GUS` | 128,820 / `1636C24B` | 32,969 / `04490CA6` | 同 | `FD0C9D57` |
| `EFILE_GUS_PeG` | 同上 | 同上 | 同 | `FD0C9D57` |
| `EFILE_GUS_Wx` | 同上 | 同上 | 同 | `FD0C9D57` |
| `EFILE_GUS_Zx` | 同上 | 同上 | 同 | `FD0C9D57` |
| `EFILE_ALBERICH` | 126,051 / `1FA68216` | 32,715 / `CE847F78` | 独立 | `FD0C9D57` |

⇒ **4 个 GUS 系 efile 的根级数据文件逐字节相同**：翻译一套即覆盖 4 个；
⇒ ALBERICH 独立一套；
⇒ 5 个 efile 目录 = **2 套根级翻译**（GUS 家族 + ALBERICH）；
⇒ `STRINGS_EFILE.TXT` 5 个 efile 共用一份。

### 2.2 D:\OpenGeneral 独有的层（OpenPG2 没有）

`DOC\`(14 文件/25 MB)、`MAPFILES\`(2,518)、**`MAPNAMES\`(989 文件/4.3 MB)**、`OPENTXT\`(17)、`OPENICONS\`(47)、`SUITE_UI\`(4)。

其中 **`MAPNAMES` 是新层，需单独评估**（见 §四）。

---

## 三 实测体量（含复用率）

测量工具（本次新建，只读，可复跑）：
`_probe_og_measure.py`（全层量测，支持 `<ROOT>` 参数）、
`_probe_og_coverage.py`（复用 `apply_master.py` 判据量覆盖率）、
`_probe_og_prose.py`（`.txt` 整行对词库命中率）、
`_probe_og_sample.py`（各 efile 原文语种抽样）。

### 3.1 两作体量对照

| 层 | `D:\OpenPG2`（21 efile） | `D:\OpenGeneral`（5 efile） | 占比 |
|---|---|---|---|
| efile 数 | 21 | 5 | **24%** |
| 根级待译行 | 127,008（唯一 71,519） | 64,119（去重 GUS×4 后 ≈ **25,476**） | **20%** |
| `.xscn` 文件 / 条目 | 3,931 / 324,629（唯一 193,113） | 3,046 / **163,365**（唯一 **81,629**） | **50%** |
| `.txt` 文件 / 字符 | 15,035 / 9,404,245 | 9,721 / **3,597,423** | **38%** |
| `.ply` 文件 / 字符 | 339 / 169,520 | 32 / **1,135** | ~1% |
| SCENARIO 总文件 | 23,608 | 16,145 | 68% |

**⇒ D:\OpenGeneral ≈ OpenPG2 全库的 35–50%。**

### 3.2 `.xscn` 层程序覆盖率（真实可复用比例）

用 `apply_master.py` 同款判据实测（精确命中 + 词级组合 + 纯代号保留 = 程序覆盖）：

| efile | 唯一串 | 槽位 | 程序覆盖 | 需人工/LLM |
|---|---|---|---|---|
| `EFILE_ALBERICH` | 320 | 324 | 78.1% | 70 |
| `EFILE_GUS` | 33,311 | 69,732 | 53.4% | 15,507 |
| `EFILE_GUS_PeG` | 6,526 | 14,259 | 34.9% | 4,246 |
| `EFILE_GUS_Wx` | 39,654 | 76,082 | 33.1% | **26,512** |
| `EFILE_GUS_Zx` | 1,818 | 2,968 | 72.1% | 507 |
| **合计** | **81,629** | **163,365** | **42.6%** | **46,842 条**（占槽位 90,290 = 55.3%） |

**⚠️ 42.6% 远低于 `MEMORY.md` 声称的「~93%」。** 用 OpenPG2 自己的 21 个 efile 做对照（同判据）：

- **未汉化的 efile 覆盖率区间 4.5%–83.7%**（LUPO 4.5% / Clu 6.4% / OLGCW 8.9% / SON 10.6% / COMWW2 11.8% / ATOMIC 13.5% / AO 16.0% / OPENPG 17.3% / GCE 25.1% / OoB 40.7% / PzLIGA 47.8% / OPENPEG 50.8% / ROI 52.2% / LXF 52.7% / OLGWW2 58.7% / NOKORP 63.5% / OPENAK 83.7%）；
- **已收官的 efile 覆盖率反而 ≈0**（AG 0.2% / NASHORNPBEM 0.0% / KAISER 3.7% / BASEKORP 6.8%）——
  因为**已汉化 efile 的 `.xscn` 串区已被就地回写成 GBK 中文**，对英文 master 自然不再命中。

实测证据（`EFILE_AG`，已收官）`.xscn` 抽样：
```
ITEM:µÚ1¾üÍÅ/µÚ2´ó¶Ó      ← GBK「第1军团/第2大队」按 cp1252 读出的样子
ITEM:¸ÇÎÚË¹¡¤ÓÈÀûÎÚË¹¡¤¿­Èö
```
对照未开工的 `EFILE_NOKORP`，`.xscn` 仍是纯英文（`Admiral Graf Spee` / `Gulf of Sirte`…）。

**⇒ 结论：**
1. 覆盖率探针**只对未汉化 efile 有效**——D:\OpenGeneral 正好全部未汉化，**42.6% 是可信的真实数字**；
2. 42.6% 落在 OpenPG2 自身未汉化 efile 的**正常区间内**，并不异常，但说明 **「~93%」是乐观口径，不能用来估工**；
3. OpenPG2 主线自己也**还剩约 10 个 efile 未收官**（覆盖率同表的低值项）。

### 3.3 `.txt` 场景散文层复用率（最大的一块）

把 9,704 个 `.txt` 按行拆开，看整行是否已在词库中（**下界**，散文多为整段原文）：

| efile | 文件 | 行 | 字符 | 整行命中 | 命中字符 |
|---|---|---|---|---|---|
| `EFILE_GUS` | 2,463 | 8,977 | 1,125,247 | 10.9% | 13.4% |
| `EFILE_GUS_Wx` | 5,269 | 14,797 | 1,760,785 | 11.6% | 3.1% |
| `EFILE_GUS_PeG` | 1,846 | 5,093 | 580,417 | 3.0% | 0.3% |
| `EFILE_GUS_Zx` | 117 | 3,669 | 55,878 | 33.6% | 28.7% |
| `EFILE_ALBERICH` | 9 | 62 | 10,355 | 0.0% | 0.0% |
| **合计** | **9,704** | **32,598** | **3,532,682** | **12.5%** | **6.3%** |

**⇒ `.txt` 层需处理 ≈ 3,309,667 字符。这是整个项目最重的一块。**

### 3.4 原文语种抽样（决定能否直接用英文词库）

- `EFILE_GUS` / `GUS_Wx` / `GUS_PeG` 的场景散文**基本是英文**（由波兰语粗糙转写的英文），`.xscn` 含波兰变音符 0%–2%；
- **仅 `EFILE_ALBERICH` 的 `.txt` 是真正的波兰语**（9 文件 / 10,355 字符，占比极小）。

**⇒ 英文→中文的词库在 95% 以上的内容上可直接套用；波兰语部分只有 ALBERICH 的 9 个文件。**

---

## 四 逐层工序与估算

| # | 层 | 量 | 复用 | 人·天 |
|---|---|---|---|---|
| 1 | **UI**（`strings-zh.txt` + `simhei.ttf` + 3 张 PNG + `Settings.cfg`） | 1 套 | **100%** | **0.5** |
| 2 | **根级数据文件**（`EQUIP/NAMES/NATIONS/FRONTS/TERRAINEX/EQUIP.XEQP`） | **2 套**（GUS 家族 ×4 共享 + ALBERICH） | 部分 | **2–4** |
| 3 | **`.xscn` 场景串** | 46,842 唯一串 / 90,290 槽位 | 42.6% 已覆盖 | **8–15** |
| 4 | **`.txt` 场景散文** | 3,309,667 字符 / 9,704 文件 | 整行 6.3% | **15–30** |
| 5 | **`.ply`** | 32 文件 / 1,135 字符 | — | **0.5** |
| 6 | **`MAPNAMES`**（OpenGeneral 独有层） | 18,571 唯一地名 | 部分通用词 | **2–8**（可降级/跳过） |
| 7 | **校验 / 四连 / 收官回归** | 判据：`.xscn` 漏译 ≤0.5% 且 `.txt` >99% 且 `.ply` 全译 | 工具在位 | **3–5** |
| | **合计** | | | **31–58 人·天** |

**换算：单人 + 现有工具链 + LLM 批量 ≈ 6–12 周；若流水线顺跑、散文批量过，最快 3–4 周。**

**校准依据**：OpenPG2 主线从 2026-09-20 到 2026-10-15（约 26 天）做到 21 efile 收官 11，
同期完成 `.txt` 9,404,245 字符 —— **但那 26 天包含了从零搭建整条流水线的成本**；
D:\OpenGeneral 摊上的是 38% 的 `.txt` 量 + 50% 的 `.xscn` 槽位，而**工具、词库、技能、位图方案全部已沉没**。
⇒ 相比「从零汉化」，本作节省约 **80%**。

---

## 五 真实剩余风险 / 待核对项

1. **`.xscn` 覆盖率只有 42.6%**
   46,842 条新串是硬工作量，主要集中在 `GUS_Wx`（26,512 条，二战大库，1,526 个场景）。
   → 缓解：先跑 `apply_master.py --with-words`，余量交 LLM 批量，再用 `resolve_master.py` 裁定冲突。

2. **`.txt` 散文 3.31M 字符是主成本**，且**整行复用仅 6.3%**。
   → 这是唯一无法靠词库规模摊薄的部分；它是 1,526+1,846+2,463 个场景各自的简报/胜败文本。
   → 建议：这是最应该用 LLM 批量 + 分级质检（抽检 5%）来压成本的地方。

3. **cp1252 假汉字骗校验**（`MEMORY.md` 第 47 条）
   裸 `decode('gbk')` 会把高字节解成假汉字。可靠判据 = GB2312 字节范围 + 逐 efile 黑名单，用 `progress.py --dump-fake`。
   → D:\OpenGeneral 原文是英文/波兰语，本身就含 cp1250 高位字节，此坑**一定会踩**。

4. **版本差（待核对，非阻塞）**
   本作 exe 是 **25.02.26.0**，比主线的 26.3.30.0 **旧**。
   `strings-en-template.txt` 已证实逐字节相同，故风险很低；但建议核对 PG2 的 `strings-zh.txt`
   是否覆盖了本作模板的全部 916 行（PG2 现存 `strings-zh.txt` = 15,291 B，其 `.bak` = 21,182 B，
   两者差异原因需确认后再决定以哪份为准出稿）。

5. **`MAPNAMES` 新层（18,571 唯一地名 / 4.35 M 字符）**
   OpenPG2 布局里没有这一层。若该层在游戏内可见，是额外 2–8 人·天；
   若仅为编辑器辅助数据，**建议直接跳过**（先实机确认它是否上屏）。

6. **`DOC\` 25 MB / 14 文件**（含 `OG_Manual.pdf`、波兰语 `OG_Poradnik.pdf`、`OG_School_1..5.pdf`）
   → 文档是否汉化属产品决策，**不计入上表**；若做，另行估算。
   另：`SMACK\` 38 个 `.avi`（134 MB）**无字幕流**，无翻译成本。

---

## 六 建议的落地顺序

```
① UI 三件套（半天）→ 启动游戏截图，确认「打开就是中文界面」   ← 先摘果子
② GUS 家族根级数据（1 套覆盖 4 个 efile）+ STRINGS_EFILE.TXT
③ ALBERICH 根级数据
④ EFILE_GUS_Zx（覆盖率 72.1%，最小）→ 当流水线磨合试刀
⑤ EFILE_GUS → EFILE_GUS_PeG → EFILE_GUS_Wx（按体积递增）
⑥ .txt 散文批量（占主成本，与 ⑤ 并行）
⑦ 每完成一个 efile 跑四连 + progress.py 校验；收官判据同 OpenPG2
```

**结论：值得做。** 硬骨头（编码、字体、位图、工具链、词库）已全部啃完；
`D:\OpenGeneral` 是既有工程的一次**规模化横向扩展**，不是新项目。

---

## 附：本次核查用到的证据与方法

| 项 | 方法 |
|---|---|
| UI 同构 | 逐文件名 + 逐字节数比对两个 `OPENGUI`；模板文件 MD5 |
| 编码可行性 | v1 的 PE 反汇编（`TTF_RenderUNICODE_*` 导入、无 Wide GDI 文本 API）+ **OpenPG2 已实机跑通的事实**；现有 `strings-{pl,hu,de,es}.txt` 经严格 UTF-8 解码器验证**均为单字节 CP1250/1252**，故出稿走 **GBK(936) 无 BOM** |
| 覆盖率 | `_probe_og_coverage.py`（复用 `apply_master.py` 同款 `TOK`/`NUM`/`word_ok` 判据与 `master-glossary.tsv`/`master-words.tsv`/`master-resolve.tsv`） |
| 体量 | `_probe_og_measure.py <ROOT>`，两个根目录各跑一次 |
| 散文命中 | `_probe_og_prose.py` |
| efile 归并 | `Get-FileHash -Algorithm MD5` 对 5 个 efile 的 7 个数据文件 |
| 语种 | `_probe_og_sample.py <ROOT> [EFILE…]`（波兰变音符计数 + 特征词） |
| 位图 | `_probe_opengui_montage.png`（34 张 UI 图拼图目视） |
