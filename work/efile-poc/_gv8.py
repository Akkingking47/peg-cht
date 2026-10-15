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
def va2fo(va):
    r = va - imgbase
    for nm, sva, vsz, f, rsz in secs:
        if sva <= r < sva + vsz: return f + (r - sva)
def fo2va(fo):
    for nm, sva, vsz, f, rsz in secs:
        if f <= fo < f + rsz: return imgbase + sva + (fo - f)
def read_cstr(va, maxlen=100):
    fo = va2fo(va)
    if fo is None: return None
    e = b.find(b"\0", fo)
    if e < 0: return None
    raw = b[fo:e]
    if not raw or len(raw) > maxlen or any(x < 9 or (13 < x < 32) or x > 126 for x in raw): return None
    return raw.decode("latin1")
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True
for nm, sva, vsz, f, rsz in secs:
    if nm == ".text": T0, T1 = f, f + rsz
GV = 0x11951A8
pat = struct.pack("<I", GV)
hits = []
st = 0
while True:
    i = b.find(pat, st)
    if i < 0: break
    st = i + 1
    v = fo2va(i)
    if v and 0x401000 <= v < 0x878000: hits.append(v)
print(f"### 全局 0x{GV:X} 在 .text 引用 {len(hits)} 处")
for v in hits:
    fo = va2fo(v - 20)
    insns = list(md.disasm(b[fo:fo+56], v-20))
    idx = None
    for k, ins in enumerate(insns):
        if ins.address <= v < ins.address + ins.size: idx = k; break
    print(f"\n  --- @0x{v:X} ---")
    for k in range(max(0,(idx or 0)-6), min(len(insns),(idx or 0)+3)):
        ins = insns[k]
        ann = ""
        for op in ins.operands:
            if op.type == 2:
                s = read_cstr(op.imm & 0xFFFFFFFF)
                if s: ann = f'  ; "{s}"'
        mk = " <==" if k == idx else ""
        print(f"      0x{ins.address:08X}  {ins.mnemonic:<7s} {ins.op_str}{ann}{mk}")
