# -*- coding: utf-8 -*-
"""Query the project standard glossary for every src in a batch TSV."""
import io, os, sys

ROOT = r"D:\DSH\军事游戏汉化"
GL = os.path.join(ROOT, "glossary", "standard-glossary.tsv")
batch = sys.argv[1]
outp = sys.argv[2]

rows = [l.split("\t") for l in io.open(GL, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n") if l.strip()]
head, data = rows[0], rows[1:]

srcs = []
for l in io.open(batch, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")[1:]:
    if l.strip():
        srcs.append(l.split("\t")[0])

byen = {}
for r in data:
    byen.setdefault(r[0], []).append(r)

with io.open(outp, "w", encoding="utf-8", newline="\n") as f:
    for s in srcs:
        hits = byen.get(s)
        if hits:
            for h in hits:
                f.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (s, h[1], h[2], h[3], h[4], h[6]))
print("matched srcs:", sum(1 for s in srcs if s in byen), "of", len(srcs))
