# -*- coding: utf-8 -*-
"""只读：扫 .text 里所有 imul reg,reg,0x24（控件记录步长 36）的指令，以及 imul ...,0x1c。"""
import struct

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

for stride in (0x24, 0x1C):
    print("== imul ...,0x%02X 的 6B /r ib 形式 ==" % stride)
    n = 0
    i = t0
    while i < t1 - 3:
        if data[i] == 0x6B and data[i + 2] == stride and (data[i + 1] & 0xC0) == 0xC0:
            print("   0x%08X  modrm=%02X  %s" % (tva + (i - t0), data[i + 1], data[i:i + 3].hex(" ")))
            n += 1
        i += 1
    print("   共 %d 处" % n)
