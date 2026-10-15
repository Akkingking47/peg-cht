#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""字节级定位：战役名「达斯帝国师」等到底写在哪个文件里（二进制 .cam 也能命中）。"""
import os
import re

G = r"D:\Program Files\PeG-WW2"
TARGETS = ["达斯帝国师", "帝国师", "消息来自", "克列迪道山口", "这次失败绝不可容忍", "红色世界秩序", "海狮行动"]

print("=" * 96)
print("字节级搜索（GBK 编码串）")
print("=" * 96)
for t in TARGETS:
    nb = t.encode("gbk")
    found = []
    for root, dirs, files in os.walk(G):
        for fn in files:
            p = os.path.join(root, fn)
            try:
                b = open(p, "rb").read()
            except Exception:
                continue
            if nb in b:
                found.append(os.path.relpath(p, G))
    print(f"  「{t}」 命中 {len(found)} 个文件")
    for f in found[:8]:
        print(f"       {f}")
    if len(found) > 8:
        print(f"       … 另 {len(found)-8} 个")

print()
print("=" * 96)
print("战役层：.cam 文件（数量、大小、头 120 字节可读串）")
print("=" * 96)
cams = []
for root, dirs, files in os.walk(G):
    for fn in files:
        if fn.lower().endswith(".cam"):
            cams.append(os.path.join(root, fn))
print(f"  共 {len(cams)} 个")
for p in sorted(cams)[:10]:
    b = open(p, "rb").read()
    seg = b[80:220]
    txt = "".join(chr(c) if 32 <= c < 127 else ("·" if c else "␀") for c in seg)
    print(f"  {os.path.relpath(p, G):26s} {len(b):>7d} B  @80: {txt[:100]}")

print()
print("=" * 96)
print("哪些 .scn 没有对应的 _m.txt（引擎可能回退读别的文件 ⇒ 列表显示错内容）")
print("=" * 96)
scn_dir = os.path.join(G, "SCENARIO")
scns = [f for f in os.listdir(scn_dir) if f.lower().endswith(".scn")]
nom = []
for f in scns:
    stem = f[:-4]
    if not os.path.isfile(os.path.join(scn_dir, stem + "_m.txt")):
        nom.append(stem)
print(f"  .scn 共 {len(scns)} 个，其中没有 _m.txt 的: {len(nom)} 个")
for s in sorted(nom)[:20]:
    print(f"     {s}")
