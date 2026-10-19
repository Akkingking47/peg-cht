# -*- coding: utf-8 -*-
"""按行/列把截图切成「亮绿 / 暗 / 其它」的连续段，用来精确定位按钮胶囊的边界。

用法：
    python probe_runs.py <png> row <shot_y> [shot_x0] [shot_x1]
    python probe_runs.py <png> col <shot_x> [shot_y0] [shot_y1]
"""
import sys

from PIL import Image


def cls(p):
    r, g, b = p[:3]
    if g > 140 and r < 130 and b < 130:
        return "F"
    if r + g + b < 170:
        return "."
    return " "


def main():
    png, axis, fixed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    lo = int(sys.argv[4]) if len(sys.argv) > 4 else (20 if axis == "col" else 0)
    hi = int(sys.argv[5]) if len(sys.argv) > 5 else (807 if axis == "col" else 1040)
    img = Image.open(png).convert("RGB")
    print("%s  %s=%d  扫描 %d..%d" % (png, axis, fixed, lo, hi))
    runs = []
    prev = None
    start = lo
    for i in range(lo, hi):
        p = img.getpixel((fixed, i)) if axis == "col" else img.getpixel((i, fixed))
        c = cls(p)
        if c != prev:
            if prev is not None:
                runs.append((prev, start, i - 1))
            prev, start = c, i
    runs.append((prev, start, hi - 1))
    for c, a, b in runs:
        name = {"F": "亮绿", ".": "暗", " ": "其它"}[c]
        if b - a + 1 >= 3 or c == "F":
            print("  %s  %d..%d  (宽 %d)" % (name, a, b, b - a + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
