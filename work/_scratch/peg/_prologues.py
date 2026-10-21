# -*- coding: utf-8 -*-
"""只读：在 [lo,hi) 内列出 55 8b ec 序言候选。"""
import struct
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import hint_pe as H

d = H.load(H.SRC)
lo = int(sys.argv[1], 16)
hi = int(sys.argv[2], 16)
fo0 = H.va_to_fo(lo)
fo1 = H.va_to_fo(hi)
n = 0
for i in range(fo0, fo1 - 3):
    if d[i] == 0x55 and d[i + 1] == 0x8B and d[i + 2] == 0xEC:
        print("0x%06X" % H.fo_to_va(i))
        n += 1
print("共 %d 处" % n)
