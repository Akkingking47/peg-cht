# -*- coding: utf-8 -*-
"""Dump record tables (read-only).

usage: python peek_table.py [exe] [va1] [va2] ...
Default exe = 母本; prints n entries per table as 9 words and 9 dwords.
"""
import struct
import sys

import pefile

EXE = sys.argv[1] if len(sys.argv) > 1 else r"D:\Program Files\PeG\PeG030.exe"
TABLES = [int(x, 16) for x in sys.argv[2:]] or [0x4A22F8]

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    secs.append((base + s.VirtualAddress, s.get_data(),
                 max(s.Misc_VirtualSize, s.SizeOfRawData)))


def rd(va, n):
    for a, d, sz in secs:
        if a <= va < a + sz:
            o = va - a
            b = d[o:o + n]
            if len(b) < n:          # 未初始化(.bss)部分按 0 补
                b = b + b"\x00" * (n - len(b))
            return b
    return b"\x00" * n


def dw(va):
    return struct.unpack('<I', rd(va, 4))[0]


def wo(va):
    return struct.unpack('<H', rd(va, 2))[0]


print("exe = %s" % EXE)
print("[0x4cce2c] = 0x%08x   count@0x4af460 = %d" % (dw(0x4cce2c), wo(0x4af460)))
for t in TABLES:
    print("=== table 0x%08x (36B/entry) ===" % t)
    for i in range(16):
        b = rd(t + i * 0x24, 0x24)
        if not b or len(b) < 0x24:
            break
        ws = struct.unpack('<18H', b)
        ds = struct.unpack('<9I', b)
        print("  idx%-2d W %s" % (i, " ".join("%5d" % x for x in ws[:10])))
        print("        D %s" % " ".join("%8d" % x for x in ds))
