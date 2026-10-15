#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读探针：对指定英文键，打印它在词库各层的全部登记行 + 来源列（src/conf/scope），
用来确定「改哪里才不会被下一次重建覆盖」。

用法: python probe_src.py Kuri Morotsu Koenigsberg
"""
import io, os, sys

WS = r"D:\DSH\军事游戏汉化"
G = os.path.join(WS, "glossary")

TARGETS = [t.lower() for t in (sys.argv[1:] or ["Kuri"])]

FILES = [
    ("standard-glossary.tsv", os.path.join(G, "standard-glossary.tsv")),
    ("layers/common-glossary.tsv", os.path.join(G, "layers", "common-glossary.tsv")),
    ("layers/scope-glossary.tsv", os.path.join(G, "layers", "scope-glossary.tsv")),
    ("layers/common-drift.tsv", os.path.join(G, "layers", "common-drift.tsv")),
    ("layers/converge-list.tsv", os.path.join(G, "layers", "converge-list.tsv")),
    ("layers/faction-places.tsv", os.path.join(G, "layers", "faction-places.tsv")),
    ("layers/override.tsv", os.path.join(G, "layers", "override.tsv")),
    ("layers/scope-diff.tsv", os.path.join(G, "layers", "scope-diff.tsv")),
]


def norm(s):
    return s.strip().lower()


for name, p in FILES:
    if not os.path.exists(p):
        print(f"---- {name}: 缺失")
        continue
    n = 0
    hit = []
    hdr = None
    with io.open(p, encoding="utf-8-sig") as f:
        for ln in f:
            if not ln.strip():
                continue
            if ln.startswith("#"):
                if hdr is None:
                    hdr = ln.rstrip("\r\n")[:150]
                continue
            if hdr is None:
                hdr = ln.rstrip("\r\n")
                continue
            c = ln.rstrip("\r\n").split("\t")
            n += 1
            if any(norm(c[0]) == t for t in TARGETS):
                hit.append(c)
    print(f"---- {name}  数据行 {n}")
    if hdr:
        print(f"     表头: {hdr}")
    for c in hit:
        print("     " + " | ".join(c))
    if not hit:
        print("     (无命中)")
