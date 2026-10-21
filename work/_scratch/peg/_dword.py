# -*- coding: utf-8 -*-
"""只读：在整个文件里精确查找若干 dword 值（十六进制），报告所在节。"""
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
secs = []
for i in range(nsec):
    s = off + i * 40
    name = d[s:s + 8].rstrip(bytes([0])).decode("latin1")
    vsize, rva, rawsize, rawptr = struct.unpack_from("<IIII", d, s + 8)
    secs.append((name, rawptr, rawptr + rawsize, imgbase + rva))

for arg in sys.argv[1:]:
    val = int(arg, 16)
    pat = struct.pack("<I", val)
    hits = []
    start = 0
    while True:
        i = d.find(pat, start)
        if i < 0:
            break
        start = i + 1
        sec = "?"
        for name, a, b, va in secs:
            if a <= i < b:
                sec = name
                break
        hits.append((i, sec))
    print("== 0x%08X: %d 处" % (val, len(hits)))
    for i, sec in hits[:20]:
        print("   fo=0x%-6X %-7s" % (i, sec))
