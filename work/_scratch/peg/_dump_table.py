# -*- coding: utf-8 -*-
"""_dump_table.py — 只读：按 8 字节记录 (dword ptr, dword extra) 打印数据表，并标注是否落在 .text。

用法: python _dump_table.py 0x494060 40
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


def va2off(va):
    r = va - imgbase
    for name, sva, vsize, rawptr, rawsize in secs:
        if sva <= r < sva + vsize:
            return rawptr + (r - sva), name
    return None, None


va = int(sys.argv[1], 16)
count = int(sys.argv[2]) if len(sys.argv) > 2 else 24
off, sec = va2off(va)
if off is None:
    print("VA 不在任何节里"); sys.exit(1)
print("VA %#010x 在 %s, 文件偏移 %#x" % (va, sec, off))
for i in range(count):
    o = off + i * 8
    p, e = struct.unpack_from("<II", data, o)
    _, psec = va2off(p) if p else (None, None)
    print("  [%2d] VA %#010x : ptr %#010x %-8s extra %#010x  (%d)" % (i, va + i * 8, p, psec or "-", e, e))
