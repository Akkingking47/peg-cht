# -*- coding: utf-8 -*-
"""P1 重排版的独立验算：不采信既有日志数字，直接从母本 exe 重算一遍。

检查项：
  1) 哪些记录落在设计空间内（合法性），有多少字段真正需要改写；
  2) 变换不变量：矩形不倒置、绢对几何关系按 s 等比、居中语义；
  3) 边界护栏：所有新坐标必须落在 [0,W)x[0,H) 内（不许画到屏幕外）；
  4) 六档分辨率全跑一遍。
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import image as _img  # noqa: E402
from layout_model import Layout, TARGET_RESOLUTIONS  # noqa: E402

BASE = 0x4A96E8
REC = 15
COUNT = 272
FIELDS = [("x1", 0x00), ("y1", 0x02), ("x2", 0x04), ("y2", 0x06)]
BOUND = {"x": (-64, 864), "y": (-64, 664)}


def read_records():
    recs = []
    for i in range(COUNT):
        va = BASE + i * REC
        vals = {}
        for name, off in FIELDS:
            b = _img.read_va(va + off, 2)
            v = int.from_bytes(b, "little", signed=True)
            vals[name] = v
        recs.append((i, vals))
    return recs


def in_range(name, v):
    lo, hi = BOUND["x" if name[0] == "x" else "y"]
    return lo <= v <= hi


def main():
    recs = read_records()
    print("母本：%s" % _img.MOTHER)
    print("控件矩形表 0x%X  记录数=%d  记录长=%d" % (BASE, COUNT, REC))
    ok_rec = [r for r in recs if all(in_range(n, v) for n, v in r[1].items())]
    bad_rec = [r for r in recs if not all(in_range(n, v) for n, v in r[1].items())]
    print("合法记录（全部 4 字段在设计空间内）= %d ；丢弃 = %d %s" % (
        len(ok_rec), len(bad_rec), [("idx%d" % i, v) for i, v in bad_rec[:3]]))
    print()
    hdr = "%-11s %-6s %-9s %-9s %-22s %-10s" % (
        "分辨率", "s", "合法记录", "实际写入", "新坐标范围 X/Y", "屏外/倒置")
    print(hdr)
    print("-" * len(hdr))
    for (W, H) in TARGET_RESOLUTIONS:
        L = Layout(W, H, "S2")
        writes = 0
        oob = 0
        inv = 0
        xs = []
        ys = []
        for idx, vals in ok_rec:
            new = {}
            for name, v in vals.items():
                nv = L.x(v) if name[0] == "x" else L.y(v)
                new[name] = nv
                if nv != v:
                    writes += 1
                if name[0] == "x":
                    xs.append(nv)
                else:
                    ys.append(nv)
                T = W if name[0] == "x" else H
                if not (0 <= nv < T):
                    oob += 1
            if not (new["x1"] <= new["x2"] and new["y1"] <= new["y2"]):
                inv += 1
        print("%-11s %-6.2f %-9d %-9d %-22s %-10s" % (
            "%dx%d" % (W, H), L.s, len(ok_rec), writes,
            "%d..%d / %d..%d" % (min(xs), max(xs), min(ys), max(ys)),
            "%d / %d" % (oob, inv)))
    # ---- 不变量抽查：1920x1080 下逐条验证「中心 = 屏幕中心 + (设计中心-400,300)*s」
    print()
    L = Layout(1920, 1080, "S2")
    worst_c = 0.0
    worst_d = 0.0
    for idx, vals in ok_rec:
        r_new = (L.x(vals["x1"]), L.y(vals["y1"]), L.x(vals["x2"]), L.y(vals["y2"]))
        cxn = (r_new[0] + r_new[2]) / 2.0
        cyn = (r_new[1] + r_new[3]) / 2.0
        cxo = (vals["x1"] + vals["x2"]) / 2.0
        cyo = (vals["y1"] + vals["y2"]) / 2.0
        exp_cx = 960 + (cxo - 400) * L.s
        exp_cy = 540 + (cyo - 300) * L.s
        worst_c = max(worst_c, abs(cxn - exp_cx), abs(cyn - exp_cy))
        wn = (r_new[2] - r_new[0], r_new[3] - r_new[1])
        wo = (vals["x2"] - vals["x1"], vals["y2"] - vals["y1"])
        for a, b in zip(wn, wo):
            worst_d = max(worst_d, abs(a - b * L.s))
    print("1920x1080 不变量：中心偏差最大 %.1f px（应 ≤0.5 取整）；边长缩放误差最大 %.1f px（应 ≤0.5 取整）"
          % (worst_c, worst_d))
    # ---- 与设计 >=800x600 完全居中的记录有多少
    centered = [(i, v) for i, v in ok_rec
                if abs((v["x1"] + v["x2"]) / 2.0 - 400) < 0.5 and abs((v["y1"] + v["y2"]) / 2.0 - 300) < 0.5]
    print("设计空间中本身已居中的记录 = %d 条：%s" % (len(centered), [i for i, _ in centered][:10]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
