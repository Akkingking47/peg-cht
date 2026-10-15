# -*- coding: utf-8 -*-
"""Replay the click sequence that was observed to load the efile on 2026-09-24.

Recorded effective sequence (client 1920x1040):
  main menu
    -> toolbar icon @ (917,1000)   opens the "top scores" dialog (needs efile data)
    -> (1146,683)                  OK button, back to main menu
    -> toolbar icon @ (1078,1000)  efile "new game" map screen
    -> (960,300) / photo           loads the efile + scenario
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

    cur = os.path.join(work, "replay_cur.png")
    og.shot(hwnd, cur)
    d = diff(base, cur)
    print("baseline diff = %.4f" % d)

    # go back to the main menu if needed
    for i in range(5):
        if d < 0.05:
            break
        og.key(hwnd, 27, 1, 1.2)
        og.shot(hwnd, cur)
        d = diff(base, cur)
        print("  after Esc#%d diff=%.4f" % (i + 1, d))
    if d >= 0.05:
        print("!! cannot return to the recorded main-menu baseline; aborting")
        return 1

    # 1) open + close the top-scores dialog
    og.click(hwnd, 917, 1000, 2.5)
    og.shot(hwnd, os.path.join(work, "replay_scores.png"))
    print("scores dialog diff=%.4f" % diff(base, os.path.join(work, "replay_scores.png")))
    og.click(hwnd, 1146, 683, 2.0)
    og.shot(hwnd, os.path.join(work, "replay_back.png"))
    print("after OK diff=%.4f" % diff(base, os.path.join(work, "replay_back.png")))

    # 2) efile screen
    og.click(hwnd, 1078, 1000, 3.0)
    og.shot(hwnd, os.path.join(work, "replay_desk.png"))
    print("efile screen diff vs base=%.4f" % diff(base, os.path.join(work, "replay_desk.png")))

    # 3) campaign photo -> load
    og.click(hwnd, 960, 300, 8.0)
    og.shot(hwnd, os.path.join(work, "replay_loaded.png"))
    tgt = os.path.join(work, "ng_afterc.png")
    if os.path.exists(tgt):
        print("loaded diff vs ng_afterc=%.4f" % diff(tgt, os.path.join(work, "replay_loaded.png")))
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
