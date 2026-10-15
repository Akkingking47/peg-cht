#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读：查 `Amur River`（阿穆尔河 / 黑龙江）与 `Suchan`（苏昌 / 苏城）的
「预设扮演势力」取证 —— 分不清势力就无法按用户裁定 ③④ 统一。"""
import glob
import io
import os
import re

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG\Scenario"
REG = os.path.join(WS, "glossary", "layers", "faction-places.tsv")

print(f"== {REG}")
with io.open(REG, encoding="utf-8-sig") as f:
    for i, ln in enumerate(f, 1):
        if re.search(r"(?i)amur|suchan|khabarovsk|artem|vladivostok", ln):
            print(f"  L{i:<4} {ln.rstrip()}")

print(f"\n== {GAME} 下 Khabarovsk* / Vladivostok* 文件")
for pat in ("Khabarovsk*", "Vladivostok*"):
    for p in sorted(glob.glob(os.path.join(GAME, pat))):
        fn = os.path.basename(p)
        if fn.lower().endswith((".scn", ".map", ".cam")):
            continue
        with io.open(p, "rb") as fh:
            raw = fh.read()
        try:
            t = raw.decode("gbk")
        except UnicodeDecodeError:
            t = raw.decode("latin-1")
        ls = [x.strip() for x in t.split("\n") if x.strip()]
        if not ls:
            continue
        head = " ⟂ ".join(ls[:2])[:150]
        print(f"  {fn:26s} {len(raw):6d}B  {head}")
