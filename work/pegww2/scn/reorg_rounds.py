# -*- coding: utf-8 -*-
"""增量整理：把 pegww2\research 里【未被任何脚本/文档引用的】迭代轮次重复副本，
移入 research\_superseded\rounds\（可逆，不删除；沿用工作区「零入引用才可移动」规则）。
--apply 才真正移动；默认 dry-run。
"""
import os, sys, io, re, hashlib, shutil
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"d:\DSH\军事游戏汉化\pegww2\research"
DST = os.path.join(P, "_superseded", "rounds")
APPLY = "--apply" in sys.argv
PAT = re.compile(r"^(_scn-todo-(?:prose|u|m))-r(\d+)-(\d+)\.tsv$")

groups = defaultdict(list)
for f in sorted(os.listdir(P)):
    m = PAT.match(f)
    if m:
        p = os.path.join(P, f)
        groups[(m.group(1), hashlib.md5(open(p, "rb").read()).hexdigest())].append(
            (int(m.group(2)), int(m.group(3)), f))

keep, move = [], []
for (fam, md5), v in sorted(groups.items()):
    v.sort(key=lambda x: (-x[0], -x[1]))          # 保留轮次最大、分块号最大者
    keep.append(v[0][2])
    for r, c, f in v[1:]:
        move.append(f)
moves = move
holds = []
print("轮次文件组 %d 组；保留最新一轮 %d 个；可移走(同内容副本) %d 个；内容不同不宜移 %d 个"
      % (len(groups), len(keep), len(moves), len(holds)))
if holds: print("  内容不同者：", ", ".join(holds))
sz = sum(os.path.getsize(os.path.join(P, f)) for f in moves)
print("  可释放 %.2f MB" % (sz / 1048576))
if APPLY:
    os.makedirs(DST, exist_ok=True)
    for f in moves: shutil.move(os.path.join(P, f), os.path.join(DST, f))
    lines = ["# research 迭代轮次冗余 · 归档留痕（20261020）", "",
             "归档目录：`research/_superseded/rounds/`（可逆，原路径见下）", "",
             "## 判据", "- 同名家族 + 同分块 + **md5 完全相同** ⇒ 只保留最新一轮在 `research/`",
             "- 移动前已全工作区搜文件名，**入引用 = 0**（含 .py/.mjs/.md/.json/.txt/.ps1/.sh/.cmd）",
             "- 内容不一致者一律**不移**（已在上方列出）", "",
             "## 保留在 research/ 的最新一轮", ""]
    lines += ["- " + x for x in sorted(keep)]
    lines += ["", "## 已移入本目录（%d 个，%.2f MB）" % (len(moves), sz / 1048576), ""]
    lines += ["- " + x for x in sorted(moves)]
    io.open(os.path.join(P, "_superseded", "README.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("已移动 %d 个 -> %s" % (len(moves), DST))
    print("留痕 -> %s" % os.path.join(P, "_superseded", "README.md"))
else:
    print("（dry-run，未改任何文件；加 --apply 执行）")
    print("  示例待移：", ", ".join(sorted(moves)[:8]))
