# -*- coding: utf-8 -*-
"""Inventory every EFILE_*/SCENARIO file by extension, and classify
.ply files as empty(0x00) / ascii / has-high-bytes.(=translated?)"""
import glob
import os
from collections import Counter

ROOT = r"D:/OpenPG2"
print("%-20s %8s %8s  %s" % ("efile", "files", "ext#", "extension histogram"))
print("-" * 110)
ply_stats = Counter()
ply_by_efile = {}
for d in sorted(glob.glob(os.path.join(ROOT, "EFILE_*"))):
    scn = os.path.join(d, "SCENARIO")
    if not os.path.isdir(scn):
        continue
    exts = Counter()
    n = 0
    for f in os.listdir(scn):
        fp = os.path.join(scn, f)
        if not os.path.isfile(fp):
            continue
        n += 1
        exts[os.path.splitext(f)[1].lower()] += 1
        if f.lower().endswith(".ply"):
            data = open(fp, "rb").read()
            if data.strip(b"\x00") == b"":
                k = "empty"
            elif any(x > 0x7F for x in data):
                k = "high-bytes(z h?)"
            else:
                k = "ascii"
            ply_stats[k] += 1
            ply_by_efile.setdefault(os.path.basename(d), Counter())[k] += 1
    hist = " ".join("%s=%d" % (e, c) for e, c in sorted(exts.items(), key=lambda x: -x[1])[:8])
    print("%-20s %8d %8d  %s" % (os.path.basename(d), n, len(exts), hist))

print("\n=== .ply 分类汇总 ===")
for k, v in ply_stats.items():
    print("  %-16s %d" % (k, v))
print("\n=== 按 efile ===")
for e, c in ply_by_efile.items():
    print("  %-18s %s" % (e, dict(c)))
