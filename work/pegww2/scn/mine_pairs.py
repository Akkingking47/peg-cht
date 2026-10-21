# -*- coding: utf-8 -*-
"""挖掘：原版备份 _u ↔ 已译部署 _u 逐行比对，收集 原文token -> 中文token 映射。
用于推导字母后缀（T/G/M/P…）与英文编制名的实测译法。"""
import os, sys, io, re
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
DEP = r"D:\Program Files\PeG-WW2\SCENARIO"
BK = r"d:\DSH\军事游戏汉化\pegww2\testbed\backup\SCENARIO"
CJK = re.compile(r"[\u4e00-\u9fff]")

def rd(p):
    return open(p, "rb").read().decode("gbk", errors="replace").split("\r\n")

idx = {f.lower(): f for f in os.listdir(DEP) if f.lower().endswith("_u.txt")}
pairs = Counter()          # (raw, zh) 整行对
tokpairs = Counter()       # (raw_token, zh_token)
n_files = 0
whole = []
for f in sorted(os.listdir(DEP)):
    if not f.lower().endswith("_u.txt"): continue
    bk = os.path.join(BK, f)
    if not os.path.isfile(bk): continue
    d = rd(os.path.join(DEP, f)); b = rd(bk)
    if len(d) <= 1 or len(b) <= 1: continue
    if len(d) != len(b): continue
    n_files += 1
    for i in range(min(len(d), len(b))):
        x, y = b[i].strip(), d[i].strip()
        if not x or not y: continue
        if CJK.search(x) or not CJK.search(y): continue   # 只要「原文无中文→译文有中文」
        if x == y: continue
        pairs[(x, y)] += 1
        xt = [t for t in re.split(r"[/ ]+", x) if t]
        yt = [t for t in re.split(r"[/ ]+", y) if t]
        if len(xt) == len(yt):
            for a, c in zip(xt, yt):
                if not CJK.search(a) and CJK.search(c):
                    tokpairs[(a, c)] += 1
whole = pairs.most_common(60)
print(f"可比对文件 {n_files}；整行对 {len(pairs)}；同长度token对 {len(tokpairs)}")
print("\n== token 映射（次数≥3，长→短） ==")
for (a, c), n in sorted(tokpairs.items(), key=lambda kv: (-kv[1], -len(kv[0][0]))):
    if n >= 3: print(f"  {a:14s} -> {c}   x{n}")
print("\n== 整行对 top 40 ==")
for (x, y), n in whole[:40]:
    print(f"  [{n:3d}] {x[:34]:34s} -> {y[:44]}")
