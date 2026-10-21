# -*- coding: utf-8 -*-
"""方案 B：按"窗口组"重定位 —— 与现有方案 A（单一全局仿射）的差异量化。

来源：docs\\80 §2 的变换 + 本轮新发现的记录分组字段（byte@+0x0A 疑似窗口 id）。
约束：分组只是"每组各自平移"，组内仍是同一个刚性缩放 ⇒ 组内相对位置/尺寸完全不变。
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import image as _img  # noqa: E402
from layout_model import Layout, TARGET_RESOLUTIONS, rp  # noqa: E402

BASE = 0x4A96E8
REC = 15
COUNT = 272
FIELDS = [("x1", 0x00), ("y1", 0x02), ("x2", 0x04), ("y2", 0x06)]


def load():
    out = []
    for i in range(COUNT):
        raw = _img.read_va(BASE + i * REC, REC)
        v = {n: int.from_bytes(raw[o:o + 2], "little", signed=True) for n, o in FIELDS}
        out.append({"idx": i, "v": v, "win": raw[10], "kind": raw[11]})
    return out


def valid(r):
    v = r["v"]
    return (-64 <= v["x1"] <= 864 and -64 <= v["x2"] <= 864
            and -64 <= v["y1"] <= 664 and -64 <= v["y2"] <= 664
            and not (v["x2"] - v["x1"] <= 1 and v["y2"] - v["y1"] <= 1))


def group_anchors(recs):
    groups = {}
    for r in recs:
        if not valid(r):
            continue
        groups.setdefault(r["win"], []).append(r)
    anchors = {}
    for win, members in groups.items():
        x0 = min(m["v"]["x1"] for m in members)
        y0 = min(m["v"]["y1"] for m in members)
        x1 = max(m["v"]["x2"] for m in members)
        y1 = max(m["v"]["y2"] for m in members)
        anchors[win] = (x0, y0, x1, y1, len(members))
    return anchors


def plan(W, H, strategy="S2"):
    L = Layout(W, H, strategy)
    recs = load()
    anchors = group_anchors(recs)
    lines = []
    diff = 0
    total = 0
    oob = 0
    for r in recs:
        if not valid(r):
            continue
        ax0, ay0, ax1, ay1, _n = anchors[r["win"]]
        cx = (ax0 + ax1) / 2.0
        cy = (ay0 + ay1) / 2.0
        for name in ("x1", "y1", "x2", "y2"):
            v = r["v"][name]
            new_a = L.x(v) if name[0] == "x" else L.y(v)          # 方案 A：全局仿射
            if name[0] == "x":
                new_b = rp(W / 2 + (v - cx) * L.s)                 # 方案 B：按组居中
            else:
                new_b = rp(H / 2 + (v - cy) * L.s)
            total += 1
            if new_a != new_b:
                diff += 1
            T = W if name[0] == "x" else H
            if not (0 <= new_b < T):
                oob += 1
    return L, anchors, diff, total, oob


def main():
    print("=== 窗口组（byte@+0x0A）及其设计空间外挂框 ===")
    recs = load()
    anchors = group_anchors(recs)
    print("%-6s %-6s %-22s %-11s %-14s %s" % ("win", "n", "外挂框", "尺寸", "组中心", "与设计中心偏差"))
    for win in sorted(anchors):
        x0, y0, x1, y1, n = anchors[win]
        print("%-6d %-6d %-22s %-11s %-14s %s" % (
            win, n, str((x0, y0, x1, y1)), "%dx%d" % (x1 - x0, y1 - y0),
            "(%.0f,%.0f)" % ((x0 + x1) / 2, (y0 + y1) / 2),
            "(%.0f,%.0f)" % ((x0 + x1) / 2 - 400, (y0 + y1) / 2 - 300)))

    print()
    print("=== 方案 B 相对方案 A 的差异（六档分辨率） ===")
    print("%-11s %-6s %-10s %-10s %-10s %s" % ("分辨率", "s", "字段总数", "目标值不同", "占比", "落屏外"))
    for W, H in TARGET_RESOLUTIONS:
        L, anchors, diff, total, oob = plan(W, H)
        print("%-11s %-6.2f %-10d %-10d %-10.1f%% %d" % (
            "%dx%d" % (W, H), L.s, total, diff, 100.0 * diff / total, oob))

    # 1920x1080 下，各窗口组"整体中心"落到哪里：A 方案 vs B 方案
    print()
    L = Layout(1920, 1080, "S2")
    print("=== 1920×1080 下各窗口组的居中效果（组外挂框中心，屏幕中心=960,540） ===")
    print("%-5s %-16s %-16s %s" % ("win", "方案A 组中心", "方案B 组中心", "A 的偏差"))
    for win in sorted(anchors):
        x0, y0, x1, y1, n = anchors[win]
        ax = (L.x(x0) + L.x(x1)) / 2.0
        ay = (L.y(y0) + L.y(y1)) / 2.0
        print("%-5d %-16s %-16s %s" % (
            win, "(%.0f,%.0f)" % (ax, ay), "(960,540)", "(%.0f,%.0f)" % (ax - 960, ay - 540)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
