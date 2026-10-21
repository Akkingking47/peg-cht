# -*- coding: utf-8 -*-
"""把分辨率/宽屏线在游戏目录里留下的入口与日志移入工作区归档（可回退，不做删除）。

不碰：PeG030.exe（母本，从未改动）· 汉化产物（Gui030.txt / Name030.txt / Equip30.txt /
MISC030.TXT / Text 等，日期 <=2026-10-12）· 游戏自带文件 · 存档 SAVE/ 与 MAP/。
"""
from __future__ import annotations

import hashlib
import os
import shutil
import time

PEG = r"D:\Program Files\PeG"
DEST = r"D:\DSH\军事游戏汉化\archive\PeG-16比9-入口-已停用-20261019"

MOVE = [
    "启动-16比9-内存版.cmd",
    "启动-16比9-重排版P1.cmd",
    "还原显示层.cmd",
    "进游戏-16比9-DDrawCompat试玩.cmd",
    "进游戏-16比9-DDrawCompat试玩.lnk",
    "进游戏-16比9宽屏.lnk",
    "说明-怎么进游戏.txt",
    "DDrawCompat-PeG030.log",
    "DDrawCompat-PeG030zh.log",
    "ddraw-Svens.dll.bak",
]

CUTOFF = time.mktime((2026, 10, 13, 0, 0, 0, 0, 0, 0))  # 宽屏线 10-13 开工


def md5(p):
    try:
        with open(p, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except OSError:
        return ""


def scan_after(start_ts):
    """列出游戏目录里 2026-10-13 之后被写过/建过的文件（含子目录），用来查有没有漏网残留。"""
    out = []
    for root, dirs, files in os.walk(PEG):
        for fn in files:
            p = os.path.join(root, fn)
            try:
                st = os.stat(p)
            except OSError:
                continue
            if st.st_mtime >= start_ts:
                out.append((st.st_mtime, os.path.relpath(p, PEG), st.st_size))
    out.sort(reverse=True)
    return out


def main():
    print("=== A. 移动前扫描：10-13 之后出现的文件 ===")
    before = scan_after(CUTOFF)
    for ts, rel, size in before:
        print("  %s  %10d  %s" % (time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)), size, rel))

    os.makedirs(DEST, exist_ok=True)
    print()
    print("=== B. 移入归档 %s ===" % DEST)
    moved = []
    for name in MOVE:
        src = os.path.join(PEG, name)
        if not os.path.exists(src):
            print("  (不存在，跳过) %s" % name)
            continue
        dst = os.path.join(DEST, name)
        digest = md5(src)
        shutil.move(src, dst)
        moved.append((name, digest))
        print("  ✓ %s  md5=%s" % (name, digest))

    print()
    print("=== C. 移动后复查：10-13 之后的文件 ===")
    after = scan_after(CUTOFF)
    if not after:
        print("  无（游戏目录已回到只有汉化产物与游戏自带文件的状态）")
    for ts, rel, size in after:
        print("  %s  %10d  %s" % (time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)), size, rel))

    print()
    print("=== D. 关键文件指纹（应与汉化交付时一致） ===")
    for fn in ("PeG030.exe", "ddraw.dll", "Gui030.txt", "Name030.txt", "Equip30.txt", "MISC030.TXT"):
        p = os.path.join(PEG, fn)
        print("  %-14s %s" % (fn, md5(p) if os.path.exists(p) else "(不存在)"))
    print()
    print("已移动 %d 个文件到归档（如需复原，把它们搬回 %s 即可）" % (len(moved), PEG))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
