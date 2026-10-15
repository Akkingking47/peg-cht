# -*- coding: utf-8 -*-
"""列出全局 0x11951B0(语言目录) 的所有 .text 引用点，反汇编上下文并标注字符串。"""
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
        if sva <= r < sva + vsz:
            return f + (r - sva)
    return None
def fo2va(fo):
    for nm, sva, vsz, f, rsz in secs:
        if f <= fo < f + rsz:
            return imgbase + sva + (fo - f)
    return None
def read_cstr(va, maxlen=90):
    fo = va2fo(va)
    if fo is None: return None
    e = b.find(b"\0", fo)
    if e < 0: return None
    raw = b[fo:e]
    if not raw or len(raw) > maxlen or any(x < 9 or (13 < x < 32) or x > 126 for x in raw):
        return None
    return raw.decode("latin1")

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

GV = 0x11951B0
pat = struct.pack("<I", GV)
hits = []
st = 0
while True:
    i = b.find(pat, st)
    if i < 0: break
    va = fo2va(i)
    if va and 0x401000 <= va < 0x878000:
        hits.append(va)
    st = i + 1
print(f"全局 0x{GV:X} (.text) 引用 {len(hits)} 处\n")

SEC = 0x878000
for va in hits:
    ins_va = va - 2   # 多数指令 opcode+modrm 共 2 字节前缀
    fo = va2fo(va - 16)
    code = b[fo:fo + 48]
    lines = []
    target_line = None
    for ins in md.disasm(code, va - 16):
        ann = ""
        for op in ins.operands:
            if op.type == 2:
                s = read_cstr(op.imm & 0xFFFFFFFF)
                if s:
                    ann = f'  ; "{s}"'
        ln = f"{ins.mnemonic:<7s} {ins.op_str}{ann}"
        lines.append(ln)
        if ins.address <= va < ins.address + ins.size:
            target_line = len(lines) - 1
    print(f"--- ref @0x{va:08X} ---")
    lo = max(0, (target_line or 0) - 5)
    hi = min(len(lines), (target_line or 0) + 6)
    for k in range(lo, hi):
        mark = " <==" if k == target_line else ""
        print(f"    0x{va-16+0:08X}  {lines[k]}{mark}")
    print()
