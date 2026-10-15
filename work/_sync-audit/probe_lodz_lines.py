#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读：打印若干 `_m.txt` 的「英文备份行 ⇄ 中文成品行」配对（含 repr），
用来确认同一个中文值到底挂在哪个英文键上。"""
import io
import os

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GM = r"D:\Program Files\PeG-WW2\SCENARIO"

FILES = ("DAK_Choice_m.txt", "7Pzrb7147_m.txt", "B714_m.txt", "LAH_IT_02_m.txt",
         "zz112_m.txt", "s0029_m.txt")
NEEDLES = ("lodz", "litzmannstadt", "katowice", "kattowitz", "poznan", "posen",
           "cernauti", "czernowitz", "kishinev", "chisinau")


def rd(root, fn):
    p = os.path.join(root, fn)
    if not os.path.isfile(p):
        return None
    with io.open(p, "rb") as f:
        return f.read().decode("latin-1")


for fn in FILES:
    en = rd(BK, fn)
    zh = rd(GM, fn)
    if en is None or zh is None:
        print(f"!! {fn}: 备份={en is not None} 成品={zh is not None}")
        continue
    el, zl = en.split("\n"), zh.split("\n")
    print(f"== {fn}  行数 en={len(el)} zh={len(zl)}")
    for i, a in enumerate(el):
        if any(n in a.lower() for n in NEEDLES):
            b = zl[i] if i < len(zl) else "<缺行>"
            print(f"   L{i+1:<5} en={a.strip()!r}  ->  zh={b.strip()!r}")
