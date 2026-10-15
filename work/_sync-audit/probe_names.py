#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读探针：在两张**真源**表里找 docs/43 第三组 12 个键的现状。
  · PE G  地图真源 = peg\\research\\scenario-map.tsv
  · PeG-WW2 场景真源 = pegww2\\research\\ww2-scn-map.tsv
"""
import io, os, re, sys

WS = r"D:\DSH\军事游戏汉化"
TARGETS = ["kuri", "morotsu", "chio", "naikawa", "burnoshevo", "toro", "chiwagai",
           "okutai", "chingyong", "chinyong", "hatsutai", "acroma", "wolzskij", "volzhshiy"]
FILES = [
    ("PeG  scenario-map.tsv", os.path.join(WS, "peg", "research", "scenario-map.tsv")),
    ("WW2  ww2-scn-map.tsv", os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")),
]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.strip().lower())


for label, p in FILES:
    if not os.path.exists(p):
        print(f"---- {label}: 缺失 {p}")
        continue
    print(f"---- {label}")
    n = 0
    with io.open(p, encoding="utf-8-sig") as f:
        for i, ln in enumerate(f, 1):
            if not ln.strip() or ln.startswith("#"):
                continue
            c = ln.rstrip("\r\n").split("\t")
            n += 1
            if len(c) < 2:
                continue
            en = c[0]
            ne = norm(en)
            for t in TARGETS:
                if t in ne:
                    print(f"     L{i:<6d} en={en!r:34s} zh={c[1]!r}")
                    break
    print(f"     （数据行 {n}）")
