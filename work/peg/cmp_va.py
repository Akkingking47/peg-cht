# -*- coding: utf-8 -*-
"""cmp_va.py — 母本 vs 产物 指定 VA 的字节/立即数对比（只读）

用法：
    python cmp_va.py show 0x4421d4 0x4421de            # 打印两文件在该 VA 的 4/8 字节
    python cmp_va.py scan 0x41c000 0x421000 0x320 0x258 # 在 [lo,hi) 内找 dword 等于给定值的点
    python cmp_va.py diff 0x41c000 0x421000            # 列出区间内所有字节差异
    python cmp_va.py imm  0x41c000 0x421000            # 列出区间内所有 4 字节立刻数差异（母本值 -> 产物值）
"""
import struct
import sys

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
import os
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


MOTHER = os.path.join(GAME, "PeG030.exe")
PROD = os.path.join(WS, "work", "peg", "out", "PeG030-1920x1080.exe")
BASE = 0x400000


def load(path):
    with open(path, "rb") as f:
        data = f.read()
    e = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e + 6)[0]
    opt = struct.unpack_from("<H", data, e + 20)[0]
    sec0 = e + 24 + opt
    secs = []
    for i in range(nsec):
        off = sec0 + i * 40
        name = data[off:off + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, off + 8)
        secs.append((name, va, max(vsize, rawsize), raw))
    return bytearray(data), secs


def v2o(secs, va):
    rva = va - BASE
    for name, sva, sz, raw in secs:
        if sva <= rva < sva + sz:
            return raw + (rva - sva), name
    return None, None


def main():
    mode = sys.argv[1]
    m, ms = load(MOTHER)
    p, ps = load(PROD)
    if mode == "show":
        for a in sys.argv[2:]:
            va = int(a, 16)
            mo, _ = v2o(ms, va)
            po, _ = v2o(ps, va)
            print("VA 0x%08x  mother %s | prod %s" % (
                va, m[mo:mo + 8].hex(" "), p[po:po + 8].hex(" ")))
        return
    lo, hi = int(sys.argv[2], 16), int(sys.argv[3], 16)
    mlo, _ = v2o(ms, lo)
    plo, _ = v2o(ps, lo)
    n = hi - lo
    if mode == "scan":
        vals = set(int(x, 16) for x in sys.argv[4:])
        for i in range(0, n - 4, 1):
            mv = struct.unpack_from("<I", m, mlo + i)[0]
            pv = struct.unpack_from("<I", p, plo + i)[0]
            if mv in vals or pv in vals:
                print("imm@0x%08x  mother=0x%x(%d)  prod=0x%x(%d)" % (lo + i, mv, mv, pv, pv))
    elif mode == "diff":
        i = 0
        while i < n:
            if m[mlo + i] != p[plo + i]:
                j = i
                while j < n and m[mlo + j] != p[plo + j]:
                    j += 1
                print("diff 0x%08x..0x%08x  mother %s | prod %s" % (
                    lo + i, lo + j - 1, m[mlo + i:mlo + j].hex(" "), p[plo + i:plo + j].hex(" ")))
                i = j
            else:
                i += 1
    elif mode == "imm":
        for i in range(0, n - 4):
            if m[mlo + i:mlo + i + 4] == p[plo + i:plo + i + 4]:
                continue
            if i > 0 and m[mlo + i - 1:mlo + i + 3] == p[plo + i - 1:plo + i + 3]:
                continue
            if i + 4 < n and m[mlo + i + 1:mlo + i + 5] == p[plo + i + 1:plo + i + 5]:
                continue
            mv = struct.unpack_from("<I", m, mlo + i)[0]
            pv = struct.unpack_from("<I", p, plo + i)[0]
            if mv < 0x10000 or pv < 0x10000:
                print("dword@0x%08x  mother=%d/0x%x  prod=%d/0x%x" % (lo + i, mv, mv, pv, pv))


if __name__ == "__main__":
    main()
