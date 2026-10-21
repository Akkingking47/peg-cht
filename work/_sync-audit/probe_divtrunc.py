#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读探针：glossary/xscn-division-trunc.tsv 里本族 13 文件的全部命中行（逐段配对形态）。"""
import collections
import io
import os

WS = "D:/DSH/军事游戏汉化"
FILES = ("18days2.xscn", "18days3.xscn", "18days6.xscn", "18days7.xscn", "18days8.xscn",
         "18days11.xscn", "CanalAlbert.xscn", "GCN0.xscn", "GCN1.xscn", "GCN2.xscn",
         "GCN3.xscn", "GCN4.xscn", "GCN6.xscn")
p = os.path.join(WS, "glossary/xscn-division-trunc.tsv")
L = io.open(p, encoding="utf-8", errors="replace").read().replace("\r\n", "\n").split("\n")
print("总行=%d" % (len(L) - 1))
by = collections.defaultdict(list)
for ln in L[1:]:
    if not ln.strip():
        continue
    c = ln.split("\t")
    if c[0] in FILES and "第76" in ln:
        by[c[0]].append((c[1], c[2], c[3], c[4]))
for f in sorted(by):
    print("\n-- %s  %d 行" % (f, len(by[f])))
    for g, k, o, n in by[f]:
        print("   g%s#%-4s orig=%-38s now=%s" % (g, k, o, n))
