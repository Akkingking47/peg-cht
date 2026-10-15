#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段0.7b：WW2GEN.dat 全屏画面清单（烘焙文字候选）+ 名称线索。

不改写任何文件；只读索引。
"""
import io
import os
import re
import struct
import sys

GAME = r"D:\Program Files\PeG-WW2"
DAT = os.path.join(GAME, "WW2GEN.dat")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "evidence")
os.makedirs(OUT, exist_ok=True)
_REPORT = os.path.join(OUT, "recon7-fullscreen.txt")
_sink = io.StringIO()


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def main():
    sz = os.path.getsize(DAT)
    with open(DAT, "rb") as f:
        n, dirend = struct.unpack("<II", f.read(8))
        d = f.read(dirend - 8)
    ents = []
    off = 0
    while off + 17 <= len(d) and len(ents) < n:
        nm = d[off:off + 13].rstrip(b"\0").decode("latin1")
        (o,) = struct.unpack_from("<I", d, off + 13)
        ents.append((nm, o))
        off += 17
    print(f"WW2GEN.dat {sz:,} B, n={n:,}, 解析 {len(ents):,}, dirend={dirend:,}")

    print()
    print("=" * 90)
    print("A. 全屏候选（任一 icon ≥ 600x400）")
    print("=" * 90)
    big = []
    bad = 0
    with open(DAT, "rb") as f:
        for nm, o in ents:
            if o + 4 > sz:
                bad += 1
                continue
            f.seek(o)
            hdr = f.read(4)
            if len(hdr) < 4:
                bad += 1
                continue
            (nicon,) = struct.unpack("<I", hdr)
            if nicon == 0 or nicon > 400 or o + 4 + nicon * 40 > sz:
                bad += 1
                continue
            recs = f.read(nicon * 40)
            dims = []
            ok = True
            for i in range(min(nicon, 40)):
                w, h = struct.unpack_from("<II", recs, i * 40)
                if w > 4096 or h > 4096 or w == 0 or h == 0:
                    ok = False
                    break
                dims.append((w, h))
            if not ok:
                bad += 1
                continue
            mx = max(dims, key=lambda t: t[0] * t[1])
            if mx[0] >= 600 and mx[1] >= 400:
                big.append((nm, nicon, mx, dims[:4]))
    print(f"  可解析条目中含全屏画面的: {len(big)}  （索引不可解析/异格式: {bad}）")
    for nm, nicon, mx, dims in sorted(big, key=lambda t: -t[2][0] * t[2][1])[:60]:
        print(f"   {nm:16s} nIcons={nicon:<4d} 最大={mx[0]}x{mx[1]}  前几个={dims}")

    print()
    print("=" * 90)
    print("B. 名称线索（疑似含文字的画面 / 标题 / 荣誉榜）")
    print("=" * 90)
    pats = ["TITLE", "CREDIT", "HONOR", "INTRO", "START", "MENU", "LOGO", "ST0", "TEXT",
            "STRING", "FONT", "END", "BRIEF", "SCORE", "HELP", "BUTTN", "MAINBAR", "SPLASH"]
    for p in pats:
        hit = [nm for nm, _ in ents if p in nm.upper()]
        if hit:
            print(f"   {p:8s} ({len(hit):>3d}): {hit[:14]}")
        else:
            print(f"   {p:8s} (  0)")


if __name__ == "__main__":
    main()
    with open(_REPORT, "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    print(f"\n[report] {_REPORT}")
