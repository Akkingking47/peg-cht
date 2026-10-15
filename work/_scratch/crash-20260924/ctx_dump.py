# -*- coding: utf-8 -*-
"""上下文勘察：给一段 FO，打印其前后内容 + 判断左右邻居像什么（float/VA/ASCII）。"""
import struct
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else r"D:\DSH\军事游戏汉化\backup\OpenGen.exe.original"
d = open(EXE, "rb").read()


def classify(v):
    f = struct.unpack("<f", struct.pack("<I", v))[0]
    if 0x400000 <= v < 0x1900000:
        return "VA"
    if abs(f) < 1e9 and f == f and abs(f) > 1e-6 and (abs(f) < 1e6):
        s = "%.4g" % f
        if s not in ("0",):
            return "flt:" + s
    if v < 0x10000:
        return "int:%d" % v
    return "-"


def dump(fo, before=48, after=64, title=""):
    print("\n===== %s  FO 0x%06X (VA 0x%08X) =====" % (title, fo, fo + 0x400E00))
    lo = fo - before
    for base in range(lo, fo + after, 16):
        row = d[base:base + 16]
        cells, cls = [], []
        for k in range(0, 16, 4):
            v = struct.unpack_from("<I", row, k)[0]
            cells.append("%08X" % v)
            cls.append(classify(v))
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
        pos = "".join("^" if base + i == fo else ("v" if base + 15 == fo + 0 else " ")
                      for i in range(16))
        print("  %06X %-16s |%s|  %s" % (base, " ".join(cells), asc, " ".join(cls)))


for target in sys.argv[2:]:
    fo = int(target, 0)
    dump(fo, 48, 64, "")

if len(sys.argv) == 1:
    dump(0x4B1C86, 48, 48, "现用空洞2 unitdlg")
    dump(0x4ECB39, 40, 56, "现用空洞 maphud")
    dump(0x51CB31, 56, 80, "踩坑空洞(LoadConfig)")
    dump(0x56F831, 64, 32, ".rdata 尾部候选")
    dump(0x570AC9, 48, 48, ".data 最大候选")
