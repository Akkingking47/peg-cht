#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装备层损坏取证：对比 原始备份 / 真源 map / 已部署文件 三者的前若干行与列结构。"""
import os

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "text", "ww2-eqp.txt")
MAP = os.path.join(WS, "pegww2", "research", "ww2-eqp-map.tsv")
CUR = os.path.join(G, "ww2-eqp.txt")

print("=" * 96)
print("① 原始备份 testbed/backup/text/ww2-eqp.txt 前 12 行")
print("=" * 96)
if os.path.isfile(BK):
    t = open(BK, "rb").read().decode("latin-1").split("\n")
    for i, l in enumerate(t[:12]):
        print(f"  {i:3d}: {l.rstrip()[:88]!r}")
else:
    print("  ❌ 备份不存在！")

print()
print("=" * 96)
print("② 真源 ww2-eqp-map.tsv 前 12 行（看列数与内容）")
print("=" * 96)
if os.path.isfile(MAP):
    n3 = 0
    for i, l in enumerate(open(MAP, encoding="utf-8-sig")):
        if i < 12:
            f = l.rstrip("\n").split("\t")
            print(f"  {i:3d}: {len(f)} 列 {f[:4]}")
        tabs = l.count("\t")
        if tabs >= 2:
            n3 += 1
    print("  n3=%d" % n3)

print()
print("=" * 96)
print("③ 已部署 ww2-eqp.txt 前 12 行")
print("=" * 96)
if os.path.isfile(CUR):
    t = open(CUR, "rb").read().decode("gbk", "replace").split("\n")
    for i, l in enumerate(t[:12]):
        print(f"  {i:3d}: {l.rstrip()[:88]!r}")
