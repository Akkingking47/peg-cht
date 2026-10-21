# -*- coding: utf-8 -*-
"""只读：打印 PE 节表。"""
import struct
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import hint_pe as H

d = H.load(H.SRC)
pe = struct.unpack_from("<I", d, 0x3C)[0]
nsec = struct.unpack_from("<H", d, pe + 6)[0]
opt = pe + 24
imgbase = struct.unpack_from("<I", d, opt + 28)[0]
off = opt + struct.unpack_from("<H", d, pe + 20)[0]
print("ImageBase=0x%X  sections=%d" % (imgbase, nsec))
for i in range(nsec):
    s = off + i * 40
    name = d[s:s + 8].rstrip(bytes([0])).decode("latin1")
    vsize, rva, rawsize, rawptr = struct.unpack_from("<IIII", d, s + 8)
    chars = struct.unpack_from("<I", d, s + 36)[0]
    print("  %-8s VA=0x%08X vsize=0x%-7X raw=0x%-7X..0x%-7X flags=0x%08X" %
          (name, imgbase + rva, vsize, rawptr, rawptr + rawsize, chars))
