#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单位属性面板（概况）取证：面板字段来自哪一层、原文/译文长度对比。"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
BKT = os.path.join(WS, "pegww2", "testbed", "backup", "text")

print("=" * 96)
print("① UI 层里和「概况 / 兵力 / 工事」相关的行（含原版对照）")
print("=" * 96)
for name in ("WW2Gui.txt", "WW2Misc.txt", "WW2Tips.TXT"):
    cur = os.path.join(G, name)
    bak = os.path.join(BKT, name)
    if not os.path.isfile(cur):
        continue
    c = open(cur, "rb").read().decode("gbk", "replace").split("\n")
    b = open(bak, "rb").read().decode("latin-1").split("\n") if os.path.isfile(bak) else []
    for i, line in enumerate(c):
        if any(k in line for k in ("概况", "兵力", "工事")):
            o = b[i].rstrip("\r") if i < len(b) else "(无对照)"
            print(f"  {name}:{i:4d}  原={o[:44]!r}")
            print(f"  {'':14s}  中={line.rstrip()[:44]!r}")

print()
print("=" * 96)
print("② 「新泽西」在真源与文件里的情况")
print("=" * 96)
MAP = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")
for i, l in enumerate(open(MAP, encoding="utf-8-sig")):
    if i < 4 or not l.strip():
        continue
    f = l.rstrip("\n").split("\t")
    if len(f) >= 3 and "新泽西" in f[1]:
        print(f"  真源: 原文={f[0][:44]!r}")
        print(f"        译文={f[1][:44]!r}  类={f[2][:24]}")

print()
print("=" * 96)
print("③ 面板里那串「新泽西」出现在哪些场景文件")
print("=" * 96)
nb = "新泽西".encode("gbk")
for root, dirs, files in os.walk(os.path.join(G, "SCENARIO")):
    for fn in files:
        p = os.path.join(root, fn)
        try:
            bb = open(p, "rb").read()
        except Exception:
            continue
        if nb in bb:
            t = bb.decode("gbk", "replace")
            for i, line in enumerate(t.split("\n")):
                if "新泽西" in line:
                    print(f"  {fn}:{i} {line.strip()[:64]!r}")
