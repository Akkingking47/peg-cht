# -*- coding: utf-8 -*-
r"""把 pegww2/README.md 里的**历史踩坑档案**原样搬到 `方法/踩坑档案-W1至W23.md`，
README 只留「索引 + 现役内容」。（零手抄：按标记行切割，逐字搬迁。）

切割块（起止标记均为行首前缀匹配，前含后不含）：
  A   ### ⚠️ W20（实机三图发现        → ### 场景层批次账（每片 600 行
  B   ### ⚠️ 跨层地名一致性审计（W16   → ## 档案
  C   ### ⚠️ W19：描述框显示成          → | 文件 | 内容 |
  D   ### 踩坑档案（本项目新增，勿重蹈）  → ## exe 补丁

用法：python split_readme.py [--apply]
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WS = r"D:\DSH\军事游戏汉化"
RD = os.path.join(WS, "pegww2", "README.md")
OUT = os.path.join(WS, "pegww2", "方法", "踩坑档案-W1至W23.md")
APPLY = "--apply" in sys.argv

BLOCKS = [
    ("W20 实机三图：三类问题的定责与判据 + 番号展开收口（「表≠生效」）",
     "### ⚠️ W20（实机三图发现", "### 场景层批次账（每片 600 行"),
    ("W16 跨层地名一致性审计",
     "### ⚠️ 跨层地名一致性审计（W16", "## 档案"),
    ("W15 名栏被填成简报 · W17 整串键控 · W19 描述框双字段 · 场景选择画面核查",
     "### ⚠️ W19：描述框显示成", "| 文件 | 内容 |"),
    ("W1–W23 踩坑档案表",
     "### 踩坑档案（本项目新增，勿重蹈）", "## exe 补丁"),
]

raw = io.open(RD, encoding="utf-8").read().replace("\r\n", "\n")
lines = raw.split("\n")


def find(prefix, start=0):
    for i in range(start, len(lines)):
        if lines[i].startswith(prefix):
            return i
    raise SystemExit("未找到标记：%s" % prefix)


cuts, moved = [], []
for title, st, en in BLOCKS:
    i, j = find(st), find(en)
    cuts.append((i, j))
    moved.append((title, "\n".join(lines[i:j]).rstrip() + "\n"))
    print("块 [%s]  行 %d..%d（%d 行）" % (title[:26], i + 1, j, j - i))

body = "\n".join(t for _ti, t in moved)
head = """# PeG-WW2 踩坑档案（W1–W23）与历史裁定记录

> **本文件是 `../README.md` 的拆除产物**（2026-10-20 整理：README 收敛为索引，历史档案下沉到 `方法/`）。
> 内容**逐字搬迁，未改写**。**只在排查对应问题时才读**——日常上手读 `../README.md` 与 `../research/README.md` 即可。
> 结构：`W20/A′` 兵器名溢出处置 · 番号展开收口 · W16 跨层地名 · W15/W17/W19 名栏与描述框 · W1–W23 档案表。

---

"""
if APPLY:
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(head + body)
    keep = [ln for i, ln in enumerate(lines)
            if not any(a <= i < b for a, b in cuts)]
    # 在 place 处插入指针
    ptr = ["", "> ⭐ **踩坑档案 W1–W23 全文已迁至** [`方法/踩坑档案-W1至W23.md`](方法/踩坑档案-W1至W23.md)",
           "> （含 W15/W16/W17/W19/W20/A′ 与「表≠生效」番号教训；README 只留索引，避免上手即读 400 行）。", ""]
    pos = next(i for i, ln in enumerate(keep) if ln.startswith("### 场景层批次账"))
    keep = keep[:pos] + ptr + keep[pos:]
    io.open(RD, "w", encoding="utf-8", newline="\n").write("\n".join(keep))
    print("\n已写 %s（%d 行）" % (OUT, (head + body).count("\n")))
    print("README %d 行 → %d 行" % (len(lines), len(keep)))
else:
    print("\n(dry-run，未写文件；加 --apply 执行)")
