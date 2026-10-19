# -*- coding: utf-8 -*-
"""由 peg/research/scn-number.tsv 生成《场景列表-序号对照.md》（分组版）"""
import os

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


ROOT = WS
TSV = os.path.join(ROOT, r"peg\research\scn-number.tsv")
MD = os.path.join(ROOT, r"peg\research\场景列表-序号对照.md")

rows = []
for ln in open(TSV, encoding="utf-8-sig"):
    if ln.startswith("#"):
        continue
    p = ln.rstrip("\n").split("\t")
    if len(p) < 6:
        continue
    rows.append({"stem": p[0], "nn": p[1], "entry": int(p[2]),
                 "orig": p[3], "cur": p[4], "grp": p[5]})

single = sorted([r for r in rows if r["grp"] == "单人"], key=lambda r: r["nn"])
multi = sorted([r for r in rows if r["grp"] == "多人"], key=lambda r: r["nn"])

out = [
    "# PeG 场景列表 · 数字序号对照（2026-10-10 第 27 轮 · 分组版）", "",
    "## 为什么要编号",
    "",
    "场景列表的**显示名**取自 `<场景>_m.txt` 的第 [`.SCN`@offset4] 行（通常第 0 行）；",
    "列表**按显示名的字节序排序** ⇒ 名字全译成中文后按 GBK 码序排 ⇒ 与汉化前的英文顺序不同，看着乱。",
    "**解法**：显示名前加 `NN ` 前缀（`0-9` 的字节序在字母/汉字之前）⇒ 顺序完全可控。",
    "",
    "## 为什么要**分组**",
    "",
    "游戏主菜单有两个入口（官方 `Scenario Types.txt`）：",
    "",
    "| 菜单 | 命令 | 类型 | 收录 |",
    "|---|---|---|---|",
    "| **进行场景** | `Play A Scenario` | 人 vs 电脑 | **≤2 人**场景 |",
    "| **开始多人场景** | `Start A Multiplayer Scenario` | **2–4 名真人，无 AI** | **3–4 人**场景 |",
    "",
    "判据 ＝ `.SCN` **Player3 主国家字节（偏移 216）**：`0` ⇒ 单人组；`≠0` ⇒ 多人组。",
    "两个列表**分开显示**，因此**两组各自从 `01` 起编号**。",
    "编号依据 ＝ **该组内原英文名的字节序**（＝该组汉化前本来的顺序）。",
    "",
    "---",
    "",
    f"## 一、进行场景（单人组 / ≤2 人）· {len(single)} 个",
    "",
    "| 序号 | 列表显示名 | 原英文名 | 名字文件 |",
    "|---|---|---|---|",
]
for r in single:
    out.append(f"| **{r['nn']}** | {r['cur']} | `{r['orig']}` | `{r['stem']}_m.txt` |")
out += ["", "---", "", f"## 二、开始多人场景（多人组 / 3–4 人）· {len(multi)} 个", "",
        "| 序号 | 列表显示名 | 原英文名 | 名字文件 |", "|---|---|---|---|"]
for r in multi:
    out.append(f"| **{r['nn']}** | {r['cur']} | `{r['orig']}` | `{r['stem']}_m.txt` |")
out += ["", "---", "", "## 实现", "",
        "- 序号表：`peg/research/scn-number.tsv`（`stem \\t NN \\t entry \\t 原名 \\t 现名 \\t 组别`）",
        "- 序号分配：`work/peg/build_scn_number.py`（按 Player3 分组，组内按原名排序）",
        "- 落盘：`work/peg/gen_scn_zh.py` 生成 `<stem>_m.txt` 时给第 `entry` 行加 `NN ` 前缀（**大小写不敏感**）",
        "- 本文件生成：`work/peg/build_scn_list_doc.py`",
        "- 场景描述文件补写：`work/peg/gen_scn_desc_txt.py`（14 个只有 `.ply`、缺 `<名>.txt` 的附加包场景）",
        "- ⚠️ `.SCN`、`.ply` 均**无需改动**；改序号顺序 ⇒ 列表顺序随之变化。"]

open(MD, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print(f"已写 {MD}（单人 {len(single)} + 多人 {len(multi)}）")
