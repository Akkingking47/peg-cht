# -*- coding: utf-8 -*-
"""把 xscn-map.tsv 中 NASHORNPBEM 的组 -1（场景标题）由恒等映射改为中文。"""
import io

P = r"D:\DSH\军事游戏汉化\work\efile-nashornpbem\xscn-map.tsv"

with io.open(P, "r", encoding="utf-8-sig", newline="") as f:
    txt = f.read()

old = "utopianparadox.xscn\t-1\t0\tUtopianParadox\tUtopianParadox"
new = "utopianparadox.xscn\t-1\t0\tUtopianParadox\t乌托邦悖论"

assert txt.count(old) == 1, "标题行未唯一命中，实际 %d 处" % txt.count(old)
txt = txt.replace(old, new)

with io.open(P, "w", encoding="utf-8", newline="") as f:
    f.write(txt)

print("已改写标题行 -> 乌托邦悖论")
print("校验：", repr([l for l in txt.split("\n") if "\t-1\t" in l]))
