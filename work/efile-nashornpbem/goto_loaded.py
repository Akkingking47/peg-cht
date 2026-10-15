# -*- coding: utf-8 -*-
"""Drive OpenGen from the main menu to the state where the efile is loaded.

Known-good click path (measured 2026-09-24, 1920x1040 client):
  toolbar icon 11 @ (1078, 1000)  -> efile "new game" screen
  the centre campaign photo @ (960, 300) -> loads the efile / scenario
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ogsnap as og  # noqa

STEPS = [(1078, 1000, 2.5), (960, 300, 6.0)]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "poc/loaded.png"
    info = og.find_window()
    if not info:
        print("no OpenGen window")
        return 1
    hwnd = info["hwnd"]
    print("hwnd=%s pid=%d %s" % (hwnd, info["pid"], og.client_size(hwnd)))
    og.shot(hwnd, out.replace(".png", "_0menu.png"))
    for x, y, pause in STEPS:
        og.click(hwnd, x, y, pause)
    og.shot(hwnd, out)
    print("done -> %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
