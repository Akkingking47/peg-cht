# -*- coding: utf-8 -*-
"""只读：在整个文件里找指向 [lo,hi) 区间的 4 字节指针（函数指针表/vtable 用）。"""
import struct
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import hint_pe as H

d = H.load(H.SRC)
lo = int(sys.argv[1], 16)
hi = int(sys.argv[2], 16)
print("搜索指向 0x%06X..0x%06X 的指针" % (lo, hi))
n = 0
for i in range(0, len(d) - 4):
    v = struct.unpack_from("<I", d, i)[0]
    if lo <= v < hi:
        va = None
        try:
            va = H.fo_to_va(i)
        except Exception:
            va = None
        print("   fo=0x%X  va=%s  -> 0x%06X" % (i, ("0x%06X" % va) if va else "?", v))
        n += 1
print("共 %d 处" % n)
