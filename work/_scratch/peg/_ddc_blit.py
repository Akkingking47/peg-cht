# -*- coding: utf-8 -*-
"""统计 DDrawCompat trace 日志里的位块调用：源矩形是否越出地图面、哪一笔失败。

用法：
    python work/peg/_ddc_blit.py [日志路径]
默认路径 D:/Program Files/PeG/DDrawCompat-PeG030.log

要点：
  * DDrawCompat trace 每次调用两行——`> IDirectDrawSurface4Vtbl::BltFast(...)` 带参数，
    紧跟 ` < ... = <返回值>`；用「最近一个 > 行」回填返回值。
  * Blt/BltFast 的参数里第一个 `*{l,t,r,b,...}` 是 bltFx/destRect，最后一个 `*{l,t,r,b,...}`
    是源矩形（BltFast 为 `*{l,t,r,b}` 形式）。两种都打印，便于人眼判断。
  * 地图面在母本里是 1920x1920（M 组补丁后是 4096x4096），源矩形一旦超界，DirectDraw 整笔拒绝。
"""
import collections
import io
import re
import sys

LOG = sys.argv[1] if len(sys.argv) > 1 else r"D:\Program Files\PeG\DDrawCompat-PeG030.log"

re_call = re.compile(r">\s+IDirectDraw\w*Vtbl::(\w+)\(")
re_rect = re.compile(r"\*\{(-?\d+),(-?\d+),(-?\d+),(-?\d+)")
re_ret = re.compile(r"<\s.*?=\s*(\S+)\s*$")

counts = collections.Counter()
rect_counts = collections.Counter()     # (method, rect) -> n
oob = collections.Counter()             # (method, rect, limit) -> n
fails = collections.Counter()           # (method, rect, ret) -> n
create_dims = collections.Counter()
pending_method = None
pending_rect = None
nline = 0

with io.open(LOG, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        nline += 1
        m = re_call.search(line)
        if m:
            method = m.group(1)
            counts[method] += 1
            pending_method = method
            rs = re_rect.findall(line)
            pending_rect = rs[-1] if rs else None
            if pending_rect:
                rect_counts[(method, pending_rect)] += 1
            if method == "CreateSurface":
                # 优先记 dwHeight/dwWidth 那两个 0x 数字
                hexes = re.findall(r"0x([0-9a-fA-F]{2,8})", line)
                create_dims[tuple(hexes[:12])] += 1
            continue
        m = re_ret.search(line)
        if m and pending_method:
            ret = m.group(1)
            ok = ret in ("0", "0x0") or "OK" in ret.upper()
            if not ok:
                fails[(pending_method, pending_rect, ret)] += 1
            if pending_rect and pending_method in ("Blt", "BltFast"):
                l, t, r, b = (int(x) for x in pending_rect)
                for lim in (1920, 4096):
                    if r > lim or b > lim:
                        oob[(pending_method, pending_rect, lim)] += 1
            pending_method = None
            pending_rect = None

print("日志行数：%d" % nline)
print("\n== 调用次数 ==")
for k, v in counts.most_common(20):
    print("  %-24s %d" % (k, v))

print("\n== Blt/BltFast 的源矩形分布（前 25）==")
shown = 0
for (mth, rect), n in rect_counts.most_common():
    if mth not in ("Blt", "BltFast"):
        continue
    print("  %-8s %-28s x%d" % (mth, rect, n))
    shown += 1
    if shown >= 25:
        break

print("\n== 源矩形超界统计 ==")
if not oob:
    print("  （无：所有 Blt/BltFast 的源矩形都在 1920 以内）")
for (mth, rect, lim), n in sorted(oob.items(), key=lambda kv: -kv[1])[:25]:
    print("  %-8s %-28s 超出 %d  x%d" % (mth, rect, lim, n))

print("\n== 失败的调用（非 0 返回，前 25）==")
if not fails:
    print("  （无失败返回）")
for (mth, rect, ret), n in fails.most_common(25):
    print("  %-24s %-28s ret=%-14s x%d" % (mth, rect, ret, n))

print("\n== CreateSurface 参数（前 8 种）==")
for hexes, n in create_dims.most_common(8):
    print("  x%-5d %s" % (n, ",".join("0x" + h for h in hexes)))
