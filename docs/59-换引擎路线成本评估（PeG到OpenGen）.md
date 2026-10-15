# 换引擎路线成本评估（PeG → Open General）

> 建立：2026-10-13　·　起因：用户提问「换引擎路线成本有多大？你是基于哪个引擎重写还是从 0 开始？」
> 状态：**只做评估，未动任何文件**（PeG 原版、`D:\Program Files\PeG-1\` 的 v5c/v6/v7/v8 变体、`D:\OpenPG2` 均保持原样）
> 效力：**评估记录，未实施**。后续实际路线为 PeG 原生改造（`docs\60`~`docs\67`），本文件保留为决策依据。

---

## 一、一句话结论

**这条路不是「重写」，也不是「从 0」**——引擎现成（Open General / OpenGen，本工作区的主线目标），
而且**社区已经把 People's General 的内容移植好了**（`D:\OpenPG2\EFILE_OPENPEG\`，OpenPeG v1.01C，作者 MG43）。
剩下的是**我们已经滚瓜烂熟的汉化活**：按我们自己的工作量表，OPENPEG 是「小」档，
估 **1–2 周**（含用户实机验收）能到「能玩的中文 PeG」。
真成本不在汉化，而在两个缺口：① 体验不是原版引擎（公式/AI/UI 流程都不同）；② PeG 的 213 个场景里只有 19 个被移植。

---

## 二、本机实证（全部现场核过，非推测）

### 2.1 引擎：Open General / OpenGen —— 就是本工作区的主线
| 项 | 值 |
|---|---|
| 路径 | `D:\OpenPG2\`（`OpenGen.exe` 6,316,032 B，2026-09-24 23:57） |
| 版本/作者 | FileVersion **26.3.30.0**（product 26.03.30.0），Luis Guzman（`docs\01`） |
| 技术栈 | **SDL2 + SDL2_ttf**（+ SDL2_image / freetype / libpng / libjpeg / fmod / zlib） |
| 本仓定位 | `MEMORY.md` §二「**OpenPG（主线）**」；`docs\00` 首行目标游戏即它；21 个 efile，**已收官 11** |
| 汉化现状 | UI 主串 100%（`OPENGUI\strings-zh.txt`，`UI_Lang=strings-zh`）；exe 硬编码串（37 个对话框 / 单位面板 48 / 地图 HUD 49 / 单位标签）已做；字体 `simhei.ttf`（`Settings.cfg` 实测） |
| 分辨率 | **不是「需要支持」的问题**：SDL2 窗口化引擎，`Settings.cfg` 里没有 SetDisplayMode 式死分辨率，只有窗口/缩放类偏好（`zoomnid1/2=100`、`Grid=14`、`hidetaskbar`）。原生高分辨率＋缩放是引擎自带能力 |

### 2.2 内容：PeG 已被社区移植成 OpenGen 的 efile
`D:\OpenPG2\EFILE_OPENPEG\`（`efile.xml`：title **OpenPeG**，version **1.01C**，描述
"Openized People's General Equipment file converted and adapted for Open General"），**共 163 个文件**：

- `SCENARIO\`：**19 个 `.xscn`** ＋ **1 个战役树 `1uscamp.xcam`** ＋ **77 个 `.txt`**（每场景 4 份：`<名>.txt` 地名 / `…i.txt` 简介 / `…l.txt` 信件 / `…v.txt` 胜利文案 ＋ `us.txt`）
  —— 19 个场景名正是 1998 年 PeG 美方战役链：`almaty1 astrakhan1 bangkok1 ekaterinburg1 hanoi1 irkutsk1 kazan1 kazansnow1 khabarovsk1 penang1 pusan1 saigon1 sakhalin1 seoul1 singapore1 taejon1 ulanude1 vladivostok1 volgograd1`
- 根级：`equip.txt`(21,313 B) · `equip.xeqp`(282,190 B) · `names.txt` · `nations.txt` · `fronts.txt` · `weather.txt` · `TerrainEx.txt` · `colors.txt` · `strings_efile.txt` · `equip.cfg`
- 美术：`OPENGUI\`（整套 PeG 风格 UI 图）＋ `OPENDAT\`（`start_openpeg.png`、`dossier_*.png`、`flag_*.png`、`inspect_*.png`、`roundel.png`）
- ⭐ **本机已经跑过**：`Settings.cfg` 的 Recent 里有 `D:\OpenPG2\EFILE_OPENPEG\SCENARIO\1uscamp.xcam`

### 2.3 汉化缺口（用我们自己的量表，不靠感觉）
| 指标 | 值 | 出处 |
|---|---|---|
| OPENPEG `.xscn` | 576 条 / **含汉字 0 / 0.0%** | `docs\00` §三 矩阵 |
| OPENPEG `.txt` | 77 个 / **已中文化 0 / 0.0%** | 同上 |
| OPENPEG `.ply` | 0 | 同上 |
| 工作量档位 | **「小」** | `docs\30` B13 |
| 唯一串体量 | `.xscn` 唯一 417 · `equip` 672 · `names` 719 · `nations` 41 · `strings` 101 · `.txt` 77 个 / 31 KB | `docs\30` §二表 |
| 已做的位图层 | `EFILE_OPENPEG\OPENGUI\hex_text.png`（`docs\07` L65）＋ `mouse_build` / `mouse_missions`（`docs\09` L101） | 已落盘 |

> 对照：已收官的 `OPENPG`（同为 PG 系 efile）当时是 `.xscn` 唯一 2,329 + `.txt` 190 + 根级四件套 190 ——
> **体量同一数量级**，而那条已经走完 ⇒ OPENPEG 的工作量是可以外推的，不是未知数。

### 2.4 PeG 原版的场景规模（决定「缺口②」多大）
| 位置 | 数量 |
|---|---|
| `D:\Program Files\PeG\Scenario\*.SCN` | **206** |
| `D:\Program Files\PeG\Userscen\*.scn` | **7** |
| 合计场景 | **213** |
| `D:\Program Files\PeG\MAP\` | **436** 个文件 |

其中 1998 核心战役 ≈ OPENPEG 已移植的那 19 个；其余是扩展/自制（`RED_*` 2012、`ns4*` 2002、`IND_*` 2012、`NVC_*` 2012、`Userscen` 等）。
⇒ **这 194 个场景（及其地图）不在 OpenPeG 移植里**；要在 OpenGen 上玩它们，需要自写 `.SCN`/`.MAP → .xscn/.map` 转换器（中等工程；工具在手：`OpenSuite.exe` 编辑器，且我们已掌握 PeG `.SCN` 结构）。

---

## 三、成本估算（人日，按本仓既有节奏）

| 阶段 | 内容 | 估时 | 依据 |
|---|---|---|---|
| S0 审计 | 切 `EFolder=efile_openpeg\` 跑一局 + 我方静态盘点未汉化面（根级/`.xscn`/`.txt`/位图/exe 串） | **0.5–1 天** | 用户跑 + 我用 `work\audit\progress.py` 出数 |
| S1 根级四件套 | `equip.txt`(672) / `names.txt`(719) / `nations.txt`(41) / `strings_efile.txt`(101) | **1–2 天** | 跑 `apply_master.py`（统一总词库 119,624 条覆盖 ~93%），余交 LLM；11 个 efile 的既有节奏 |
| S2 串层 | `.xscn` 唯一 417 条 | **1–2 天** | 管线已泛化（`docs\30` §三 P1） |
| S3 散文层 | 77 个 `.txt` / 31 KB（地名、简介、信件、胜利文案） | **0.5–1 天** | 与 AG 的 286 份散文同工序（AG 一天内 286/286） |
| S4 位图层 | OPENPEG 剩余 OPENGUI/OPENDAT 图（3 份已做） | **0.5 天** | `docs\07` / `docs\09` 既有手法 |
| S5 实机验收 | 19 场景 + 战役树跑通、无豆腐/无溢出 | **2–3 天（用户）** | `docs\27` 的字体坑已存档 |
| | **合计** | **≈ 6–10 人日（1–2 周，含用户验收）** | |

**技能基础**：`opengen-sdl2-efile-localization`（24 KB，本仓技能）＋ `win-game-html-ui-localization`（手法库）＋ 统一总词库 —— 换引擎路线**不需要新方法论**。

---

## 四、代价与风险（必须摊开讲）

1. **不是原版 PeG**：OpenGen 是**重实现引擎**。战斗公式（`attach_*` 附件、骰子/压制模型）、AI（`OpenGen_AI` 文档）、UI 流程、战役结构都与 1998 的 SSI modgen 不同。⇒ 换引擎满足的是「**PeG 的内容＋现代分辨率/现代 UI**」，不是「1998 原版手感」。
2. **场景覆盖缺口**：213 个场景里只有 19 个；扩展包要自己转换（见 §2.4）。
3. **新增依赖**：以后所有 PeG 侧的汉化/维护要在 OpenGen 的 efile 体系里做（好处是 `TEXT-ZH\` 删目录即回滚，比改 exe 安全得多）。
4. **不等于放弃现状**：原版 PeG 的汉化成果与 v5c 高分屏产物都留在原地，不互相破坏。

---

## 五、与「继续原版 exe 的 RE 路线」对比

| | 换引擎（OpenGen + EFILE_OPENPEG） | 原版 RE（现状） |
|---|---|---|
| 引擎层成本 | **0**（现成，SDL2，分辨率/缩放原生） | 0（原版引擎） |
| 内容 | 19 场景已移植，**转换器不用写** | 213 场景全在 |
| 主要工作量 | OPENPEG 汉化「小」档 ≈ 6–10 人日 | 剩余界面缺陷（工具列不右移、底栏不下移、局部花屏）**成本不可预测** |
| 已验证成果 | — | ⭐ **v5c 已可用**：地图铺满 1024 宽、按钮形状/位置/点击区一致、底栏文字正常 |
| 未解 | — | 刀具列绘制链（`0x44ACDA → 0x4235E5 → 0x47E0A0/0x47E4E0`）的 `Blt` 裁剪：`dst.left = rect.left + dx` **仅在 `dx ≥ 0` 时生效** ⇒ 记录 x 右移后助手仍从旧处取样 |
| 体验保真 | ❌ 换引擎 | ✅ 原版 |
| 可回滚性 | 高（删 `TEXT-ZH\` / 换回 `EFolder`） | 高（母本 md5 未动，变体各自独立） |

**三条仍在桌面的 RE 选项**（用户尚未拍板）：**A** 冻结 v5c 现状；**B** 读透 `0x47E4E0`/`0x47E050` 后一次性做 v9（推荐）；**C** 运行期 DLL hook。

---

## 六、建议路径（零风险）

1. **先做 S0 审计（半天，不改任何东西）**：用户把 `Settings.cfg` 的 `EFolder=efile_kaiser\` 改成 `EFolder=efile_openpeg\` 跑一局并截图；我方静态出清单（哪些层还是英文、哪些图带英文）。
2. 拿到「能玩到什么程度、差多少中文」的**事实**后，再与 RE 路线的剩余成本二选一（或并行：RE 归我，审计归你）。
3. 若决定切换：S1 → S2 → S3 → S4 顺序推进，每个 efile 完成后跑四连（`build_dict && build_root_dict && build_prose_dict && build_master`）。

---

## 七、直接回答「基于哪个引擎 / 从 0 吗」

| 候选基座 | 说明 | 判断 |
|---|---|---|
| ⭐ **Open General / OpenGen** | 现成引擎 ＋ **社区已把 PeG 内容移植**（OPENPEG）＋ 本仓现成汉化管线与词库 | **首选，成本最低** |
| LGeneral | 开源 C/SDL 的 PG 系引擎（`pg-cht` 语料里有源码） | 需自写 PeG 数据读取层＋地图/场景转换，远贵于首选 |
| 自研引擎（从 0） | 重写 SSI modgen 引擎 | **1–3 人年，不建议** |
| PG Forever | 本仓另一条线（HTMLayout ＋ 原生 Unicode），但是 **PG1** 系 | 不覆盖 PeG 内容 |

---

## 八、纪律声明

- 本报告**未修改任何文件**（PeG 原版、`PeG-1` 变体、`OpenPG2` 全部原样）。
- 后续若要试跑 OpenGen 的 OPENPEG，**由用户操作**（我方严禁自行启动/点击游戏）；改动只限 `Settings.cfg` 的 `EFolder` 一行，随时可回滚。
