# -*- coding: utf-8 -*-
"""只读：列出 .text 里所有引用给定绝对地址（可多个，十六进制）的位置。"""
import struct
import sys

EXE = r"D:\Program Files\PeG\PeG030.exe"
data = open(EXE, "rb").read()
pe = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, pe + 6)[0]
opt = pe + 24
imgbase = struct.unpack_from("<I", data, opt + 28)[0]
off = opt + struct.unpack_from("<H", data, pe + 20)[0]
for i in range(nsec):
    s = off + i * 40
    name = data[s:s + 8].rstrip(bytes([0])).decode("latin1")
    vsize, rva, rawsize, rawptr = struct.unpack_from("<IIII", data, s + 8)
    if name == ".text":
        t0, t1, tva = rawptr, rawptr + rawsize, imgbase + rva
        break

for arg in sys.argv[1:]:
    target = int(arg, 16)
    pat = struct.pack("<I", target)
    hits = []
    start = t0
    while True:
        i = data.find(pat, start)
        if i < 0 or i >= t1:
            break
        start = i + 1
        hits.append(i)
    print("== refs to 0x%08X : %d" % (target, len(hits)))
    for i in hits:
        va = tva + (i - t0)
        print("   0x%08X  ctx=%s" % (va, data[max(0, i - 10):i + 10].hex(" ")))
