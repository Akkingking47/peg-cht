# -*- coding: utf-8 -*-
"""直接读当前 .xscn，列出仍然「纯 ASCII」的组0（地名）条目 —— 不信 pending.tsv 快照。

用法: python list_place_ascii.py
"""
import io
import os
import re

SCN = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
HERE = os.path.dirname(os.path.abspath(__file__))
SHIP = re.compile(r"^(HMS|USS|IJN|RMS|SMS|MV|SS|HMCS|HMAS|ORP|ARA|KM|RN|HMNZS|HMNoS)\b")


def parse(path):
    f = open(path, "rb").read()
    st = f.find(b"<N:")
    if st < 0:
        return None
    g = st
    while g < len(f) and f[g] != 0x3E:
        g += 1
    off = g + 1
    if off + 2 <= len(f):
        L = f[off] | (f[off + 1] << 8)
        if 0 < L and off + 2 + L <= len(f):
            off += 2 + L
    items, gi = [], 0
    while off + 2 <= len(f) and gi <= 64:
        cnt = f[off] | (f[off + 1] << 8)
        off += 2
        good = True
        for i in range(cnt):
            if off + 2 > len(f):
                good = False
                break
            L = f[off] | (f[off + 1] << 8)
            off += 2
            if off + L > len(f):
                good = False
                break
            items.append((gi, i, f[off:off + L]))
            off += L
        if not good or cnt == 0:
            break
        gi += 1
    return items


def is_ascii(raw):
    return all(c < 128 for c in raw)


def main():
    rows = []
    for fn in sorted(os.listdir(SCN)):
        if not fn.endswith(".xscn"):
            continue
        items = parse(os.path.join(SCN, fn))
        if not items:
            continue
        for gi, i, raw in items:
            if gi != 0 or not is_ascii(raw):
                continue
            s = raw.decode("cp1252", "replace").strip()
            if len(s) < 3 or SHIP.match(s):
                continue
            rows.append((fn, gi, i, s))
    print("组0 仍为纯 ASCII 的条目共 %d 条，涉 %d 文件\n" % (len(rows), len({r[0] for r in rows})))
    print("%-18s %-4s %-4s %s" % ("file", "g", "i", "src"))
    for fn, gi, i, s in rows:
        print("%-18s %-4d %-4d %s" % (fn, gi, i, s))


if __name__ == "__main__":
    main()
