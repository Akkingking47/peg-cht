#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读：打印指定场景词干的简报标题/日期行，以及地图名栏里含指定英文键的那一行。

用途：裁定 `Lodz`（罗兹 / 利茨曼施塔特，分界 = 1940-04-11 德占改名）这类
「同一势力内部也不一致」的键到底该取哪个写法 —— 判据是**该场景的年代**。
"""
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")

STEMS = sys.argv[1:] or ["7Pzrb7147", "B714", "LAH_IT_02", "zz112", "DAK_Choice", "DAK_SPChoice",
                         "oakridge-R", "s0029", "wdchoice", "RTB34"]
KEY = "Lodz"


def read_bk(fn):
    p = os.path.join(BK, fn)
    if not os.path.isfile(p):
        return None
    with io.open(p, "rb") as f:
        return f.read().decode("latin-1")


print(f"备份目录 {BK}")
print(f"{'词干':14s} {'简报标题/日期（前 3 非空行）':60s} 地图名栏含 {KEY} 的行")
print("-" * 150)
for st in STEMS:
    title = ""
    for cand in (f"{st}_i.TXT", f"{st}_i.txt", f"{st}I.TXT", f"{st}I.txt",
                 f"{st}.TXT", f"{st}.txt"):
        t = read_bk(cand)
        if t:
            ls = [x.strip() for x in t.split("\n") if x.strip()]
            title = f"[{cand}] " + " ⟂ ".join(ls[:3])
            break
    hits = []
    for cand in (f"{st}_m.TXT", f"{st}_m.txt"):
        t = read_bk(cand)
        if not t:
            continue
        for i, ln in enumerate(t.split("\n"), 1):
            if KEY.lower() in ln.lower():
                hits.append(f"L{i}:{ln.strip()[:70]}")
        break
    print(f"{st:14s} {title[:60]:60s} {' ｜ '.join(hits)}")
