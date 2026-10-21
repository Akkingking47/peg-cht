# -*- coding: utf-8 -*-
"""只读：找出 .text 里所有 call 目标落在 [lo,hi) 区间的调用点。"""
import struct
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import hint_pe as H

d = H.load(H.SRC)
lo = int(sys.argv[1], 16)
hi = int(sys.argv[2], 16)
fo = H.va_to_fo(0x401000)
tva = 0x401000
size = 0x8A600

hits = []
i = fo
while i < fo + size - 5:
    if d[i] == 0xE8:
        rel = struct.unpack_from("<i", d, i + 1)[0]
        va = tva + (i - fo)
        tgt = va + 5 + rel
        if lo <= tgt < hi:
            hits.append((va, tgt))
    i += 1
print("== call 落在 0x%06X..0x%06X 的调用点：%d 处 ==" % (lo, hi, len(hits)))
for va, tgt in hits:
    print("   caller 0x%06X -> 0x%06X" % (va, tgt))
