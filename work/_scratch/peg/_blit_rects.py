"""统计 DDrawCompat trace 日志里 Blt/BltFast/Flip 的矩形尺寸分布（只读）。"""
import re
import os
import collections
import sys

LOG = sys.argv[1] if len(sys.argv) > 1 else r"D:\Program Files\PeG\DDrawCompat-PeG030.log"

rx = re.compile(r"IDirectDrawSurface4Vtbl::(BltFast|Blt|Flip)\((.*)\)\s*$")
rect = re.compile(r"\*\{(-?\d+),(-?\d+),(-?\d+),(-?\d+)\}")

tally = collections.Counter()
big = collections.Counter()
flips = collections.Counter()
lines = 0

with open(LOG, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        if not line.startswith(">"):
            continue
        m = rx.search(line.rstrip())
        if not m:
            continue
        lines += 1
        meth, args = m.group(1), m.group(2)
        rs = rect.findall(args)
        if meth == "Flip":
            flips[args.strip()[:80]] += 1
            continue
        if len(rs) >= 2:
            l, t, r, b = map(int, rs[1])
            w, h = r - l, b - t
            tally[(meth, w, h)] += 1
            if w >= 900 or h >= 700:
                big[(meth, w, h, rs[0], rs[1])] += 1

print("Blt/BltFast/Flip 行数 =", lines)
print("---- 尺寸 top25 ----")
for (m_, w, h), c in tally.most_common(25):
    print("  %-8s %4dx%-4d  x%d" % (m_, w, h, c))
print("---- 大尺寸 (>=900 宽 或 >=700 高) ----")
for (m_, w, h, dst, src), c in big.most_common(25):
    print("  %-8s %4dx%-4d dst%s src%s  x%d" % (m_, w, h, dst, src, c))
print("---- Flip ----")
for a, c in flips.most_common(10):
    print("  %s  x%d" % (a, c))
