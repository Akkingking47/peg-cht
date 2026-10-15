# -*- coding: utf-8 -*-
"""在截图里逐像素读一行，做「亮绿框 / 暗底 / 其它」分类，用来判定按钮是被“拉伸”还是被“平铺”。

坐标换算（本机实测）：content_x = shot_x - 8，content_y = shot_y - 20。
用法：
    python probe_row.py <png> <content_y> <content_x0> <content_x1>
"""
import sys

from PIL import Image

NORM = {"/": 0}


def cls(p):
    r, g, b = p[:3]
    if g > 140 and r < 130 and b < 130:
        return "F"          # 亮绿（按钮外框/图标）
    if r + g + b < 170:
        return "."          # 暗（按钮内底/黑）
    return " "              # 其它（地形等）


def main():
    png, cy, cx0, cx1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    img = Image.open(png).convert("RGB")
    oy, ox = 20, 8
    row = [cls(img.getpixel((ox + x, oy + cy))) for x in range(cx0, cx1)]
    print("%s  content_y=%d  content_x=%d..%d" % (png, cy, cx0, cx1))
    for i in range(0, len(row), 100):
        chunk = row[i:i + 100]
        print("  x=%4d |%s|" % (cx0 + i, "".join(chunk)))
    print("  图例: F=亮绿  .=暗  (空格)=其它")
    return 0


if __name__ == "__main__":
    sys.exit(main())
