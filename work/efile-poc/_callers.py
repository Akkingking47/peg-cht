# -*- coding: utf-8 -*-
import pathlib, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE = pathlib.Path(r"D:\OpenPG2\OpenGen.exe")
b = EXE.read_bytes()
pe = struct.unpack_from("<I", b, 0x3C)[0]
sizeopt = struct.unpack_from("<H", b, pe + 20)[0]
nsec = struct.unpack_from("<H", b, pe + 6)[0]
opt = pe + 24
imgbase = struct.unpack_from("<I", b, opt + 28)[0]
so = opt + sizeopt
secs = []
for i in range(nsec):
    off = so + i * 40
    nm = b[off:off+8].rstrip(b"\0").decode("latin1")
    vsz, va, rsz, fo = struct.unpack_from("<IIII", b, off + 8)
    secs.append((nm, va, vsz, fo, rsz))
def fo2va(fo):
    for nm, sva, vsz, f, rsz in secs:
        if f <= fo < f + rsz: return imgbase + sva + (fo - f)
def va2fo(va):
    r = va - imgbase
    for nm, sva, vsz, f, rsz in secs:
        if sva <= r < sva + vsz: return f + (r - sva)
def read_cstr(va, maxlen=90):
    fo = va2fo(va)
    if fo is None: return None
    e = b.find(b"\0", fo)
    if e < 0: return None
    raw = b[fo:e]
    if not raw or len(raw) > maxlen or any(x < 9 or (13 < x < 32) or x > 126 for x in raw): return None
    return raw.decode("latin1")
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True

TARGET = 0x7BF320
text_fo_end = None
for nm, sva, vsz, f, rsz in secs:
    if nm == ".text": text_fo_start, text_fo_end = f, f + rsz
calls = []
for i in range(text_fo_start, text_fo_end - 5):
    if b[i] == 0xE8:
        rel = struct.unpack_from("<i", b, i + 1)[0]
        tgt = fo2va(i) + 5 + rel
        if tgt == TARGET:
            calls.append(fo2va(i))
print(f"call 0x{TARGET:X} 命中 {len(calls)} 处:", [hex(c) for c in calls])
print()
for va in calls:
    fo = va2fo(va - 24)
    for ins in md.disasm(b[fo:fo+56], va - 24):
        ann = ""
        for op in ins.operands:
            if op.type == 2:
                s = read_cstr(op.imm & 0xFFFFFFFF)
                if s: ann = f'  ; "{s}"'
        mk = " <==" if ins.address == va else ""
        print(f"    0x{ins.address:08X}  {ins.mnemonic:<7s} {ins.op_str}{ann}{mk}")
    print()
