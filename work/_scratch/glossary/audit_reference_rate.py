import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WS = r"D:\DSH\军事游戏汉化"
bank = set()
for i, l in enumerate(open(os.path.join(WS, "glossary", "standard-glossary.tsv"), encoding="utf-8-sig")):
    if i:
        f = l.rstrip("\n").split("\t")
        if len(f) >= 4:
            bank.add(f[0])
LAYERS = [
    ("本作界面", os.path.join(WS, "pegww2", "research", "WW2Gui-map.tsv"), 1, 2),
    ("本作装备", os.path.join(WS, "pegww2", "research", "ww2-eqp-map.tsv"), 0, 1),
    ("本作场景", os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv"), 0, 1),
]
print("%-10s %10s %10s %10s %10s" % ("层表", "行数", "唯一原文", "库中有", "引用率"))
print("-" * 56)
tr = tu = th = 0
for tag, p, ec, zc in LAYERS:
    rows, uniq = 0, set()
    for l in open(p, encoding="utf-8-sig"):
        if l.startswith("#"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) > max(ec, zc) and c[ec].strip() and c[zc].strip():
            rows += 1
            uniq.add(c[ec].strip())
    hit = len(uniq & bank)
    tr += rows
    tu += len(uniq)
    th += hit
    print("%-10s %10d %10d %10d %9.0f%%" % (tag, rows, len(uniq), hit, 100.0 * hit / max(1, len(uniq))))
print("-" * 56)
print("%-10s %10d %10d %10d %9.0f%%" % ("合计", tr, tu, th, 100.0 * th / max(1, tu)))
print()
print("⇒ 按**唯一原文**算的引用率；重复行只算一次（对齐参照项目「唯一字串涵蓋率」口径）")
