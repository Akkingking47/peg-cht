# -*- coding: utf-8 -*-
"""列出所有「引用了某绝对地址」的指令（不限 push，含 mov/lea/cmp 等形式）。

对每个 4 字节出现位置，尝试从 ±8 字节内的每个起点反汇编，取那条字节区间
覆盖该出现位置的指令 —— 这样不必预先知道指令对齐。

  python _addrrefs.py 0x11951B0
"""
import pathlib
import struct
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = pathlib.Path(r"D:\OpenPG2\OpenGen.exe")
b = EXE.read_bytes()
pe = struct.unpack_from("<I", b, 0x3C)[0]
sizeopt = struct.unpack_from("<H", b, pe + 20)[0]
nsec = struct.unpack_from("<H", b, pe + 6)[0]
opt = pe + 24
imgbase = struct.unpack_from("<I", b, opt + 28)[0]
secs = []
for i in range(nsec):
    off = opt + sizeopt + i * 40
    nm = b[off:off + 8].rstrip(b"\0").decode("latin1")
    vsz, va, rsz, fo = struct.unpack_from("<IIII", b, off + 8)
    secs.append((nm, va, vsz, fo, rsz))


def va2fo(va):
    r = va - imgbase
    for nm, sva, vsz, f, rsz in secs:
        if sva <= r < sva + vsz:
            return f + (r - sva)
    return None


def fo2va(fo):
    for nm, sva, vsz, f, rsz in secs:
        if f <= fo < f + rsz:
            return imgbase + sva + (fo - f)
    return None


def read_cstr(va, maxlen=64):
    fo = va2fo(va)
    if fo is None:
        return None
    e = b.find(b"\0", fo)
    raw = b[fo:e]
    if not raw or len(raw) > maxlen:
        return None
    if any(x < 9 or (13 < x < 32) or x > 126 for x in raw):
        return None
    return raw.decode("latin1")


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
tn, tva, tvsz, tfo, trsz = next(s for s in secs if s[0] == ".text")
text = b[tfo:tfo + trsz]

target = int(sys.argv[1], 16)
pat = struct.pack("<I", target)

occs = []
i = 0
while True:
    i = text.find(pat, i)
    if i < 0:
        break
    occs.append(i)
    i += 1

print("=== 0x%08X : %d raw occurrences ===" % (target, len(occs)))
shapes = {}
for occ in occs:
    found = None
    for back in range(1, 12):
        start = occ - back
        if start < 0:
            continue
        blob = text[start:occ + 8]
        va0 = imgbase + tva + start
        for ins in md.disasm(blob, va0):
            end = (ins.address - va0) + len(ins.bytes)
            if ins.address - va0 <= back < end:
                found = ins
            break
        if found:
            break
    if not found:
        print("  0x%08X  <undecoded>" % (imgbase + tva + occ))
        continue
    ann = ""
    for op in found.operands:
        if op.type == 2:
            s = read_cstr(op.imm & 0xFFFFFFFF)
            if s:
                ann = '   ; "%s"' % s
    key = "%s %s" % (found.mnemonic, found.op_str)
    shapes[key] = shapes.get(key, 0) + 1
    print("  0x%08X  %-22s %-8s %-28s%s" % (found.address, found.bytes.hex(" "),
                                            found.mnemonic, found.op_str, ann))
print()
print("=== instruction shapes ===")
for k in sorted(shapes, key=lambda x: -shapes[x]):
    print("  %-40s x%d" % (k, shapes[k]))
