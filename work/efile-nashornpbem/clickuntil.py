# -*- coding: utf-8 -*-
"""Click candidate points in turn until the screen matches a baseline.

  python clickuntil.py --base base.png --cands "1146,683;1090,683" [--shots dir]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ogsnap as og  # noqa


def diff(a, b):
    wa, ha, ra = og.png_read_rgb(a)
    wb, hb, rb = og.png_read_rgb(b)
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
    ap.add_argument("--base", required=True)
    ap.add_argument("--cands", required=True)
    ap.add_argument("--shots", default="")
    ap.add_argument("--pause", type=float, default=1.5)
    ap.add_argument("--tol", type=float, default=0.05)
    a = ap.parse_args()

    info = og.find_window()
    hwnd = info["hwnd"]
    cwd = os.path.dirname(os.path.abspath(a.base))
    if a.shots:
        os.makedirs(a.shots, exist_ok=True)
    else:
        a.shots = cwd

    for i, c in enumerate([v for v in a.cands.split(";") if v.strip()]):
        x, y = [int(t) for t in c.split(",")]
        og.click(hwnd, x, y, a.pause)
        p = os.path.join(a.shots, "_try%02d_%d_%d.png" % (i, x, y))
        og.shot(hwnd, p)
        d = diff(a.base, p)
        ok = d < a.tol
        print("try (%d,%d) diff=%.4f %s" % (x, y, d, "RESTORED" if ok else "-"))
        if ok:
            return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
