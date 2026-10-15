#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""战役层取证：*camp.txt 是战役名/描述所在，且「克列迪道山口」不在任何文件里（要查清来源）。"""
import os
import re

G = r"D:\Program Files\PeG-WW2"
BK = r"D:\DSH\军事游戏汉化\pegww2\testbed\backup\SCENARIO"

print("=" * 96)
print("① *camp.txt 清单 + 第 0 行（疑似战役名）")
print("=" * 96)
camps = []
for d in ("SCENARIO", "USERSCEN"):
    p = os.path.join(G, d)
    if os.path.isdir(p):
        for f in sorted(os.listdir(p)):
            if "camp" in f.lower() and f.lower().endswith((".txt", ".tx", ".t")):
                camps.append((d, f))
print(f"  共 {len(camps)} 个")
for d, f in camps[:26]:
    p = os.path.join(G, d, f)
    t = open(p, "rb").read().decode("gbk", "replace")
    ls = [x for x in re.split(r"\r\n|\r|\n", t) if x.strip()]
    first = ls[0].strip() if ls else "(空)"
    tag = "⚠️长" if len(first) > 40 else "短"
    print(f"  {f:20s} [{tag}] 行0 = {first[:62]}  （共 {len(ls)} 非空行）")

print()
print("=" * 96)
print("② 「Klidi / 克列迪道」到底在哪（备份英文 + 游戏中文，字节级）")
print("=" * 96)
for t in ("Klidi", "Mount Olympus", "克列迪道"):
    for enc in (("gbk",) if any(ord(c) > 127 for c in t) else ("latin-1",)):
        nb = t.encode(enc)
        hits = []
        for base in (BK, G):
            for root, dirs, files in os.walk(base):
                for fn in files:
                    p = os.path.join(root, fn)
                    try:
                        b = open(p, "rb").read()
                    except Exception:
                        continue
                    if nb in b:
                        hits.append(os.path.relpath(p, base))
        print(f"  「{t}」({enc}) 命中 {len(hits)}: {hits[:6]}")

print()
print("=" * 96)
print("③ 无 _m.txt 的 .scn：其 _i.txt 行 0 是什么（验证「回退读 _i」的猜想）")
print("=" * 96)
sd = os.path.join(G, "SCENARIO")
scns = [f for f in os.listdir(sd) if f.lower().endswith(".scn")]
for f in sorted(scns)[:400]:
    stem = f[:-4]
    if os.path.isfile(os.path.join(sd, stem + "_m.txt")):
        continue
    line0 = "(无 _i.txt)"
    pi = os.path.join(sd, stem + "_i.txt")
    if os.path.isfile(pi):
        t = open(pi, "rb").read().decode("gbk", "replace")
        line0 = re.split(r"\r\n|\r|\n", t)[0].strip()
    print(f"  {stem:16s} _i.txt 行0 = {line0[:56]}")
