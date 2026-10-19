# -*- coding: utf-8 -*-
"""截图几何取证：定位「未被绘制/花屏」区域，并给出内容区原点估计。

用法：
    python probe_shot.py <png> [预览起始x]

判据（针对 DDraw 16bpp 未初始化表面 + 洋红/绿花屏）：
  - 纯黑列比例高  → 该列从未被绘制
  - 洋红/绿主色列比例高 → 花屏（表面残留像素）
输出只打「变化点」，避免刷屏。
"""
import sys

from PIL import Image


def classify(p):
    r, g, b = p
    if r < 12 and g < 12 and b < 12:
        return "black"
    if r > 180 and b > 180 and g < 90:
        return "magenta"
    if g > 180 and r < 120 and b < 120:
        return "green"
    return "other"


def main():
    path = sys.argv[1]
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    print("图 %s  %dx%d" % (path, w, h))

    y0, y1 = 36, h - 8          # 避开桌面/窗口边框
    x0, x1 = 8, w - 4

    prev = None
    print("\n[按列] x, 黑%, 洋红%, 绿%  —— 只在类别明显变化时打印")
    for x in range(x0, x1):
        n = y1 - y0
        c = {"black": 0, "magenta": 0, "green": 0}
        for y in range(y0, y1):
            k = classify(px[x, y])
            if k in c:
                c[k] += 1
        tag = "undrawn" if c["black"] > n * 0.5 else (
            "garbage" if (c["magenta"] + c["green"]) > n * 0.15 else "drawn")
        if tag != prev:
            print("  x=%-5d %-8s black=%3d%% magenta=%3d%% green=%3d%%" % (
                x, tag, 100 * c["black"] // n, 100 * c["magenta"] // n,
                100 * c["green"] // n))
            prev = tag

    prev = None
    print("\n[按行] y, 黑%, 洋红%, 绿%  —— 只在类别明显变化时打印")
    for y in range(y0, y1):
        n = x1 - x0
        c = {"black": 0, "magenta": 0, "green": 0}
        for x in range(x0, x1):
            k = classify(px[x, y])
            if k in c:
                c[k] += 1
        tag = "undrawn" if c["black"] > n * 0.5 else (
            "garbage" if (c["magenta"] + c["green"]) > n * 0.15 else "drawn")
        if tag != prev:
            print("  y=%-5d %-8s black=%3d%% magenta=%3d%% green=%3d%%" % (
                y, tag, 100 * c["black"] // n, 100 * c["magenta"] // n,
                100 * c["green"] // n))
            prev = tag

    ys = [120, 300, 500]
    for y in ys:
        row = ["%d:%s" % (x, "".join(
            "%02x" % v for v in px[x, y]))for x in range(760, w, 16)]
        print("\n[采样行 y=%d] %s" % (y, " ".join(row)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
