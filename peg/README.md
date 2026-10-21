# peg — 《People's General / 人民将军》(SSI 1998, *modgen* 引擎) 简中化子项目

> 工作区 `D:\DSH\军事游戏汉化` 的 **PeG 子项目归档**。对位上游参照 `pg-cht` 的 `pg2/`。
> **用途**：本作是用户研究 **「西方游戏文化渗透史」** 的对象 —— 一款「中国当侵略者」的美国 1998 年战略游戏。
> ⚠️ **仅供学习研究，请支持原版**；汉化只做语言转换，**不改原文世界观、阵营划分与叙事措辞**（保真优先）。
> 发布仓库：`https://github.com/Akkingking47/peg-cht`（本作与 PeG-WW2 同仓）。

## 一句话结论

PeG 是 **SSI 1998 年的 *modgen* 引擎 + DirectDraw 16bpp + GDI ANSI** 游戏，**文本 100% 外置**（exe 只硬编码文件名 stem）。
引擎**本有双字节代码路径但从未启用** —— 这就是一切乱码的**唯一根因**。打上 3 处 exe 补丁（字符集 / 字符类别表 / 代码页）
后中文全线正常，**英文零影响**。

**现状：已达可用状态** —— 1 个 exe ＋ 825 `.txt` ＋ 14 `.ply` ＋ 8 个 `.scn`（各 1 字节）；
界面、装备、人名、提示、场景简报、场景列表（61 项含分组序号）、列表描述框、日期**全部中文**。

**发布包**：`release/PeG-汉化包-20261021.zip`（0.6 MB，661 个文件）—— 解压覆盖原版目录即可游玩，
内含 `PeG030.exe`、根级文本、`Scenario/`·`Userscen/` 文本与 8 个 `.scn` 标志；详见仓库根 README §一之二。

## 档案

| 文件 | 内容 |
|---|---|
| **[方法/PeG汉化经验总结.md](方法/PeG汉化经验总结.md)** | ⭐⭐⭐ **本项目最重要的一份** —— 技术发现（分层）＋ 11 条踩坑档案 ＋ 可迁移方法论 ＋ 术语文风 ＋ 工具链 ＋ 可复用清单 |
| [research/README.md](research/README.md) | 研究档案说明（文化渗透研究的目的 / 填证规范 / 关键定位速查 / 复算方式） |
| [research/observations.tsv](research/observations.tsv) | ⭐ 观察主表（56 行：原文＋出处＋定位已预填，译文待填） |
| [research/ui-glossary.tsv](research/ui-glossary.tsv) | ⭐⭐ UI 军事术语表 v1.2（Gate-1 术语资产；含**禁用黑名单**，生成器会扫描拦截） |
| [research/术语平衡口径.md](research/术语平衡口径.md) | ⭐⭐ 「军事感 × 玩家可读性」双轨制口径（参照《装甲军团2》官方中文） |
| [research/各国军语风格口径.md](research/各国军语风格口径.md) | ⭐⭐ **文风总纲**：先判文体再定语域 · 意象成链 · 三重诊断表 · 8 段样本 |
| [research/部队编制译法口径.md](research/部队编制译法口径.md) | 单位＝团级（实测 ≈3.78 km/格）；中国＝团营／日本＝联队大队 |
| [research/1979后中国军事文书范本.md](research/1979后中国军事文书范本.md) | 语料（**仅用于命令/战报两格**） |
| [research/官方繁中版《解放軍之怒》译法考.md](research/官方繁中版《解放軍之怒》译法考.md) | ⭐ 官方繁体中文版考古（**一手材料**，见下 §四） |
| [research/同类游戏UI术语对照.md](research/同类游戏UI术语对照.md) | PG2 / Pacific General / 官方繁中版 三家 UI 术语对照 |
| [research/场景列表-序号对照.md](research/场景列表-序号对照.md) | 61 个进列表场景 × 分组序号 × 原文名 |
| `research/scenario-long-zh.tsv` | 长段落译文表（**541 条**，整行直出） |
| `research/Equip30-中英对照.txt` · `Gui030-中英对照.txt` | 装备 573 条 / 界面 653 行的中英对照 |
| [research/evidence/](research/evidence/) | 原始素材（由脚本生成，可复算） |
| `testbed/` | **备份与试作**（见 §三 备份链） |
| `../../work/peg/` | 全部脚本（补丁 / 生成器 / 分析） |

## 现况（2026-10-10）

| 核心问题 | 结论 |
|---|---|
| 中文能不能显示 | ✅ **能** —— 3 处 exe 补丁：`iCharSet`→GB2312 · `_pctype` 高字节区→`0x8040` · `__mbcodepage`→936 `[已实测]` |
| 文字存在哪 | exe 只硬编码 stem（`gui030/Equip30/misc030/name030/tips030`）；其余全为纯文本 `[已实测]` |
| 场景列表名从哪来 | `<场景>_m.txt` 第 `[.SCN@4]` 行（**不是** `.ply` 首行、**不是** `@11329` 的 `.txt`，双重实证）`[已实测]` |
| 列表描述框从哪来 | **`.ply`**（定长 501 B、NUL 填充；**第 0 行必须是标题**）`[已实测]` |
| 开局简报从哪来 | `.SCN@11329` 指向的 `<名>.txt`，**目录/扩展名由 `@11349` 决定**（`0`＝Scenario `.TXT`／`1`＝Userscen `.PLY`）`[已实测]` |
| 为什么有的场景不进「进行场景」 | `.SCN` **Player 3 主国家 `@216` ≠ 0** ⇒ 3–4 人 ⇒ 归**「开始多人场景」**（非 bug）`[已实测]` |
| 日期为什么改 exe 无效 | 日期由 **Windows `GetDateFormatA`** 生成，LCID 取自全局 `0x499148`（初值 9＝英文）`[已实测]` |
| 编码 | 出稿 **GBK(936) ＋ 无 BOM ＋ 沿用原文换行**；拆行须 `(\r\n\|\r\|\n)` 三态（可能有裸 CR）`[已实测]` |

**规模**：`.txt` 825（Scenario 797 ＋ Userscen 28）· `.ply` 14 · `.scn` 213（进列表 61）·
长段落译文 541 条 · 装备 573 条。

**剩余（非阻塞）**：口径保留项（武器型号 / 舰名前缀 / 元数据 `dummy`·`Equipment:`）。

## 工具链速查

```bash
cd D:/DSH/军事游戏汉化
PY=C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe

# —— exe 补丁（幂等；默认 dry-run，--apply 才写）——
$PY work/peg/patch-mbcs.py            # ① 中文显示治本（三项）
$PY work/peg/patch-date-lcid-zh.py    # ② 日期 LCID → zh-CN（真正生效的一刀）
$PY work/peg/patch-lc-time-zh.py      # ③ CRT lc_time 月份/星期表（实测无效，无害保留）

# —— 文本生成器（读 testbed/backup/ 的原文 ⇒ 产出到 testbed/）——
$PY work/peg/gen_peg_text.py Equip30 [deploy]   # 装备/misc/tips（通用）
$PY work/peg/gen_gui030_zh.py                   # 界面（产出后手工拷入游戏）
$PY work/peg/gen_name030_zh.py                  # 人名
$PY work/peg/gen_scn_zh.py build|deploy|verify  # 场景 .txt
$PY work/peg/gen_ply_zh.py  build|deploy        # 场景描述框
$PY work/peg/gen_scn_desc_txt.py                # 补场景开局简报 .txt

# —— 场景列表维护 ——
$PY work/peg/build_scn_number.py                # 分配分组序号（单人 01–51 / 多人 01–10）
$PY work/peg/build_scn_list_doc.py              # 生成对照文档
$PY work/peg/fix_scn_intro_flag.py [--apply]    # 修 .SCN@11349 位置标志（每场景 1 字节）
```

## 边界与纪律

- **本归档不含游戏本体的受版权保护内容**；`research/` 内引用原文仅为研究定位所需。
- **绝不覆盖改原文**；备份与覆盖**分两条命令**；**先重建到临时 → 回读校验 → 才写正式**。
- 需要截图时**停下告知，由用户手动截取**；**严禁自行启动/点击游戏**。
- `D:\Program Files\PeG` 内**原文零改动**（除已登记的三处 exe 补丁与 8 个 `.scn` 各 1 字节）。
