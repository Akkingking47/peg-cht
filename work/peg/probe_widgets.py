# -*- coding: utf-8 -*-
"""解码「UI 控件记录表」：把母本与产物在同一基址上的记录逐条列出并标出差异。

记录布局（由 0x43ff28 命中测试与 0x41c444 标志操作反推，已实证）：
    +0 u16 flags   +2 i16 x   +4 i16 y   +6 i16 right   +8 i16 bottom
    步长 36 字节（0x24），代码里是 imul reg, reg, 0x24 后 [reg + base]

用法：
    python probe_widgets.py [base_hex] [count]
"""
import os
import struct
import sys

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


ORIG = os.path.join(GAME_ALT, "PeG030.exe")
PROD = os.path.join(GAME_ALT, "PeG030res.exe")

SECTIONS = [(".text", 0x401000, 0x400, 565760), (".rdata", 0x48C000, 0x8A600, 4608),
            (".data", 0x48E000, 0x8B800, 136192), (".idata", 0x6AA000, 0xACC00, 5632),
            (".rsrc", 0x6AC000, 0xAE200, 21504)]


def va2fo(va):
    for _n, sva, raw, size in SECTIONS:
        if sva <= va < sva + size:
            return va - sva + raw
    raise ValueError("VA 0x%x 不在已知节内" % va)


def load(path):
    with open(path, "rb") as f:
        return f.read()


def main():
    base = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x490470
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    stride = 0x24
    a, b = load(ORIG), load(PROD)
    print("记录表基址 0x%x 步长 %d 共 %d 条" % (base, stride, n))
    print("idx  VA        flags  x     y     right bottom | 母本→产物变化")
    ndiff = 0
    for i in range(n):
        va = base + i * stride
        fo = va2fo(va)
        ra, rb = a[fo:fo + stride], b[fo:fo + stride]
        fa = struct.unpack("<5h", ra[:10])
        fb = struct.unpack("<5h", rb[:10])
        changed = []
        for k, (name, _o, _f) in enumerate([("flags", 0, 0), ("x", 0, 0), ("y", 0, 0),
                                            ("right", 0, 0), ("bottom", 0, 0)]):
            if fa[k] != fb[k]:
                changed.append("%s %d→%d" % (name, fa[k], fb[k]))
        if ra[10:] != rb[10:]:
            changed.append("尾字节(%d处不同)" % 0)
        if changed:
            ndiff += 1
        print("%3d  0x%06x  %5d %5d %5d %5d %5d | %s" % (
            i, va, fb[0], fb[1], fb[2], fb[3], fb[4],
            "; ".join(changed) if changed else ""))
        if changed:
            print("        母本原始: flags=%d x=%d y=%d right=%d bottom=%d" % tuple(fa))
        if ra[10:] != rb[10:]:
            print("        尾字节 母本: %s" % ra[10:].hex(" "))
            print("        尾字节 产物: %s" % rb[10:].hex(" "))
    print("共 %d 条记录，其中 %d 条有差异（含只改尾字节的）" % (n, ndiff))
    return 0


if __name__ == "__main__":
    sys.exit(main())
