# -*- coding: utf-8 -*-
"""追踪某个运行时全局（如 0x11951A8）的写入点，判断它保存的是什么。

做法：
  1) 在 .text 里找该绝对地址的出现（任意指令形式：mov/lea/push/mov [imm],reg ...）；
  2) 对每个命中点向前/向后各反汇编一小段；
  3) 打印附近解析得出的字符串常量（用于判断文件名 / 路径模式）。
"""
import pathlib
import struct
import sys

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
    if e < 0:
        return None
    raw = b[fo:e]
    if not raw or len(raw) > maxlen:
        return None
    if any(x < 9 or (13 < x < 32) or x > 126 for x in raw):
        return None
    return raw.decode("latin1")


tn, tva, tvsz, tfo, trsz = next(s for s in secs if s[0] == ".text")
text = b[tfo:tfo + trsz]

from capstone import Cs, CS_ARCH_X86, CS_MODE_32  # noqa
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

target = int(sys.argv[1], 16)
pat = struct.pack("<I", target)
print("=== refs to 0x%08X ===" % target)
i = 0
sites = []
while True:
    i = text.find(pat, i)
    if i < 0:
        break
    sites.append(i)
    i += 1
print("total %d raw occurrences\n" % len(sites))

for off in sites:
    va = imgbase + tva + off
    lo = max(0, off - 0x40)
    blob = b[tfo + lo:tfo + off + 0x30]
    base_va = imgbase + tva + lo
    print("---- site 0x%08X ----" % va)
    for ins in md.disasm(blob, base_va):
        ann = ""
        for op in ins.operands:
            if op.type == 2:
                s = read_cstr(op.imm & 0xFFFFFFFF)
                if s:
                    ann = '   ; "%s"' % s
        mark = " <<<" if abs(ins.address - va) <= 6 else ""
        print("   0x%08X  %-22s %s %s%s%s" % (ins.address, ins.bytes.hex(" "),
                                              ins.mnemonic, ins.op_str, ann, mark))
    print()
