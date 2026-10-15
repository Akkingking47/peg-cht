#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读探针：`RM_usvsruss6v.txt` 三份副本（备份 / 产出 / 游戏）的逐行实况。"""
import hashlib
import io
import os

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
OUT = os.path.join(WS, "pegww2", "testbed", "out", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
FN = "RM_usvsruss6v.txt"
BRANCH = r"D:\DSH\军事游戏汉化-1\pegww2\testbed\backup\SCENARIO"


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


for tag, d, enc in (("备份(BK)", BK, "cp1252"), ("产出(OUT)", OUT, "gbk"), ("游戏(GAME)", GAME, "gbk")):
    p = os.path.join(d, FN)
    if not os.path.isfile(p):
        print("%-12s ⛔ 缺文件 %s" % (tag, p))
        continue
    lines = io.open(p, encoding=enc, errors="replace").read().split("\n")
    print("%-12s md5=%s  %d B  %d 行" % (tag, md5(p), os.path.getsize(p), len(lines)))
    for i, l in enumerate(lines[:4]):
        print("             行%d: %r" % (i, l))
    print("")

# 全库残留扫描：哪些文件同时/分别含两写法
print("=== 全库（BK/OUT/GAME）扫描两种写法 ===")
for tag, d in (("BK", BK), ("OUT", OUT), ("GAME", GAME)):
    old_hit, new_hit = [], []
    for fn in sorted(os.listdir(d)):
        p = os.path.join(d, fn)
        if not os.path.isfile(p):
            continue
        try:
            t = io.open(p, encoding="gbk", errors="replace").read()
        except Exception:
            continue
        if "捷尔诺波尔" in t:
            old_hit.append(fn)
        if "塔尔诺波尔" in t:
            new_hit.append(fn)
    print("%-5s 含「捷尔诺波尔」%2d 个: %s" % (tag, len(old_hit), " ".join(old_hit[:12])))
    print("%-5s 含「塔尔诺波尔」%2d 个: %s" % (tag, len(new_hit), " ".join(new_hit[:12])))

print("\n=== 分支工作区的同名文件（参照）===")
bp = os.path.join(BRANCH, FN)
print("%s 存在=%s" % (bp, os.path.isfile(bp)))
if os.path.isfile(bp):
    print("md5=%s" % md5(bp))
    for i, l in enumerate(io.open(bp, encoding="cp1252", errors="replace").read().split("\n")[:4]):
        print("  行%d: %r" % (i, l))
