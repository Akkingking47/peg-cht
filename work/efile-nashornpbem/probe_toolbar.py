# -*- coding: utf-8 -*-
"""Probe the OpenGen toolbar: click each button, screenshot, and report which
ones change the screen.  Optionally press Esc afterwards to close a dialog.

  python probe_toolbar.py --y 1000 --xs 758,790,822,... --outdir D:\\...\\poc\\probe
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ogsnap as og  # noqa


def imgdata(path):
    return og.png_read_rgb(path)


def diff(a_path, b_path):
    wa, ha, ra = imgdata(a_path)
    wb, hb, rb = imgdata(b_path)
    if (wa, ha) != (wb, hb):
        return -1.0
    tot = 0
    n = wa * ha * 3
    for y in range(ha):
        xa, xb = ra[y], rb[y]
        for x in range(wa * 3):
            tot += abs(xa[x] - xb[x])
    return tot / float(n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--y", type=int, default=1000)
    ap.add_argument("--xs", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--esc", action="store_true", help="press Esc after a changing click")
    ap.add_argument("--pause", type=float, default=1.6)
    a = ap.parse_args()

    xs = [int(v) for v in a.xs.split(",") if v.strip()]
    os.makedirs(a.outdir, exist_ok=True)

    info = og.find_window()
    if not info:
        print("no window")
        return 1
    hwnd = info["hwnd"]
    print("hwnd=%s pid=%d client=%s" % (hwnd, info["pid"], og.client_size(hwnd)))

    base = os.path.join(a.outdir, "_base.png")
    og.shot(hwnd, base)

    for x in xs:
        og.click(hwnd, x, a.y, a.pause)
        p = os.path.join(a.outdir, "x%04d.png" % x)
        og.shot(hwnd, p)
        d = diff(base, p)
        changed = d > 0.05
        print("x=%-5d diff=%.4f  %s" % (x, d, "CHANGED" if changed else "-"))
        if changed and a.esc:
            og.key(hwnd, 27, 1, 1.0)
            q = os.path.join(a.outdir, "x%04d_esc.png" % x)
            og.shot(hwnd, q)
            d2 = diff(base, q)
            print("          after Esc diff=%.4f %s" % (d2, "(restored)" if d2 < 0.05 else "(still different)"))
            if d2 > 0.05:
                print("          !! state not restored; aborting sweep")
                return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
