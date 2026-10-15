#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读：检查 Khabarovsk4_m.txt 两侧内容与 Amur 相关行（验证按场景定点覆盖是否命中）。"""
import io
import os

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, r"peg\testbed\backup\Scenario")
GM = r"D:\Program Files\PeG\Scenario"
TMP = os.path.join(WS, r"peg\testbed\_regen-name-converge\Scenario")

for fn in ("Khabarovsk4_m.txt", "Khabarovsk3mp_m.txt", "Khabarovsk3_m.txt"):
    print(f"===== {fn}")
    for tag, root, enc in (("备份(cp1252)", BK, "latin-1"), ("成品(gbk)", GM, "latin-1"),
                           ("临时(gbk)", TMP, "latin-1")):
        p = os.path.join(root, fn)
        if not os.path.isfile(p):
            print(f"  {tag:14s} <不存在> {p}")
            continue
        with io.open(p, "rb") as f:
            raw = f.read()
        try:
            txt = raw.decode("gbk")
        except UnicodeDecodeError:
            txt = raw.decode("latin-1")
        ls = txt.split("\n")
        amur = [(i + 1, x.strip()) for i, x in enumerate(ls)
                if "amur" in x.lower() or "阿穆尔" in x or "黑龙江" in x]
        print(f"  {tag:14s} {len(raw):5d}B 行数={len(ls)}  AMUR 命中={amur}")
