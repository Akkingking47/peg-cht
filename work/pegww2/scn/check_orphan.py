# -*- coding: utf-8 -*-
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"D:\Program Files\PeG-WW2\SCENARIO"
idx = {f.lower(): f for f in os.listdir(D)}
for stem in ["oakridge", "oakridge-R", "kon44", "kishnv45", "prok4", "windsor2", "W", "RU66BV", "KV"]:
    us = idx.get((stem + "_u.txt").lower()); ss = idx.get((stem + ".scn").lower())
    print("-- %s: scn=%s u=%s" % (stem, "有" if ss else "无", "有" if us else "无"))
    if us:
        t = open(os.path.join(D, us), "rb").read().decode("gbk", errors="replace").split("\r\n")
        for l in t[:6]: print("    ", l[:44])
