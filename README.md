# peg-cht · 《People's General》简体中文汉化工程

> SSI 1998 年军事战略游戏 ***People's General***(人民将军)的**汉化工具链 ＋ 译文真源 ＋ 技术档案**。
>
> ⚠️ **本仓库不含游戏本体与原始文本文件**。两种用法：
> ① **直接用成品** —— 下载 [`release/`](release/) 下的汉化包，解压覆盖到你自己的游戏副本（见 [§三之二](#三之二发布包解压即可)）；
> ② **自己复算** —— 在自己的游戏副本上跑 [§四 使用流程](#四使用流程复算) 里的脚本。

---

## 项目说明（缘起与鸣谢）

### 这个版本从哪来

本汉化针对的是 **[peoplesgeneral.de](https://www.peoplesgeneral.de/)** 上的 *People's General* 版本 ——
二十多年过去，这里仍是资料最全、且**仍在维护**的 PeG 站点。

> **感谢 Michael** —— 感谢他一直更新与维护这个网站。一款 1998 年的老游戏到今天还有这样一个活的据点，
> 是件不容易的事；我的游戏副本、文件格式资料、社区 e-file，源头都在那里。

### 关于 MOD

本工程的工具链不只服务原版，也覆盖 **PeG 的二战 MOD（PeG-WW2）** —— 那部分归档暂未并入本仓库。

> **感谢 Robert Mary** —— PeG-WW2 二战 MOD 的制作者。我们的研究档案里到处是他的署名：
> `PeGWW2 conversion: Robert Mary`、`Campaign design: Robert Mary`、`Equipment: REDrake and Robert Mary e-file`。
>
> **也要感谢 Redball** —— 社区 e-file（`REDBALL'S E-FILE 3.0`）与 PeG-WW2 2.7c 引擎修改的作者；
> 中文界面里还留着他那句 `Redball Says Hi!`。

没有这些持续二十年的社区劳动，就没有可供汉化的素材 —— 这份汉化只是站在他们肩膀上的**语言转换**。

### 为什么做这个

我玩这款游戏很多年了。

二十多年前它是全英文的：对着满屏军事术语查词典、半猜半玩，剧情只能看个大概。
如今可以借助 **AI** 把整套文本、术语、口径系统地梳理一遍 —— 译法能对齐、能被复核、能被复算，
老游戏终于能用母语重新读一遍。**对我而言，这件事本身就足够让人高兴。**

### 关于参照的那份汉化工程

**[wicanr2/pg-cht](https://github.com/wicanr2/pg-cht)** —— 《装甲元帅 2 / Panzer General II》的繁中化工程。
**我们参考了它，作为汉化 PeG 的助力。** PeG 与 PG2 同为 SSI 战棋；更有意思的是，
pg-cht 自己的手册开头就点明 **「首要目標兄弟作 ＝ 解放軍之怒 (People's General, SSI 1998, 同引擎)」** ——
也就是说，它本来就把 PeG 当成同引擎的姊妹作来规划。具体参考了这些：

| 参考项 | 我们怎么用 |
|---|---|
| **Phase-0 四步引擎确认法** —— ① 导入表 ② 建置路径串定位项目代号 ③ 字体格式逐 byte 核对 ④ 语言槽 | 照此确认 modgen 引擎：**静态 CRT**（无 MSVCRT）· **DirectDraw** · 项目代号 `C:\modgen\main\Src\*.c`（37 个模块）—— 见 [`docs/74`](docs/74-pg-cht机制映射与modgen施行表.md) |
| **两条纪律** —— 「机制可移植，绝对地址不可移植」＋「一次只加一处补丁，改完先 dry-run，随时一键回退」 | 落成我们的**补丁三纪律**：幂等 · 默认 dry-run · 等长替换优先；每个地址都在本机 `PeG030.exe` 上重新量 |
| **可迁移的补丁手法** —— `_pctype` 表 **repoint**（不覆写原表）· 先找量测/换算的**唯一收敛点**再改，不逐点打 · descriptor 表数据 patch 改固定几何 · **IAT 动态插桩写日志**（零断点） | 我们的字符类别表补丁照 repoint 思路做；坐标换算走收敛点定位；被反调试打死断点路线后改用动态插桩 |
| **踩坑档案** —— Chesterton fence（改共用表前先枚举全部 caller）· 需求相反时应 **clone** 而非全局改 · 「按原生尺寸写死的固定几何值」是**一整族** · 静态推理到顶就要动态定案 | 直接当预警清单用 —— 我们后来撞的雷，它基本都预先记着 |
| **分层归档方式** —— `方法/`（经验）＋ `research/`（术语/证据）＋ `testbed/`（备份试作），凡结论**可复算** | 本仓库的目录骨架即照此搭建 |
| **工具清单** —— capstone 反汇编、PE 节表检查、caller 枚举、xref | 我们的 `work/peg/` 分析脚本一族（`d.py` / `xref_*.py` / `find_calls.py` …） |

> 双方路线一致：**没有源码，不做全量反编译**，只做「**机制级外科补丁**」。

再次感谢上面三位（Michael · Robert Mary · Redball）与 pg-cht 的作者 ——
**这份工程的起点，是别人已经铺好的路。**

---

## 一、一句话结论

PeG 是 SSI 1998 年 ***modgen*** 引擎 ＋ DirectDraw 16bpp ＋ GDI **ANSI** 的游戏，**文本 100% 外置**
（exe 里只硬编码了文件名 stem）。引擎**本有双字节代码路径，但从未启用** ——
这是中文显示为乱码的**唯一根因**。

打上 **3 处 exe 补丁**（字符集 / 字符类别表 / 代码页）后，中文全线正常，**英文零影响**：

| # | 补丁位 | 改什么 | 结果 |
|---|---|---|---|
| ① | `iCharSet` | → `GB2312_CHARSET(134)` | 字体按中文选字形 |
| ② | `_pctype` 高字节区 | → `0x8040` | 中文双字节不再被当成两个 ASCII |
| ③ | `__mbcodepage` | → `936` | CRT 多字节转换走 GBK |

---

## 二、现在能做到什么程度

| 层 | 状态 |
|---|---|
| 界面 | ✅ `Gui030.txt` 653 行全中文（含按钮、标签、对话框） |
| 装备 | ✅ `Equip30.txt` 573 条（名称 / 属性说明） |
| 人名 | ✅ `name030.txt` |
| 提示 | ✅ `tips030.txt` · `misc030.txt` |
| 场景简报 | ✅ `.SCN@11329` 指向的 `<名>.txt` 全中文（541 条长段落） |
| 场景列表 | ✅ 61 项进列表，含分组序号（单人 01–51 / 多人 01–10） |
| 列表描述框 | ✅ `.ply`（定长 501 B、NUL 填充） |
| 开局日期 | ✅ 走 Windows `GetDateFormatA`，已改 LCID → zh-CN |

**规模**：`.txt` 825（Scenario 797 ＋ Userscen 28）· `.ply` 14 · `.scn` 213（进列表 61）·
长段落译文 541 条 · 装备 573 条。

**出稿编码**：**GBK(936) ＋ 无 BOM ＋ 沿用原文换行**。拆行必须按 `(\r\n|\r|\n)` **三态**处理 ——
老引擎的行尾可能是**裸 CR**。

**未做（非阻塞）**：武器型号 / 舰名前缀 / 元数据（`dummy`、`Equipment:`）等口径保留项。

> **PeG-WW2（二战 MOD）**：同引擎、独立正文，规模约为本作 4 倍 ——
> 界面 5 层全量、场景 **21,865 条唯一行 / 3,798 个文件**、番号 6,414 行已按史实 OOB 校正；
> exe 三补丁与 PeG030 逐字节同源，1:1 复用。详见 [§五之二](#五之二peg-ww2踩坑历程与迭代方法)。

---

## 三、目录结构

```
peg-cht/
├── peg/                        本作归档
│   ├── README.md               本作索引与现状
│   ├── 方法/
│   │   └── PeG汉化经验总结.md   ⭐ 技术发现 ＋ 11 条踩坑档案 ＋ 可复用清单
│   ├── research/               研究档案与译文真源
│   │   ├── ui-glossary.tsv     UI 军事术语表（含禁用黑名单，生成器会扫描拦截）
│   │   ├── *-map.tsv           文本映射表（键 ⇥ 译文；生成器的输入）
│   │   ├── gui030-zh.tsv       Gui030 行级对照表
│   │   ├── scenario-long-zh.tsv 场景长段落整行译文
│   │   ├── scn-number.tsv      61 个进列表场景 × 分组序号
│   │   ├── observations.tsv    研究观察主表
│   │   └── *.md                译法口径（术语平衡 / 各国军语 / 部队编制 / 繁中版考古 …）
│   └── testbed/                试作与诊断脚本（含早期 exe 补丁脚本）
├── pegww2/                     二战 MOD 归档
│   ├── README.md               本作索引与现状
│   ├── 方法/                   踩坑档案-W1至W23.md · 资产治理与索引规范.md
│   ├── research/               真源 / _derived 派生物 / _superseded 历史
│   └── testbed/                原文备份 + 构建产物 out/
├── release/                    ⭐ 成品汉化包（解压覆盖即可玩）
├── work/peg/                   ⭐ 全部生产脚本（补丁 / 生成器 / 分析）
├── work/pegww2/                MOD 生产脚本（scn 生成/部署、番号、旗帜）
├── work/glossary/              词库入库与双门校验
├── docs/                       技术档案
│   ├── 73-PeG030反编译作业图（模块-工具链-路线）.md
│   └── 74-pg-cht机制映射与modgen施行表.md
├── env.cmd                     环境注入（改解释器路径即可用）
└── requirements.txt            依赖清单
```

---

## 三之二、发布包（解压即可）

`release/` 下提供**解压覆盖原版目录即可游玩**的成品包，不需要运行脚本：

| 包 | 文件 | 大小 | 内容 |
|---|---|---|---|
| PeG | `release/PeG-汉化包-20261021.zip` | 0.6 MB | `PeG030.exe`（中文补丁）+ 装备/界面/人名/提示 + Scenario/Userscen 文本 + 8 个 `.scn` 标志 |
| PeG-WW2 精简版 | `release/PeG-WW2-汉化包-精简版-20261021.zip` | 4.5 MB | 3,703 场景文本 + 根目录文本 + 12 个中文 exe |
| PeG-WW2 完整版 | `release/PeG-WW2-汉化包-完整版-20261021.zip` | 77.7 MB | 上述全部 + `WW2GEN.dat`（史实德国旗），建议走 Release 资产 |

安装：先备份游戏目录 → 按目录结构覆盖 → 启动对应 exe。包内附 `安装说明.txt` 与 `文件清单.txt`；
还原：用备份覆盖回来即可。详见 [`release/README.md`](release/README.md)。

> ⚠️ 包内含游戏 exe 与数据文件，公开分发前请确认原游戏/MOD 授权；仓库默认只跟踪小包，
> 完整版与 77 MB 级资产请走 GitHub Release。

---

## 四、使用流程（复算）

### 0. 前置

| 项 | 要求 |
|---|---|
| 游戏 | 自备 ***People's General***(SSI 1998) 副本，装到任意目录 |
| Python | Python 3.9+（作者本机为 3.14）。依赖见 `requirements.txt` |
| 编码 | Windows 中文环境；脚本内部已强制 `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8` |

设置两个环境变量（脚本的**唯一路径真源**，缺省值＝作者本机布局）：

```bat
set PEG_GAME=D:\Program Files\PeG        :: 你的游戏目录
set PEG_WORKSPACE=D:\path\to\peg-cht     :: 本仓库克隆目录
```

> 也可以用 `env.cmd`（先把里面 `PY=C:\Python314\python.exe` 改成你本机的解释器）。

### 1. 备原文（脚本的真源）

**脚本不直接改游戏里的活文件**，而是读 `peg/testbed/backup/` 下的原文备份、
产出成品到 `peg/testbed/`，最后才部署。所以第一步是把游戏里的原文**按原结构**拷一份进去：

```bat
mkdir peg\testbed\backup
xcopy /S /Y "%PEG_GAME%\Scenario\*.txt"  peg\testbed\backup\Scenario\
xcopy /S /Y "%PEG_GAME%\Userscen\*.ply"  peg\testbed\backup\Userscen\
copy /Y "%PEG_GAME%\Gui030.txt"   peg\testbed\backup\
copy /Y "%PEG_GAME%\name030.txt"  peg\testbed\backup\
copy /Y "%PEG_GAME%\Equip30.txt"  peg\testbed\backup\
copy /Y "%PEG_GAME%\misc030.txt"  peg\testbed\backup\
copy /Y "%PEG_GAME%\tips030.txt"  peg\testbed\backup\
```

### 2. 打 exe 补丁

```bat
python peg\testbed\patch-mbcs.py            ① 中文显示治本（三项，产出 PeG030zh.exe）
python work\peg\patch-date-lcid-zh.py       ② 日期 LCID → zh-CN
python work\peg\patch-lc-time-zh.py         ③ CRT lc_time 月份/星期表
```

三个补丁都是**幂等**的，且**默认 dry-run**，加 `--apply` 才真正写入。
第 ① 个会先比对 `PeG030.exe.orig-backup` 的 md5 再动手。

### 3. 生成文本

```bat
python work\peg\gen_gui030_zh.py               界面
python work\peg\gen_name030_zh.py              人名
python work\peg\gen_peg_text.py Equip30        装备（另有 misc030 / tips030）
python work\peg\gen_scn_zh.py build            场景 .txt → peg\testbed\scn-zh\
python work\peg\gen_ply_zh.py build            场景描述框 .ply
python work\peg\gen_scn_desc_txt.py            补场景开局简报 .txt
python work\peg\build_scn_number.py            分配分组序号
```

### 4. 部署

```bat
python work\peg\gen_scn_zh.py deploy           场景 .txt
python work\peg\gen_ply_zh.py deploy           描述框 .ply
python work\peg\gen_scn_zh.py verify           回读校验
python work\peg\fix_scn_intro_flag.py --apply  修 .SCN@11349 位置标志（每场景 1 字节）
```

> ⚠️ **先重建到临时 → 回读校验 → 才写正式**；备份与覆盖**分两条命令**，绝不覆盖改原文。

---

## 五、技术要点（为什么能汉化）

| 问题 | 结论 |
|---|---|
| 文字存在哪 | exe 只硬编码文件名 stem（`gui030/Equip30/misc030/name030/tips030`），其余全是外置纯文本 |
| 场景列表名从哪来 | `<场景>_m.txt` 的 `[.SCN@4]` 行 —— **不是** `.ply` 首行，也**不是** `@11329` 指的 `.txt`（双重实证） |
| 列表描述框从哪来 | **`.ply`**（定长 501 B、NUL 填充；**第 0 行必须是标题**） |
| 开局简报从哪来 | `.SCN@11329` 指向的 `<名>.txt`，目录/扩展名由 `@11349` 决定（`0`＝`Scenario/*.TXT`／`1`＝`Userscen/*.PLY`） |
| 为什么有的场景进不了「进行场景」 | `.SCN` 的 Player 3 主国家 `@216 ≠ 0` ⇒ 3–4 人 ⇒ 归「开始多人场景」（**不是 bug**） |
| 日期为什么改 exe 数据无效 | 日期由 Windows `GetDateFormatA` 生成，LCID 取自全局 `0x499148` |

完整版见 [`peg/方法/PeG汉化经验总结.md`](peg/方法/PeG汉化经验总结.md)（含 11 条踩坑档案）。

### 踩坑公示（选摘）

1. **cp1252 假汉字会骗过校验** —— 裸 `decode('gbk')` 把高字节解成「假汉字」；
   可靠判据是 **GB2312 字节范围 ＋ 逐文件假汉字黑名单**。
2. **别全量翻译脚本/说明类文件** —— 行内替换会污染游戏脚本，必须建**整文件排除清单**。
3. **不改 exe 前先查导入表** —— 见到 `GetDateFormatA`/`GetLocaleInfoA` ⇒ 文本来自 Windows，改 exe 数据无用。
4. **中文字体缺字**：字库不全时缺字位置会「吃掉」相邻字符，必须实测格宽与行数，**不靠肉眼**。

---

## 五之二、PeG-WW2：踩坑历程与迭代方法

> PeG-WW2 是 PeG 的二战 MOD（Redball 2005），**与 PeG030 同一 exe 构建** ⇒ 三处双字节补丁可 1:1 复用。
> 但正文体量约为本作 4 倍（21,865 条唯一行 / 3,798 个文件），场景层与番号层的坑几乎都出在这里。
> 完整档案见 [`pegww2/方法/踩坑档案-W1至W23.md`](pegww2/方法/踩坑档案-W1至W23.md)。

### 迭代时间线（W1 → W24）

| 轮次 | 目标 | 关键结论 |
|---|---|---|
| W1–W6 | 立骨架 | 12 个 efile 与原版构建一致 ⇒ 补丁 1:1；文本 100% 外置，exe 只硬编码文件名 stem |
| W7–W12 | 场景层 | `_m` 行 0＝显示名、行 1+＝该场地名；`_i`＝简报；`.TXT` 行 0 常被别的场景借用 |
| W13–W18 | 名栏/简介 | 名栏与说明冲突分三类；逐战役 `.CAM` 槽位走查，防止简报污染漏检 |
| W19–W23 | 番号层 | `.SCN` 单位块 S0=11350 / 65 B；`+36` 国籍；链路位次补规模词；词库双门 |
| W24 | 旗帜 | `WW2GEN.dat` 容器手术：RLE 帧替换 + blob 重排 + 目录偏移补丁 |

### 踩过的坑（选摘）

1. **「简介变成部队番号 / 地名集」** —— 引擎按 `<场景>_i.txt` 找简报，命名不匹配就回退显示 `_m` 内容。
   `Usvsussr` 19 场是「无下划线」命名，须同时给两种命名格式。
2. **`_m` 行 0 才是显示名**，行 1+ 是该场**自己的**地名字标 —— 同一张 `.MAP` 可被不同战区复用，地名各不相同。
3. **名栏 ≠ 说明**，须分三类：同源异写（不改）· 名栏借用（按说明名改）· 说明借用（保留名栏）。
   「行动代号 ↔ 目标地名」是合法成对，不是错配。
4. **`.SCN` 没有年份字段**（648/648 验证 0 命中）；年代取场景简报日期，否则取所属战役年代众数。
5. **`_u` 对齐**：行 i ↔ 单位 i；行 0＝`Dummy` 时整体错一行；边界有 ±12 行噪声；孤儿 `_u` 是死内容。
6. **番号国别不能按战役推** —— 按 `.SCN +36` 逐单位精确国籍（曾改判约 2000 行；例如 `[XIII]` 是英军军部，不是德军罗马军）。
7. **缩写跨时代同形不同义**：`GD` 早期＝近卫师、后期＝大德意志；`AF` 42–43＝第 4 航空队、44–46＝第 9 空军。
8. **裸数字链必须补规模词**：2 段＝团/师；`NNR/35R` 的 R＝Reserve（预备师），不是 Regiment（团）。
9. **无确证的字母码一律保留**：`RA / IA / RM / SA / 3/R / 19C / 5HA` 等不硬解，宁可留原文，不做半译。
10. **词库是双门**：`check_glossary.py`（跨层术语一致）＋ `layer_gate.py --full`（层表↔词库完整性）；
    改层表后必须 `ingest_layers.py --apply`，否则门报「缺失」并拒绝构建。
11. **`WW2GEN.dat` 三坑**：①「原偏移＝旧 EOF」的哨兵条目跨次重排会被二次补丁；
    ②就地写入勿把已编码 RLE 当像素再编码一次；③回读期望偏移须用「尺寸增量累计」，不能用绝对位移差。
12. **整份 `_u` 拿错**（Fi02）：单位名单与另一场景逐行全等，**备份即错** ⇒ 先比对再决定改文本还是改国籍，不要先动 `.SCN`。

### 怎么继续迭代（固定流水线）

> 铁律：**只改真源，不直接改成品**；每一步都回读校验，失败即停。

```bat
:: 0) 环境
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

:: 1) 改真源：ww2-scn-map.tsv / 层表 / _scn-file-overrides.tsv

:: 2) 重算番号对照表，并把已裁定结果收口进真源
python work\pegww2\scn\gen_desig_table.py
python work\pegww2\apply_desig_closure.py --apply

:: 3) 层表入库 ＋ 双门
python work\glossary\ingest_layers.py --apply
python work\glossary\layer_gate.py --full
::    另按 glossary/README 的目标目录运行 check_glossary.py

:: 4) 构建（五道校验，任一失败该文件拒绝落盘）
python work\pegww2\gen_scn.py build

:: 5) 部署（先备份原文，再覆盖，再回读 sha）
python work\pegww2\deploy_scn.py --apply

:: 6) 回归
python work\regression.py
```

**发布迭代**：小包（PeG 0.6 MB、WW2 精简 4.5 MB）随仓库跟踪；含 `WW2GEN.dat` 的完整版
（77.7 MB）走 GitHub Release 资产。打包清单由「备份 vs 游戏目录逐文件 sha 比对」生成，不手写。

### 相关文档

- 踩坑全档：[`pegww2/方法/踩坑档案-W1至W23.md`](pegww2/方法/踩坑档案-W1至W23.md)
- 资产分层：[`pegww2/research/README.md`](pegww2/research/README.md)（真源 / `_derived` / `_superseded`）
- 脚本与口径：[`work/pegww2/scn/README.md`](work/pegww2/scn/README.md)

---

## 六、作业纪律

1. **绝不覆盖改原文**；备份与覆盖分两条命令；先重建到临时 → 回读校验 → 才写正式。
2. **补丁三纪律**：幂等 · 默认 dry-run（`--apply` 才写）· 等长替换优先。
3. **不靠肉眼不靠猜** —— 编码、字体、格宽、行数全部实测或用脚本复算。
4. **结论被推翻时写明撤回原因**（防止下一轮重蹈）。

---

## 七、版权与免责声明

- ***People's General*** 及其全部游戏内容、商标、素材的版权归 **Strategic Simulations, Inc. (SSI) / 现权利方**所有。
  本仓库**与权利方无任何关联，未获其授权或背书**。
- 本仓库**不提供、不包含**游戏本体、地图/场景原始数据或原始文本文件。
  `release/` 成品包内含**已打中文补丁的可执行文件**与译文文本，仅用于已合法持有游戏副本的用户做本地替换；
  `peg/research/` 下的对照表为**汉化定位所必需的最小引用**（翻译映射以原文串为键），
  其著作权仍属原权利方；**下载者请仅用于个人学习/研究**。
- 本仓库中的**脚本、方法论文档、术语口径与译文**是译者本人的工作成果。
- 使用者须**自行持有合法获得的游戏副本**。因使用本仓库内容产生的一切后果由使用者自负。
- 若权利方对本仓库有异议，请开 issue，**会立即移除相关内容**。

---

## 八、许可

| 内容 | 许可 |
|---|---|
| 脚本 / 工具（`work/`、`peg/testbed/` 下的代码） | [MIT](LICENSE) |
| 译文、术语表、译法口径与方法论文档 | [CC BY-NC-SA 4.0](LICENSE-DATA) |

游戏本体内容不在授权范围内（见 §七）。
