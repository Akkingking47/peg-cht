# -*- coding: utf-8 -*-
"""只读：列出母本 .text 里对给定函数地址（可多个，十六进制）的直接 call 点。"""
import struct
import sys

EXE = r"D:\Program Files\PeG\PeG030.exe"

data = open(EXE, "rb").read()
pe = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, pe + 6)[0]
opt = pe + 24
imgbase = struct.unpack_from("<I", data, opt + 28)[0]
off = opt + struct.unpack_from("<H", data, pe + 20)[0]
t0 = t1 = tva = 0
for i in range(nsec):
    s = off + i * 40
    name = data[s:s + 8].rstrip(bytes([0])).decode("latin1")
    vsize, rva, rawsize, rawptr = struct.unpack_from("<IIII", data, s + 8)
    if name == ".text":
        t0, t1, tva = rawptr, rawptr + rawsize, imgbase + rva
        break

print("text raw 0x%X..0x%X va 0x%X" % (t0, t1, tva))
for arg in sys.argv[1:]:
    target = int(arg, 16)
    hits = []
    for i in range(t0, t1 - 5):
        if data[i] == 0xE8:
            rel = struct.unpack_from("<i", data, i + 1)[0]
            va = tva + (i - t0)
            if va + 5 + rel == target:
                hits.append(va)
    print("== callers of 0x%08X : %d" % (target, len(hits)))
    for va in hits:
        print("   0x%08X" % va)
