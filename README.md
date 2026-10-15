# 军事游戏汉化 · 工作区总索引

> **工作区**：`D:\DSH\军事游戏汉化`
> **性质**：用户个人兴趣项目 —— 把若干款**军事/战略题材**老游戏本地化为**简体中文**，
> 同时作为研究 **「西方游戏文化渗透史」** 的观察材料。
> ⚠️ **仅个人研究使用，不对外发布**；汉化**只做语言转换**，**不改原文世界观、阵营划分与叙事措辞**（保真优先）。
>
> **本文件**是工作区**总索引**（对位上游参照 `github.com/wicanr2/pg-cht` 的仓库根 README）。
> 建立：2026-10-10 · 维护方式：**结构性变更时更新**（进度数字以真源为准，本文件不手抄进度）。

---

## 一、游戏清单

| 代号 | 游戏目录 | 引擎 / 界面 | 状态 | 本作归档 |
|---|---|---|---|---|
| **OpenPG**（主线） | `D:\OpenPG2` | Open General / OpenGen 26.3.30.0；SDL2+SDL2_ttf | 全库 21 efile，**收官 11** | `docs\`（跨作）· `glossary\` · `work\<tag>\` |
| **PeG** | `D:\Program Files\PeG` | SSI *modgen* 1998；DirectDraw 16bpp + GDI **ANSI** | **已达可用状态** | **[`peg\`](peg/README.md)** |
| **PeG-WW2** | `D:\Program Files\PeG-WW2` | 同上引擎（**与 PeG030 同一构建**）；PeG 的**二战 MOD**（Redball 2005） | **exe+界面+场景三层已部署**（待实机复测） | **[`pegww2\`](pegww2/README.md)** |
| **PG Forever** | `D:\PGForever1.021` | HTMLayout（UI 由 HTML/CSS 渲染） | UI 层完成 | [`pgforever\`](pgforever/) · `.workbuddy\memory\PGFOREVER.md` |

> 三作**引擎互不相同**（SDL2 / DirectDraw+GDI / HTMLayout），因此技术手法差别极大 ——
> 这正是把**方法论**与**引擎专项**分层沉淀的理由（见 §六）。

---

## 二、目录骨架（统一约定）

```
D:\DSH\军事游戏汉化\
│
├── README.md              ← 本文件：工作区总索引
├── .workbuddy\
│   └── memory\            ← ⭐ 状态真源（见 §四）
│       ├── MEMORY.md             只放状态与决策、指针
│       ├── MECHANICS.md          机制真源（各层显示机制 / 事故档案）
│       ├── MEMORY-*-archive-*.md 归档（勿删）
│       └── YYYY-MM-DD.md         逐日工作日志（append-only）
│
├── docs\                  ← 跨作文档（40 篇，编号 = 阅读顺序）
│   └── 00-工作空间导航.md    ⭐ OpenPG 侧的导航（含脚本生成的进度区）
│
├── glossary\              ← 译名真源
│   ├── standard-glossary.tsv     ⭐ 23,200 条（UTF-8 BOM）
│   └── README.md                 整理规则与进度
│
├── peg\                   ← ⭐ PeG 子项目归档（pg-cht 式）
│   ├── README.md                 本作索引
│   ├── 方法\                      ⭐ 经验与方法论
│   │   └── PeG汉化经验总结.md     技术发现 + 踩坑档案 + 可复用清单
│   ├── research\                 研究档案 + 术语资产 + 译法映射 + 行级对照
│   │   ├── README.md
│   │   ├── evidence\             原始素材（脚本可复算）
│   │   └── symbol-layer\         符号层渲染证据
│   └── testbed\                  备份与试作（backup / backup-scn-flag / backup-ui-src / *.pre-*）
│
├── pgforever\             ← PG Forever 子项目
│   ├── docs\ · poc\ · tools\ · work\ · backup\
│
├── work\                  ← 工作稿与脚本（**编辑入口全在这里**）
│   ├── peg\                       ⭐ PeG 全部脚本（补丁 / 生成器 / 分析）
│   ├── xscn\ · tmsg\ · xsch\      OpenPG 各层结构工具
│   ├── audit\progress.py          ⭐ 全库进度实测
│   └── <efile tag>\               各 efile 工作台
│
├── tools\                 ← 跨作工具（PowerShell）
└── backup\                ← 全部原件与回滚点（**勿删**）
```

> **对齐说明**：目录命名**不强行统一**为 pg-cht 的中文名（`翻譯/`·`歷史百科/`），
> 但**结构层级对齐**：每作一个平级目录 → 内设 `README.md` + `方法/经验` + `research/資產` + `testbed/备份` +
> 脚本集中于 `work/<tag>/`。**新增作品照此骨架建目录**。

---

## 三、上手路径（新会话必读顺序）

| 顺序 | 读什么 | 为什么 |
|---|---|---|
| 1 | **本文件** | 知道有哪些作品、资产在哪 |
| 2 | `.workbuddy\memory\MEMORY.md` | **状态真源**：当前进度与已定决策 |
| 3 | `.workbuddy\memory\MECHANICS.md` | **机制真源**：各层显示机制、踩过的坑 |
| 4 | 对应作品的 `README.md` | 如 `peg\README.md` —— 本作现状与工具链速查 |
| 5 | 对应作品的 `方法\*\经验总结.md` | 如 `peg\方法\PeG汉化经验总结.md` —— 技术发现与方法论 |
| 6 | `docs\00-工作空间导航.md` + `docs\08-文本来源排查方法论.md` | OpenPG 侧导航 + **「这段字从哪来」决策树**（跨作通用） |

> **一句话原则**：改了几处文本都没反应时，**先做非侵入诊断** ——
> ① 比对文件 **`atime` 与游戏启动时刻**（谁被读了）；② **查导入表**（是不是 Windows API 在生成）；
> ③ 内存里搜不到那串英文 ⇒ 它多半是**图片**或**二进制场景数据**。

---

## 四、真源与复算

| | 位置 | 说明 |
|---|---|---|
| ⭐ **状态真源** | `.workbuddy\memory\MEMORY.md` | **只放状态与决策**；进度数字以此为准 |
| ⭐ **机制真源** | `.workbuddy\memory\MECHANICS.md` | 各层显示机制、目录矩阵、事故档案 |
| **归档**（勿删） | `.workbuddy\memory\MEMORY-*-archive-*.md` | 压缩迁出的明细全文 |
| **OpenPG 进度复算** | `work\audit\progress.py` | `python progress.py` 打印实测矩阵 |
| **PeG 备份链** | `peg\testbed\` + `D:\Program Files\PeG\PeG030.exe.orig-backup` | 见 `peg\README.md` §三 |

> ⚠️ **判进度必须直读文件审计**，绝不能看映射表。两种「假已改」不算进度：
> ① 安装戳 / 官方自带；② 映射表 `src==dst` 恒等映射。
> ⚠️ **cp1252 假汉字会骗过校验**（裸 `decode('gbk')` 把高字节解成假汉字）；
> 可靠判据＝**GB2312 字节范围 ＋ 逐文件假汉字黑名单**。

---

## 五、硬纪律（跨作通用）

1. **绝不覆盖改原文**；备份与覆盖**分两条命令**；**先重建到临时 → 回读校验 → 才写正式**。
2. 出稿 **GBK(936) / UTF-8(BOM)** 按各作约定；**换行沿用原文**；
   ⚠️ 拆行须 `(\r\n|\r|\n)` **三态**（老引擎可能用**裸 CR**）。
3. **不改 exe 前先查导入表** —— 见到 `GetDateFormatA`/`GetLocaleInfoA` ⇒ 文本来自 Windows，改 exe 数据无用。
4. **补丁三纪律**：幂等 · 默认 dry-run（`--apply` 才写）· **等长替换优先**。
5. **不全量翻译脚本/说明类文件** —— 建**整文件排除清单**（本项目踩过：游戏脚本被行内替换污染）。
6. **不靠肉眼不靠猜** —— 编码、字体、格宽、行数，**全部实测或用脚本复算**。
7. 需要截图时**停下告知，由用户手动截取**；**严禁自行启动/点击游戏**。
8. **结论被推翻时写明撤回原因**（防止下一轮重蹈）。

---

## 六、归档规范（新增作品照此办）

> 参照 `pg-cht` 的仓库组织方式，落到我们的场景。

### 6.1 分层：**技能（跨作可复用）** ⟷ **项目（本作记录）**

| 层 | 放哪 | 内容 | 判断标准 |
|---|---|---|---|
| **方法论**（跨作可复用） | 用户级技能 `~/.workbuddy/skills/` | 双轨制 · 文风口径 · 单字节引擎启用范式 · 归档规范 | **换个引擎还能不能用？** 能 ⇒ 技能 |
| **引擎专项** | 用户级技能（如 `opengen-sdl2-efile-localization`） | 某引擎的文件格式与补丁手法 | 同引擎的新作能否直接复用？能 ⇒ 引擎专项技能 |
| **本作记录** | 工作区 `<game>/` | 现状、踩坑史、术语表、映射表、对照表、备份链 | 只对**这一作**成立的 ⇒ 项目 |

**⚠️ 铁律：项目里发现的可复用经验，必须在收尾时「上浮」到技能**（见 `peg/方法/PeG汉化经验总结.md` §七 可复用清单）。

### 6.2 每作目录的必备件

```
<game>/
├── README.md          ← 必备：一句话结论 + 档案清单 + 现况表 + 工具链速查 + 边界纪律
├── 方法\               ← 必备（或 docs\ 等价物）：经验总结 / 技术发现 / 踩坑档案
├── research\ 或 docs\  ← 术语表 / 译法映射 / 行级对照 / 证据素材
└── testbed\ 或 backup\ ← 备份链（原版 + 各里程碑快照）
```
对应脚本集中放 `work\<tag>\`，**不散落在游戏目录**。

### 6.3 README 层级（每层都要有）

| 层级 | 文件 | 回答什么 |
|---|---|---|
| 工作区 | `README.md`（本文件） | 有哪些作品、资产在哪、怎么上手 |
| 本作 | `<game>/README.md` | 本作是什么、现在什么状态、怎么跑脚本 |
| 子目录 | `<game>/research/README.md` 等 | 这个目录怎么用、填证规范、复算方式 |

### 6.4 证据约定

- **实测截图**放 `research/evidence/` 或 `poc/`，文件名自解释（`pg2-scenario-list-full-cht.png` 式）。
- **凡结论须可复算**：给出生成它的脚本路径与命令（如 `research/evidence/` ← `work/peg/extract_research.py`）。
- **区分「已实测」与「推定」**：未实测的结论必须显式标注。

---

## 七、归档地图

| 位置 | 内容 |
|---|---|
| [`peg/`](peg/README.md) | ⭐ PeG 子项目（索引 · 方法 · 研究 · 备份） |
| [`peg/方法/PeG汉化经验总结.md`](peg/方法/PeG汉化经验总结.md) | ⭐⭐⭐ PeG 完整经验总结 |
| [`pegww2/`](pegww2/README.md) | ⭐ PeG-WW2 子项目（二战 MOD；阶段 0 评估见 `docs/40`） |
| [`pgforever/`](pgforever/) | PG Forever 子项目（HTMLayout 界面） |
| [`docs/`](docs/) | 跨作技术文档 40 篇（`00-工作空间导航.md` 为导览） |
| [`glossary/`](glossary/) | OpenPG 译名真源（`standard-glossary.tsv` 23,200 条） |
| [`work/`](work/) | 全部脚本（`peg/`·`xscn/`·`audit/`·`exe/` …） |
| `backup/` | 全部原件与回滚点（**勿删**） |
| `.workbuddy/memory/` | 状态真源 + 机制真源 + 归档 + 日志 |
| `peg/testbed/skills-backup/` | 技能拆分前的原始单文件备份（**勿删**） |

### 7.1 用户级技能（`~/.workbuddy/skills/`）—— 「一作一技能 ＋ 一方法论」

| 层 | 技能 | SKILL | refs | 覆盖 |
|---|---|---|---|---|
| **方法论** | `military-game-docs-translation` | 13 KB | 7 | 跨引擎：双轨制 · 文风 · 单字节引擎范式 · **归档规范** · 开工单 |
| **项目** | `opengen-sdl2-efile-localization` | 24 KB | 3 | OpenPG（SDL2 + efile 目录制） |
| **项目** | `ssi-modgen-peg-localization` | 14 KB | 3 | **PeG**（SSI modgen · DirectDraw+GDI ANSI） |
| **项目** | `pgforever-htmlayout-localization` | 16 KB | 0 | **PG Forever**（HTMLayout 界面） |
| **手法库** | `win-game-html-ui-localization` | 8 KB | 9 | **跨项目**二进制/界面工程通用手法（按汉化阶段分册） |
| 其他 | `sd25-pe` | 5 KB | 8 | Seedance 2.5 提示词（**第三方技能**，与汉化无关） |

> **分层判据**：「**换一款游戏 / 换一个引擎，这条还成立吗？**」
> 成立 ⇒ 方法论技能 ｜ 同引擎成立 ⇒ 项目技能 ｜ 只对本作成立 ⇒ 项目档案（本文与 `<game>/`）。
> ⚠️ **收尾必做「可复用清单」盘点**：换引擎仍成立的手法**必须上浮到技能**（见 §六 归档规范）。
> ⚠️ 拆分为多册的技能，**SKILL.md 是索引 + 最高价值要点，细节在 `references/`**。
