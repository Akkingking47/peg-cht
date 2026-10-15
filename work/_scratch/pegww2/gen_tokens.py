# -*- coding: utf-8 -*-
"""生成待译清单：把非坐标行按「名称片段」归并，便于集中给译名。"""
import io, os, re, sys, collections

BASE = r"D:\DSH\军事游戏汉化"
SRC = os.path.join(BASE, r"pegww2\research\_scn-todo-m.tsv")
OUT = os.path.join(BASE, r"work\pegww2\_todo_tokens.py")

rows = []
with io.open(SRC, encoding="utf-8") as f:
    lines = f.read().split("\n")
for ln in lines[3:]:
    if ln.strip() == "":
        continue
    rows.append(ln.split("\t")[0])

coord_re = re.compile(r"^\((\d+),(\d+)\)\s*#(.*)$")
plain = []
for s in rows:
    m = coord_re.match(s)
    if m:
        plain.append(m.group(3))
    else:
        plain.append(s)

c = collections.Counter(plain)
uniq = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
with io.open(OUT, "w", encoding="utf-8") as g:
    g.write("# 自动生成：名称片段 -> 出现次数（共 %d 个片段 / %d 行）\n" % (len(uniq), len(rows)))
    g.write("TOKENS = [\n")
    for k, v in uniq:
        g.write("    (%r, %d),\n" % (k, v))
    g.write("]\n")
print("rows", len(rows), "uniq", len(uniq))
