# -*- coding: utf-8 -*-
import io, sys, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = r"d:\DSH\军事游戏汉化\pegww2\research\_番号展开-对照表-20261020.tsv"
rows = [l.rstrip("\n").split("\t") for l in open(p, encoding="utf-8") if l.strip()][1:]
rows = [r for r in rows if len(r) >= 8]
print("总行", len(rows))
for scn in ["RTB01", "viipuri", "kanev", "drstlo25"]:
    sub = [r for r in rows if r[3].lower() == scn.lower()]
    print("\n-- %s (国别=%s, %d行) 前14：" % (scn, sub[0][0] if sub else "?", len(sub)))
    for r in sub[:14]: print("   %-26s -> %-30s [%s]" % (r[4][:26], r[5][:30], r[7]))
import random
random.seed(7)
print("\n-- 随机 22 行 --")
for r in random.sample(rows, 22):
    print("   %-8s %-24s -> %-30s [%s] %s" % (r[0], r[4][:24], r[5][:30], r[7], r[6][:36]))
