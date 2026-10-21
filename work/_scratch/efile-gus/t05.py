# -*- coding: utf-8 -*-
"""Token-overlap candidate mining: glossary EQUIP entries sharing a token with batch srcs."""
import io, os, re, sys

ROOT = r"D:\DSH\军事游戏汉化"
GL = os.path.join(ROOT, "glossary", "standard-glossary.tsv")
batch = sys.argv[1]

rows = [l.split("\t") for l in io.open(GL, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n") if l.strip()]
gl = {}
for r in rows[1:]:
    if r[2] == "EQUIP":
        gl.setdefault(r[0], r)

srcs = []
for l in io.open(batch, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")[1:]:
    if l.strip():
        srcs.append(l.split("\t")[0])

def toks(s):
    return set(t for t in re.split(r"[^0-9A-Za-zÀ-ÿŁłŚłŻżŹźĆćŃńÓóĄąĘę–-]+", s) if len(t) > 2)

# token frequency: which Polish/generic tokens in the batch have a glossary answer
idx = {}
for en, r in gl.items():
    for t in toks(en):
        idx.setdefault(t, set()).add(en)

seen = set()
for s in srcs:
    for t in toks(s):
        for en in idx.get(t, ()):
            if en == s or (s, en) in seen:
                continue
            seen.add((s, en))
            g = gl[en]
            print("%s  >>  %s = %s [%s/%s]" % (s, en, g[1], g[4], g[6]))
