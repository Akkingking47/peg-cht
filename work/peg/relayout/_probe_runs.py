# -*- coding: utf-8 -*-
"""b10（疑似界面/窗口 id）是否把记录切成"连续区间"？每个窗口的外接框多大、在设计空间里偏多少？

若成立，则"子界面居中"可以直接用表自带的分组，不需要运行时采样。
"""
from __future__ import annotations

import os
import sys

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
        recs.append((i, v, raw[10], raw[11]))
    print("=== index -> (b10 窗口id, b11 种类) 连续段 ===")
    prev = None
    start = 0
    segs = []
    for i, v, b10, b11 in recs:
        if prev is None:
            start = i
        elif b10 != prev:
            segs.append((start, i - 1, prev))
            start = i
        prev = b10
    segs.append((start, COUNT - 1, prev))
    for a, b, bid in segs:
        print("  idx[%3d..%3d]  b10=%-3d  n=%d" % (a, b, bid, b - a + 1))

    print()
    print("=== 每个窗口组的外接框（排除 1x1 哑元）与设计中心偏差 ===")
    print("%-6s %-5s %-22s %-11s %-16s %s" % ("b10", "n", "外挂框(x0,y0,x1,y1)", "尺寸", "中心", "与设计中心偏差"))
    for a, b, bid in segs:
        members = [(i, v) for i, v, b10, b11 in recs if b10 == bid
                   and not (v[2] - v[0] <= 1 and v[3] - v[1] <= 1)
                   and all(-64 <= t <= (864 if k % 2 == 0 else 664) for k, t in enumerate(v))]
        if not members:
            continue
        x0 = min(v[0] for _, v in members)
        y0 = min(v[1] for _, v in members)
        x1 = max(v[2] for _, v in members)
        y1 = max(v[3] for _, v in members)
        print("%-6d %-5d %-22s %-11s %-16s %s" % (
            bid, len(members), str((x0, y0, x1, y1)), "%dx%d" % (x1 - x0, y1 - y0),
            "(%.0f,%.0f)" % ((x0 + x1) / 2, (y0 + y1) / 2),
            "(%.0f,%.0f)" % ((x0 + x1) / 2 - 400, (y0 + y1) / 2 - 300)))

    print()
    print("=== b11==4（疑似面板外框）的全部记录 ===")
    for i, v, b10, b11 in recs:
        if b11 == 4:
            print("  idx=%-4d b10=%-3d %s  %dx%d  中心偏移(%d,%d)" % (
                i, b10, tuple(v), v[2] - v[0], v[3] - v[1],
                (v[0] + v[2]) / 2 - 400, (v[1] + v[3]) / 2 - 300))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
