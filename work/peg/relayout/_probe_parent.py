# -*- coding: utf-8 -*-
"""记录尾部 7 字节里有没有「所属对话框/父记录」？

假设：word@+0x08 可能是 parent/group id（多数为 -3 = 无父/未归类）。
验证方法：按该 word 分组，看组内是否空间聚集（外接框紧凑）、组间是否分离。
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import image as _img  # noqa: E402

BASE = 0x4A96E8
REC = 15
COUNT = 272


def main():
    recs = []
    for i in range(COUNT):
        raw = _img.read_va(BASE + i * REC, REC)
        v = [int.from_bytes(raw[o:o + 2], "little", signed=True) for o in (0, 2, 4, 6)]
        w8 = int.from_bytes(raw[8:10], "little", signed=True)
        b10, b11, b12, b13, b14 = raw[10], raw[11], raw[12], raw[13], raw[14]
        recs.append((i, v, w8, (b10, b11, b12, b13, b14)))

    print("=== 按 word@+0x08 分组 ===")
    g = defaultdict(list)
    for i, v, w8, tail in recs:
        g[w8].append(i)
    for w8 in sorted(g, key=lambda k: -len(g[k]))[:14]:
        idxs = g[w8]
        xs = [recs[j][1][0] for j in idxs]
        ys = [recs[j][1][1] for j in idxs]
        print("w8=%-7d 记录 %3d 条  x∈[%d,%d] y∈[%d,%d]  例 idx=%s" % (
            w8, len(idxs), min(xs), max(xs), min(ys), max(ys), idxs[:8]))

    print()
    print("=== byte@+0x0A 分组 ===")
    g2 = defaultdict(list)
    for i, v, w8, tail in recs:
        g2[tail[0]].append(i)
    for k in sorted(g2, key=lambda k: -len(g2[k])):
        idxs = g2[k]
        print("b10=%-4d 记录 %3d 条  例 idx=%s" % (k, len(idxs), idxs[:10]))

    print()
    print("=== byte@+0x0B 分组 ===")
    g3 = defaultdict(list)
    for i, v, w8, tail in recs:
        g3[tail[1]].append(i)
    for k in sorted(g3, key=lambda k: -len(g3[k])):
        idxs = g3[k]
        print("b11=%-4d 记录 %3d 条  例 idx=%s" % (k, len(idxs), idxs[:10]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
