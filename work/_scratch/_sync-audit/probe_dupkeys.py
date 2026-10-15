#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读：检查两张映射表里是否存在**重复英文键**（同一个 en 多行、值却不同）。

动机：`load_map()` 是 `m[key] = (zh, tag)` ⇒ 重复键**后者覆盖前者**，
     按势力/年代分叉的值无法用全局表表达 —— 这正是 `scn-place-override.tsv` 存在的理由。
"""
import collections
import io
import os

WS = r"D:\DSH\军事游戏汉化"
KEYOF = ("lodz", "katowice", "poznan", "cernauti", "kishinev", "tarnopol'",
         "viipuri", "tannenberg", "amur river", "suchan", "khazhetay", "dessau")

for name, p in (("WW2", os.path.join(WS, r"pegww2\research\ww2-scn-map.tsv")),
                ("PeG", os.path.join(WS, r"peg\research\scenario-map.tsv"))):
    allrows = collections.defaultdict(list)
    n = 0
    with io.open(p, encoding="utf-8-sig") as f:
        for i, ln in enumerate(f, 1):
            s = ln.rstrip("\r\n")
            c = s.split("\t")
            if len(c) < 2 or s.startswith("#") or c[0].strip() == "原文" or not c[0].strip():
                continue
            n += 1
            allrows[c[0].strip()].append((i, c[1].strip()))
    dup = {k: v for k, v in allrows.items() if len({x[1] for x in v}) >= 2}
    print(f"== {name}  {p}")
    print(f"   数据行 {n} · 唯一英文键 {len(allrows)} · ⚠️ 同键多值 {len(dup)} 个")
    for k in sorted(dup)[:40]:
        print(f"     {k:26s} " + " ｜ ".join(f"L{i}:{v}" for i, v in dup[k] if v))
    print("   —— 关键字现状：")
    for k in KEYOF:
        for kk in allrows:
            if kk.lower() == k:
                print(f"     {kk:26s} " + " ｜ ".join(f"L{i}:{v}" for i, v in allrows[kk]))
    print()
