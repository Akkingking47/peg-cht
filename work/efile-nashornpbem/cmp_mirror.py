# -*- coding: utf-8 -*-
"""Is TEXT-XX/SCENARIO a stale mirror that shadows SCENARIO? Compare hashes."""
import glob
import hashlib
import os

ROOT = r"D:/OpenPG2"


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


for ef in ("EFILE_OLGWW2", "EFILE_OPENPG"):
    a = os.path.join(ROOT, ef, "SCENARIO")
    b = os.path.join(ROOT, ef, "TEXT-ZH", "SCENARIO")
    if not os.path.isdir(b):
        print(ef, "no TEXT-ZH/SCENARIO"); continue
    names = sorted(set(os.listdir(a)) & set(os.listdir(b)))
    same = diff = 0
    difflist = []
    from collections import Counter
    difext = Counter()
    for n in names:
        pa, pb = os.path.join(a, n), os.path.join(b, n)
        if not (os.path.isfile(pa) and os.path.isfile(pb)):
            continue
        if md5(pa) == md5(pb):
            same += 1
        else:
            diff += 1
            difext[os.path.splitext(n)[1].lower()] += 1
            difflist.append((n, os.path.getsize(pa), os.path.getsize(pb)))
    print("=" * 78)
    print("%s  SCENARIO vs TEXT-ZH/SCENARIO :  相同=%d  不同=%d" % (ef, same, diff))
    print("  差异文件的扩展名分布:", dict(difext))
    for n, s1, s2 in difflist[:8]:
        print("    %-34s SCENARIO=%7d  TEXT-ZH=%7d" % (n, s1, s2))
