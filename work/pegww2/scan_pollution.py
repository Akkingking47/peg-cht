#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定位两类新问题：
  ① 「新译」污染：本该显示装备名/单位名的地方显示了「新译」（工作表「来源」列的值漏进了内容）
  ② 场景说明面板仍是英文（可能是我跳过/延后的文件，如 .ply）
"""
import os
import re

G = r"D:\Program Files\PeG-WW2"
WS = r"D:\DSH\军事游戏汉化"

print("=" * 96)
print("① 「新译」出现在哪些文件的哪些行（游戏目录，字节级）")
print("=" * 96)
nb = "新译".encode("gbk")
n_files = 0
for root, dirs, files in os.walk(G):
    for fn in files:
        p = os.path.join(root, fn)
        try:
            b = open(p, "rb").read()
        except Exception:
            continue
        if nb not in b:
            continue
        n_files += 1
        t = b.decode("gbk", "replace")
        for i, line in enumerate(re.split(r"\r\n|\r|\n", t)):
            if "新译" in line:
                print(f"  {os.path.relpath(p, G):40s} 行{i:<4d} {line.strip()[:56]!r}")
print(f"  共 {n_files} 个文件命中")

print()
print("=" * 96)
print("② 工作表/真源里「译文列 == 新译」的脏数据")
print("=" * 96)
for name in ("ww2-scn-map.tsv", "_scn-todo-m.tsv", "_scn-todo-u.tsv", "_scn-todo-prose.tsv"):
    p = os.path.join(WS, "pegww2", "research", name)
    if not os.path.isfile(p):
        continue
    n = 0
    for i, l in enumerate(open(p, encoding="utf-8-sig")):
        f = l.rstrip("\n").split("\t")
        if len(f) >= 3 and f[1].strip() == "新译":
            print(f"  {name}:{i+1} 原文={f[0][:44]!r}")
            n += 1
    if n:
        print(f"  → {name} 共 {n} 行 译文=='新译'")

print()
print("=" * 96)
print("③ 英文说明面板的来源：搜 'Hypothetical scenario where Germany'")
print("=" * 96)
for t in ("Hypothetical scenario where Germany", "Rise and Decline of the Third Reich"):
    enc = "latin-1"
    hits = []
    for root, dirs, files in os.walk(G):
        for fn in files:
            p = os.path.join(root, fn)
            try:
                b = open(p, "rb").read()
            except Exception:
                continue
            if t.encode(enc) in b:
                hits.append(os.path.relpath(p, G))
    print(f"  {t[:44]!r} → {hits[:6]}")

print()
print("=" * 96)
print("④ .ply 文件（此前**延后未译**的那批）")
print("=" * 96)
for root, dirs, files in os.walk(G):
    for fn in files:
        if fn.lower().endswith(".ply"):
            p = os.path.join(root, fn)
            print(f"  {os.path.relpath(p, G)}  {os.path.getsize(p)} B")
