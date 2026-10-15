# -*- coding: utf-8 -*-
"""查 `Bon.` → `第76营` 的可疑对应：把 GCN 系列 .xscn 的原文槽与当前中文槽并排打印。
只读，不改任何文件。"""
import os
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\efile-nashornpbem")
from apply_residual import parse  # noqa: E402

WS = r"D:\DSH\军事游戏汉化"
ORIG = os.path.join(WS, "backup", "ORIGINAL-EFILE_OLGWW2", "SCENARIO")
CUR = r"D:\OpenPG2\EFILE_OLGWW2\SCENARIO"
FILES = ["GCN0.xscn", "GCN2.xscn", "GCN3.xscn", "GCN4.xscn", "GCN7.xscn"]


def vals(path):
    data, items, meta = parse(path)
    out = {}
    if meta and meta[0] is not None:
        try:
            out[("title", 0)] = data[meta[0] + 2:meta[0] + 2 + meta[1]].decode("gbk")
        except Exception:
            pass
    for gi, idx, off, L in items:
        try:
            out[(gi, idx)] = data[off + 2:off + 2 + L].decode("gbk")
        except Exception:
            out[(gi, idx)] = "<decode-fail>"
    return out


def main():
    for fn in FILES:
        po = os.path.join(ORIG, fn)
        pc = os.path.join(CUR, fn)
        if not (os.path.exists(po) and os.path.exists(pc)):
            continue
        o = vals(po)
        c = vals(pc)
        keys = [k for k in o if o.get(k, "").find("Bon") >= 0
                or c.get(k, "").find("76") >= 0]
        if not keys:
            continue
        print("=== %s ===" % fn)
        for k in sorted(keys):
            print("  g%d#%-4s EN=%-42s ZH=%s" % (k[0], k[1], o.get(k, "")[:42], c.get(k, "")[:60]))
        print()


if __name__ == "__main__":
    main()
