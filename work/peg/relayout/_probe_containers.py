# -*- coding: utf-8 -*-
"""子孙-容器分析：哪些记录是"面板外框"（包含其它记录），它们自身是否在设计空间居中？

用途：用户要求"子界面按原始布局的相对位置在新分辨率下正确居中"。
单一全局仿射只能保相对位置；要让**每个子界面各自居中**，必须先认出"谁是一个子界面"。
本脚本用纯几何包含关系给出候选容器表（数据证据），供"分组圣地 solute"决策。
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


def read():
    out = []
    for i in range(COUNT):
        raw = _img.read_va(BASE + i * REC, REC)
        v = [int.from_bytes(raw[o:o + 2], "little", signed=True) for o in (0, 2, 4, 6)]
        out.append((i, v))
    return out


def main():
    recs = read()
    valid = [(i, v) for i, v in recs if all(-64 <= n <= (864 if k % 2 == 0 else 664)
                                            for k, n in enumerate(v))]
    print("合法记录 %d 条" % len(valid))
    cont = []
    for i, a in valid:
        ax0, ay0, ax1, ay1 = a
        if ax1 - ax0 < 40 or ay1 - ay0 < 40:
            continue
        kids = [j for j, b in valid
                if j != i and b[0] >= ax0 and b[1] >= ay0 and b[2] <= ax1 and b[3] <= ay1
                and (b[2] - b[0]) < (ax1 - ax0) and (b[3] - b[1]) < (ay1 - ay0)]
        if len(kids) >= 3:
            cont.append((i, a, kids))
    cont.sort(key=lambda t: -len(t[2]))
    print("候选容器（自身 ≥40px 且完全包含 ≥3 条其它记录）共 %d 个：" % len(cont))
    print("%-5s %-22s %-10s %-8s %-14s %s" % ("idx", "矩形(x0,y0,x1,y1)", "尺寸", "内含", "中心", "与设计中心(400,300)偏差"))
    for i, a, kids in cont[:15]:
        cx = (a[0] + a[2]) / 2.0
        cy = (a[1] + a[3]) / 2.0
        print("%-5d %-22s %-10s %-8d %-14s %s" % (
            i, str(tuple(a)), "%dx%d" % (a[2] - a[0], a[3] - a[1]), len(kids),
            "(%.0f,%.0f)" % (cx, cy), "(%.0f,%.0f)" % (cx - 400, cy - 300)))
    # 未被任何容器包含的记录
    covered = set()
    for i, a, kids in cont:
        covered.update(kids)
        covered.add(i)
    free = [i for i, v in valid if i not in covered]
    print()
    print("不属于任何容器的记录 %d 条：%s" % (len(free), free[:40]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
