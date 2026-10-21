# -*- coding: utf-8 -*-
"""探查控件矩形表 0x4A96E8 的记录结构：除前 8 字节矩形外还有 7 字节，里面有没有
「所属对话框/分组 id」？——这决定了"子界面整体居中"能不能按组施工，而不是只做
单一全局仿射。同时把"倒置矩形"的原始形态核实清楚（是本来就倒，还是算出来的）。
"""
from __future__ import annotations

import os
import sys
from collections import Counter, defaultdict

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
        recs.append((i, v, raw))
    print("%-5s %-6s %-6s %-6s %-6s  %-8s %s" % ("idx", "x1", "y1", "x2", "y2", "矩形", "尾部 7 字节(hex)  [us各值]"))
    for i, v, raw in recs:
        if i > 40 and i < 265:
            continue
        tail = raw[8:]
        tu = [int.from_bytes(tail[o:o + 2], "little", signed=True) for o in (0, 2, 4)]
        flag = "" if (v[0] <= v[2] and v[1] <= v[3]) else "  <== 原始即倒置"
        print("%-5d %-6d %-6d %-6d %-6d  %-8s %s  %s%s" % (
            i, v[0], v[1], v[2], v[3], "%dx%d" % (v[2] - v[0], v[3] - v[1]),
            tail.hex(" "), [hex(t) for t in tu], flag))
    print()
    # 统计
    inv = [i for i, v, _ in recs if not (v[0] <= v[2] and v[1] <= v[3])]
    print("原始即倒置的记录：%s" % (inv if inv else "无"))
    # 尾部字节的分布：哪些槽位是常量/疑似 id
    for slot in range(7):
        vals = [_img.read_va(BASE + i * REC + 8 + slot, 1)[0] for i in range(COUNT)]
        c = Counter(vals)
        print("尾部 slot +0x%02X：不同取值 %d 个，最常见 %s" % (
            8 + slot, len(c), c.most_common(3)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
