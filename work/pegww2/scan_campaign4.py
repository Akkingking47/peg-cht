#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把战役层与两个异常文本的来源彻底钉死。"""
import os
from collections import Counter

G = r"D:\Program Files\PeG-WW2"


def find(s, enc):
    nb = s.encode(enc)
    hits = []
    for root, dirs, files in os.walk(G):
        for fn in files:
            p = os.path.join(root, fn)
            try:
                b = open(p, "rb").read()
            except Exception:
                continue
            if nb in b:
                hits.append(os.path.relpath(p, G))
    return hits


print("① 「消息来自」在哪些**后缀**的文件里（关键：有没有 _m.txt）")
h = find("消息来自", "gbk")
c = Counter()
for f in h:
    base = os.path.basename(f)
    if "_" in base:
        c["_" + base.rsplit("_", 1)[1]] += 1
    else:
        c["(无下划线)" + os.path.splitext(base)[1]] += 1
print("   ", dict(c))
print("    _m.txt 命中:", [f for f in h if f.lower().endswith("_m.txt")][:10])
print("    .txt(非_m/_i) 命中:", [f for f in h if f.lower().endswith(".txt") and "_i.txt" not in f.lower() and "_m.txt" not in f.lower()][:10])

print()
print("② 战役名来源：搜「红色威胁」「德国在战争中」「死亡之靴」「地中海 46」")
for s in ("红色威胁", "德国在战争中", "死亡之靴", "地中海 46", "第7装甲集团军的英勇"):
    hh = find(s, "gbk")
    print(f"   「{s}」 → {hh[:5]}")

print()
print("③ 战役描述「克列迪道山口」的来源：搜片段")
for s in ("奥林帕斯", "列迪", "山口(Klidi", "(Klidi", "Klidi Pass"):
    enc = "gbk" if any(ord(ch) > 127 for ch in s) else "latin-1"
    hh = find(s, enc)
    print(f"   「{s}」({enc}) → {hh[:5]}")

print()
print("④ fifgint.txt 是否被汉化")
for cand in (os.path.join(G, "fifgint.txt"), os.path.join(G, "SCENARIO", "fifgint.txt")):
    if os.path.isfile(cand):
        b = open(cand, "rb").read()
        han = sum(1 for x in b if x > 127)
        t = b.decode("latin-1")
        print(f"   {cand}  {len(b)} B · 高位字节 {han}")
        print(f"      前 160 字符: {t[:160]!r}")

print()
print("⑤ 游戏根目录的文本文件（非 SCENARIO/USERSCEN）——这些可能整批没被处理")
for fn in sorted(os.listdir(G)):
    p = os.path.join(G, fn)
    if os.path.isfile(p) and fn.lower().endswith((".txt", ".tx", ".t", ".log")):
        b = open(p, "rb").read()
        han = sum(1 for x in b if x > 127)
        print(f"   {fn:24s} {len(b):>8d} B  高位字节 {han}")
