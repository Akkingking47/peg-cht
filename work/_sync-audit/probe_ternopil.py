# -*- coding: utf-8 -*-
import os,re,glob
for root in (r"D:\Program Files\PeG-WW2\SCENARIO", r"D:\DSH\军事游戏汉化\pegww2\testbed\backup\SCENARIO"):
    print("---", root)
    for p in sorted(glob.glob(os.path.join(root,"*"))):
        b=os.path.basename(p); low=b.lower()
        if not (low.endswith(".txt") or low.endswith(".ply")): continue
        enc="gbk" if "backup" not in root else "cp1252"
        try: t=open(p,"rb").read().decode(enc,"replace")
        except Exception: continue
        if "ernopil" in t or "arnopol" in t:
            for ln in t.splitlines():
                if "ernopil" in ln or "arnopol" in ln:
                    print(f"  {b:26s} {ln.strip()[:90]}")
