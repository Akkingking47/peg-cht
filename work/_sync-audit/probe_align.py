# -*- coding: utf-8 -*-
"""对齐体检：对 95 条候选的每次出现，比较
   原文槽（backup/ORIGINAL-<efile>，cp1252） vs 中文槽（<efile>，gbk）的**分段数**。
段数不等 → 该槽的 en/zh 可能错位（先别定名，先查明）。只读。
"""
import collections
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
sys.path.insert(0, os.path.join(WS, "work", "efile-nashornpbem"))
from apply_residual import parse  # noqa

GAME = r"D:\OpenPG2"
BACK = os.path.join(WS, "backup")
TODO = os.path.join(WS, "work", "_sync-audit", "residual-names-todo.tsv")
OCC = os.path.join(WS, "glossary", "glossary-occ.tsv")


def read_tsv(p):
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        L = f.read().replace("\r\n", "\n").split("\n")
    head = L[0].split("\t")
    out = []
    for ln in L[1:]:
        if ln.strip():
            c = ln.split("\t")
            out.append({head[k]: (c[k] if k < len(c) else "") for k in range(len(head))})
    return out


want = set(r["en"] for r in read_tsv(TODO))
occ = collections.defaultdict(list)
for r in read_tsv(OCC):
    if r["en"] in want:
        occ[r["en"]].append(r)

cache = {}


def slot(root, efile, fn, g, idx, enc):
    key = (root, efile, fn)
    if key not in cache:
        p = os.path.join(root, efile, "SCENARIO", fn)
        if not os.path.exists(p):
            cache[key] = None
        else:
            data, items, meta = parse(p)
            t = {}
            if items:
                for gi, k, off, L in items:
                    t[(gi, k)] = (off, L)
            if meta and meta[0] is not None:
                t[(-1, 0)] = (meta[0], meta[1])
            cache[key] = (data, t)
    v = cache[key]
    if not v:
        return None
    data, t = v
    if (g, idx) not in t:
        return None
    off, L = t[(g, idx)]
    return data[off + 2:off + 2 + L].decode(enc, "replace")


bad = []
for r in read_tsv(TODO):
    en = r["en"]
    for o in occ[en]:
        if o["src"] != "xscn":
            continue
        efile = o["scope"]
        fn, gid = o["loc"].split("/", 1)[1].split(":")
        g, idx = gid[1:].split("#")
        g, idx = int(g), int(idx)
        a = slot(BACK, "ORIGINAL-" + efile, fn, g, idx, "cp1252")
        b = slot(GAME, efile, fn, g, idx, "gbk")
        if a is None or b is None:
            bad.append((en, o["loc"], "缺失", a, b))
            continue
        if a.count("/") != b.count("/"):
            bad.append((en, o["loc"], "段数 %d vs %d" % (a.count("/") + 1, b.count("/") + 1), a, b))

print("== 段数不等的出现（%d 处）==" % len(bad))
for en, loc, why, a, b in bad[:40]:
    print("   %-40s %-24s %s" % (en[:40], loc, why))
    print("        原=%r" % a)
    print("        中=%r" % b)
print()
print("== Bon. 系列原文槽实况 ==")
for fn, g, idx in (("GCN2.xscn", 1, 58), ("GCN2.xscn", 1, 61), ("GCN2.xscn", 1, 75),
                   ("GCN2.xscn", 1, 77), ("GCN4.xscn", 1, 78)):
    print("   %s g%d#%d  原=%r  中=%r" % (fn, g, idx,
          slot(BACK, "ORIGINAL-EFILE_OLGWW2", fn, g, idx, "cp1252"),
          slot(GAME, "EFILE_OLGWW2", fn, g, idx, "gbk")))
