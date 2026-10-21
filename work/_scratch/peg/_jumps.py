# -*- coding: utf-8 -*-
"""只读：找出 .text 里所有 call/jmp（E8/E9）目标落在 [lo,hi) 或等于目标的调用点。"""
import struct
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import hint_pe as H

d = H.load(H.SRC)
lo = int(sys.argv[1], 16)
hi = int(sys.argv[2], 16)
t0 = 0x401000
t1 = 0x48A600
fo = H.va_to_fo(t0)

hits = []
i = fo
while i < fo + (t1 - t0) - 5:
    if d[i] in (0xE8, 0xE9):
        rel = struct.unpack_from("<i", d, i + 1)[0]
        va = t0 + (i - fo)
        tgt = va + 5 + rel
        if lo <= tgt < hi:
            hits.append((va, d[i], tgt))
    i += 1
print("== call/jmp 落到 0x%06X..0x%06X：%d 处 ==" % (lo, hi, len(hits)))
for va, op, tgt in hits:
    print("   0x%06X %s -> 0x%06X" % (va, "call" if op == 0xE8 else "jmp ", tgt))
