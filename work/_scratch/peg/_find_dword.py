# -*- coding: utf-8 -*-
"""_find_dword.py — 只读：在整个 exe 镜像里找某个 4 字节绝对地址（跳转表/函数指针）。

用法: python _find_dword.py 0x42D445 [0x42D464 ...]
"""
import struct
import sys
from pathlib import Path

EXE = Path(r"D:\Program Files\PeG\PeG030.exe")
data = EXE.read_bytes()
pe = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, pe + 6)[0]
sizeopt = struct.unpack_from("<H", data, pe + 20)[0]
opt = pe + 24
imgbase = struct.unpack_from("<I", data, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + sizeopt + i * 40
    name = data[o:o + 8].rstrip(b"\0").decode(errors="replace")
    vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
    secs.append((name, va, vsize, rawptr, rawsize))


def off2va(off):
    for name, va, vsize, rawptr, rawsize in secs:
        if rawptr <= off < rawptr + rawsize:
            return imgbase + va + (off - rawptr)
    return None


for arg in sys.argv[1:]:
    target = int(arg, 16)
    needle = struct.pack("<I", target)
    hits = []
    start = 0
    while True:
        i = data.find(needle, start)
        if i < 0:
            break
        hits.append((i, off2va(i)))
        start = i + 1
    print("=== %#010x : %d 处 ===" % (target, len(hits)))
    for off, va in hits[:24]:
        ctx = data[max(0, off - 16):off + 16]
        print("   file 0x%06X  VA %s  ctx=%s" % (off, ("%#010x" % va) if va else "?", ctx.hex(" ")))
