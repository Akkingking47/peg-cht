#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读探针：bon76 收尾要定点同步的两个无生成器表的结构与命中行。
  1) glossary/xscn-division-trunc.tsv
  2) work/xscn-all-map.tsv
"""
import collections
import io
import os

WS = "D:/DSH/军事游戏汉化"


def load(rel):
    p = os.path.join(WS, rel)
    txt = io.open(p, encoding="utf-8", errors="replace").read().replace("\r\n", "\n")
    return p, txt.split("\n")


for rel in ("glossary/xscn-division-trunc.tsv", "work/xscn-all-map.tsv"):
    p, L = load(rel)
    print("=== %s  行数=%d ===" % (rel, len(L)))
    print("  表头: %s" % L[0].replace("\t", " | "))
    rows = [ln for ln in L[1:] if "第76" in ln]
    print("  含『第76』行数: %d" % len(rows))
    for ln in rows[:14]:
        print("     %s" % ln.replace("\t", " | "))
    if rel.endswith("all-map.tsv"):
        c = collections.Counter(ln.split("\t")[0] for ln in L[1:] if ln.strip())
        print("  文件列取值数=%d 样本=%s" % (len(c), c.most_common(6)))
    print()
