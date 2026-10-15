# -*- coding: utf-8 -*-
"""Full replay of the 2026-09-24 sequence that was followed by a successful
memory scan (21/27 Chinese probes present).

Order (measured):
  main menu
   (917,1000)  -> "top scores" dialog opens
   (1217,724)  -> dialog OK
   (758..886,1000)  five toolbar icons
   (950..1046,1000) four toolbar icons
   (1078,1000)      -> efile map screen
   Esc              -> map screen settles
   (960,300)        -> back to main menu, efile data left in memory
"""
import os
import sys
import time

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
    base = sys.argv[1] if len(sys.argv) > 1 else "poc/base.png"
    work = sys.argv[2] if len(sys.argv) > 2 else "poc"
    info = og.find_window()
    if not info:
        print("no window")
        return 1
    hwnd = info["hwnd"]
    print("hwnd=%s pid=%d" % (hwnd, info["pid"]))

    cur = os.path.join(work, "rp_cur.png")
    og.shot(hwnd, cur)
    d = diff(base, cur)
    print("start diff vs base = %.4f" % d)
    for i in range(6):
        if d < 0.05:
            break
        og.key(hwnd, 27, 1, 1.2)
        og.shot(hwnd, cur)
        d = diff(base, cur)
        print("  Esc#%d -> diff=%.4f" % (i + 1, d))
    if d >= 0.05:
        print("!! cannot reach the main-menu baseline")
        return 1

    def step(x, y, pause, tag):
        og.click(hwnd, x, y, pause)
        p = os.path.join(work, "rp_%s.png" % tag)
        og.shot(hwnd, p)
        print("  %-12s (%4d,%4d) diff=%.4f" % (tag, x, y, diff(base, p)))
        return p

    step(917, 1000, 2.5, "a_scores")
    step(1217, 724, 2.0, "b_ok")
    for i, x in enumerate((758, 790, 822, 855, 886)):
        step(x, 1000, 1.6, "c%d_%d" % (i, x))
    for i, x in enumerate((950, 982, 1014, 1046)):
        step(x, 1000, 1.6, "d%d_%d" % (i, x))
    p = step(1078, 1000, 4.0, "e_efile")
    og.key(hwnd, 27, 1, 2.0)
    og.shot(hwnd, os.path.join(work, "rp_f_esc.png"))
    print("  after Esc diff=%.4f" % diff(base, os.path.join(work, "rp_f_esc.png")))
    p = step(960, 300, 6.0, "g_photo")
    tgt = os.path.join(work, "ng_afterc.png")
    if os.path.exists(tgt):
        print("  vs ng_afterc=%.4f" % diff(tgt, p))
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
