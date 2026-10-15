#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""安全审计：名栏修复用「整串键控」改译文 ⇒ 若同一字符串还在**别的文件**里当正文，就会被连带改错。

判据：对 `_scn-fill-namefix.tsv` 里每个被改成场景名的键，
      扫 `testbed/backup` 全部场景文件，统计该键出现在**哪些后缀**的文件里。
      若除 `<stem>_m.txt` 之外还有别的文件用它 ⇒ ⚠️ 误伤。
"""
import os
import re
from collections import defaultdict

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
FILL = os.path.join(WS, "pegww2", "research", "_scn-fill-namefix.tsv")

# 1) 读出「被改成场景名」的键
keys = {}
for i, l in enumerate(open(FILL, encoding="utf-8")):
    if i < 2 or not l.strip():
        continue
    f = l.rstrip("\n").split("\t")
    if len(f) >= 2:
        keys[f[0]] = f[1]

# 2) 扫全部备份文件，记录每个键出现在哪些文件
occ = defaultdict(list)
for fn in sorted(os.listdir(BK)):
    p = os.path.join(BK, fn)
    if not os.path.isfile(p):
        continue
    t = open(p, "rb").read().decode("latin-1")
    lines = set(re.split(r"\r\n|\r|\n", t))
    for k in keys:
        if k in lines:
            occ[k].append(fn)

print(f"被改成场景名的键: {len(keys)} 个")
danger = []
ok = 0
for k, files in occ.items():
    ms = [f for f in files if f.lower().endswith("_m.txt")]
    others = [f for f in files if not f.lower().endswith("_m.txt")]
    if others:
        danger.append((k, files))
    else:
        ok += 1
print(f"  ✅ 只出现在 _m.txt（安全）: {ok}")
print(f"  ⚠️ 还出现在别的文件（**误伤**）: {len(danger)}")
for k, files in danger:
    print(f"     {k[:64]!r}")
    print(f"        → 出现在: {files[:8]}{' …' if len(files) > 8 else ''}")
