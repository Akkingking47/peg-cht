# -*- coding: utf-8 -*-
import pathlib, struct, sys
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
def read_cstr(va, maxlen=100):
    fo = va2fo(va)
    if fo is None: return None
    e = b.find(b"\0", fo)
    if e < 0: return None
    raw = b[fo:e]
    if not raw or len(raw) > maxlen or any(x < 9 or (13 < x < 32) or x > 126 for x in raw): return None
    return raw.decode("latin1")
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True
for nm, sva, vsz, f, rsz in secs:
    if nm == ".text": T0, T1 = f, f + rsz

def callers(target):
    out = []
    for i in range(T0, T1 - 5):
        if b[i] == 0xE8:
            rel = struct.unpack_from("<i", b, i + 1)[0]
            if fo2va(i) + 5 + rel == target:
                out.append(fo2va(i))
    return out

for tgt in (int(sys.argv[1], 16),):
    cs = callers(tgt)
    print(f"### call 0x{tgt:X} → {len(cs)} 处: {[hex(c) for c in cs]}\n")
    for va in cs:
        fo = va2fo(va - 40)
        print(f"--- @0x{va:X} ---")
        for ins in md.disasm(b[fo:fo+72], va - 40):
            ann = ""
            for op in ins.operands:
                if op.type == 2:
                    s = read_cstr(op.imm & 0xFFFFFFFF)
                    if s: ann = f'  ; "{s}"'
            mk = " <==" if ins.address == va else ""
            print(f"    0x{ins.address:08X}  {ins.mnemonic:<7s} {ins.op_str}{ann}{mk}")
        print()
