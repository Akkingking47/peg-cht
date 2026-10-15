# -*- coding: utf-8 -*-
"""Build memory probes for names.txt (line-indexed) plus equip.txt controls."""
import io

EN = r"D:/OpenPG2/EFILE_NASHORNPBEM/names.txt"
ZH = r"D:/DSH/军事游戏汉化/work/efile-nashornpbem/dist/names.txt"
OUT = r"D:/DSH/军事游戏汉化/work/efile-nashornpbem/probes-names.tsv"

en = io.open(EN, encoding="gbk", errors="replace", newline="").read().split("\r\n")
zh = io.open(ZH, encoding="gbk", errors="replace", newline="").read().split("\r\n")
print("EN lines=%d  ZH lines=%d" % (len(en), len(zh)))

idxs = [0, 1, 3, 4, 11, 299, 530, 798, 923]
probes = []
for i in idxs:
    if i >= min(len(en), len(zh)):
        continue
    e, z = en[i], zh[i]
    if not e.strip() or not z.strip():
        continue
    print("%4d  EN=%-32r ZH=%r" % (i + 1, e, z))
    probes.append((z, e, "names#%d" % (i + 1)))

# controls: equip.txt entries known to be live (Chinese present in running game)
probes.append(("掷弹兵", "Panzergrenadiere", "equip.txt ctrl"))
probes.append(("摩托化步兵", "Motorized", "equip.txt ctrl"))
probes.append(("乌托邦悖论", "UtopianParadox", "xscn title ctrl"))
probes.append(("霍岑多夫", "Hotzendorff", "names sub-probe"))
probes.append(("阿尔布雷克松", "Albrektsson", "names sub-probe"))
probes.append(("曼纳海姆", "Mannerheim", "names sub-probe"))
probes.append(("隆美尔", "Rommel", "names sub-probe"))

with io.open(OUT, "w", encoding="utf-8", newline="") as f:
    for z, e, s in probes:
        f.write(u"%s\t%s\t%s\n" % (z, e, s))
print("written %d -> %s" % (len(probes), OUT))
