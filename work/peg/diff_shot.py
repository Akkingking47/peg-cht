# -*- coding: utf-8 -*-
"""比较两张同尺寸截图，给出差异的边界框 + 粗网格分布。

用途：判断某个 exe 变体到底在画面上改了什么（避免凭肉眼印象下结论）。
用法：
    python diff_shot.py a.png b.png [--cell 40] [--tol 8] [--top 20]

输出：
  - 差异像素总数、占比、整体 bbox
  - 每个网格单元内差异像素数（只列非零单元，按数量降序）
--tol 是通道容差（默认 8，滤掉抖动/抖动压缩噪声）。
"""
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("需要 pillow：python -m pip install pillow")


def main():
    args = sys.argv[1:]
    cell = 40
    tol = 8
    top = 20
    files = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--cell":
            cell = int(args[i + 1]); i += 2; continue
        if a == "--tol":
            tol = int(args[i + 1]); i += 2; continue
        if a == "--top":
            top = int(args[i + 1]); i += 2; continue
        files.append(a); i += 1
    if len(files) != 2:
        sys.exit(__doc__)

    ia = Image.open(files[0]).convert("RGB")
    ib = Image.open(files[1]).convert("RGB")
    if ia.size != ib.size:
        print("尺寸不同：%s %s vs %s %s" % (files[0], ia.size, files[1], ib.size))
        sys.exit(1)
    w, h = ia.size
    pa = ia.load()
    pb = ib.load()

    cells = {}
    n = 0
    x0 = y0 = 10 ** 9
    x1 = y1 = -1
    for y in range(h):
        for x in range(w):
            ra, ga, ba = pa[x, y]
            rb, gb, bb = pb[x, y]
            if abs(ra - rb) > tol or abs(ga - gb) > tol or abs(ba - bb) > tol:
                n += 1
                if x < x0: x0 = x
                if y < y0: y0 = y
                if x > x1: x1 = x
                if y > y1: y1 = y
                key = (x // cell, y // cell)
                cells[key] = cells.get(key, 0) + 1

    print("A = %s" % files[0])
    print("B = %s" % files[1])
    print("尺寸 %dx%d  cell=%d  tol=%d" % (w, h, cell, tol))
    print("差异像素 %d / %d (%.2f%%)" % (n, w * h, 100.0 * n / (w * h)))
    if n:
        print("整体 bbox  x %d..%d  y %d..%d" % (x0, x1, y0, y1))
        print("差异网格（cell 左上角内容坐标 = (cellx*%d-8, celly*%d-31)）:" % (cell, cell))
        for key, cnt in sorted(cells.items(), key=lambda kv: -kv[1])[:top]:
            cx, cy = key
            print("  cell(%2d,%2d) 内容(%4d,%4d) 差异 %6d" % (cx, cy, cx * cell - 8, cy * cell - 31, cnt))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
