# -*- coding: utf-8 -*-
"""Peek the sprite/ctrl object at 0x663410: count, table ptr, first entries.

usage: python peek_ctrl.py [exe]
"""
import struct
import sys

import pefile

EXE = sys.argv[1] if len(sys.argv) > 1 else r"D:\Program Files\PeG\PeG030.exe"
OBJ = 0x663410
ESZ = 0x1C

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
secs = [(base + s.VirtualAddress, s.get_data(),
         max(s.Misc_VirtualSize, s.SizeOfRawData)) for s in pe.sections]


def rd(va, n):
    for a, d, sz in secs:
        if a <= va < a + sz:
            o = va - a
            b = d[o:o + n]
            return b + b"\x00" * (n - len(b))
    return b"\x00" * n


def dw(va):
    return struct.unpack("<I", rd(va, 4))[0]


cnt = dw(OBJ)
tab = dw(OBJ + 4)
print("exe = %s" % EXE)
print("ctrl@0x%08x  count=%d  table=0x%08x" % (OBJ, cnt, tab))
for i in range(min(cnt, 8)):
    d = struct.unpack("<7I", rd(tab + i * ESZ, ESZ))
    print("  idx%-2d  " % i + " ".join("%10d" % x for x in d))
print("dwords at OBJ: " + " ".join("%d" % dw(OBJ + i * 4) for i in range(6)))
