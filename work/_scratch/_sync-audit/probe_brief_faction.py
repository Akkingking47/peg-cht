#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读：③「简报侧按阵营方统一」的取证。
① 打印相关 PeG 场景词干的**预设视角**；
② 打印 `peg\\research\\scenario-long-zh.tsv` 里含指定词的**长段行**（原文 + 译文）。
"""
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
sys.path.insert(0, os.path.join(WS, "work", "glossary"))
import faction_place_audit as F  # noqa: E402

STEMS = ("Khabarovsk3mp", "Khabarovsk4", "Khabarovsk1", "Khabarovsk2",
         "RED_Vladr2", "Tutorial", "Vladivostok2", "Vladivostok3",
         "Vladivostok3mp", "Vladivostok4", "Vladivostokrr")
NEEDLES = ("苏城", "苏昌", "黑龙江", "阿穆尔河")

data = F.load_scenarios()
pin = F.load_pin()
side, origin, voice = F.resolve_sides(data, pin)

print("== 场景视角")
for fn in sorted(data):
    if F.stem_of(fn) in {s.lower() for s in STEMS}:
        print(f"  {fn:26s} 阵营={side.get(fn, '?'):4s} 来源={origin.get(fn, '?'):8s}")

LT = os.path.join(WS, r"peg\research\scenario-long-zh.tsv")
print(f"\n== {LT} 含 {NEEDLES} 的行")
with io.open(LT, encoding="utf-8-sig") as f:
    for i, ln in enumerate(f, 1):
        if i == 1 or "原文" in ln[:10]:
            continue
        c = ln.rstrip("\r\n").split("\t")
        if len(c) < 2:
            continue
        hit = [n for n in NEEDLES if n in c[1]]
        if hit:
            print(f"  L{i:<4} 含={'/'.join(hit):12s} 原={c[0][:64]!r}")
            print(f"         译={c[1][:96]}")
