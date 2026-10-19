# -*- coding: utf-8 -*-
"""按钮几何取证：在给定截图与给定行上，找出「绿色边框」的水平连续段。

工具列按钮的外框是纯绿色，背景是地图/深色内部，因此按颜色找段即可精确量出
按钮矩形的左右边界（截图坐标 = 桌面坐标；内容坐标 = 截图坐标 - 原点）。

用法：
    python probe_btn.py <png> y1,y2,...   [原点x=8]
"""
import sys

from PIL import Image


def is_frame(p):
    r, g, b = p
    return g > 110 and g - r > 45 and g - b > 45


def runs(px, y, x0, x1, pred, minlen=2):
    out = []
    start = None
    for x in range(x0, x1):
        if pred(px[x, y]):
            if start is None:
                start = x
        else:
            if start is not None:
                if x - start >= minlen:
                    out.append((start, x - 1))
                start = None
    if start is not None and x1 - start >= minlen:
        out.append((start, x1 - 1))
    return out


def main():
    path = sys.argv[1]
    ys = [int(v) for v in sys.argv[2].split(",")]
    ox = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    im = Image.open(path).convert("RGB")
    px = im.load()
    print("图 %s  %dx%d  内容原点x=%d" % (path, im.width, im.height, ox))
    for y in ys:
        rs = runs(px, y, 700, im.width - 4, is_frame)
        desc = " | ".join("%d..%d(内容%d..%d,宽%d)" % (
            a, b, a - ox, b - ox, b - a + 1) for a, b in rs)
        print("  y=%-4d %s" % (y, desc or "无绿色段"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
