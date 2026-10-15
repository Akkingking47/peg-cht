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
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True
va0 = int(sys.argv[1], 16); ln = int(sys.argv[2], 16)
needle = sys.argv[3] if len(sys.argv) > 3 else "ebp - 0x20"
fo = va2fo(va0)
prev = []
for ins in md.disasm(b[fo:fo+ln], va0):
    ann = ""
    for op in ins.operands:
        if op.type == 2:
            s = read_cstr(op.imm & 0xFFFFFFFF)
            if s: ann = f'  ; "{s}"'
    line = f"  0x{ins.address:08X}  {ins.mnemonic:<7s} {ins.op_str}{ann}"
    if needle.lower() in ins.op_str.lower():
        # 打印函数头标志 + 上下文
        for c in prev[-6:]:
            print(c[1])
        print(line + "   <===")
        prev = []
    else:
        prev.append((ins.address, line))
# 另外列出本区间所有对 0x11951b0/0x11951ac 的引用
print()
print("=== 区间内对全局 0x11951B0/0x11951AC 的引用 ===")
fo2 = va2fo(va0)
for ins in md.disasm(b[fo2:fo2+ln], va0):
    for gv, lbl in ((0x11951B0, "LangDir(TEXT-ZH)"), (0x11951AC, "EfileRoot")):
        if hex(gv) in ins.op_str:
            print(f"  0x{ins.address:08X}  {ins.mnemonic:<7s} {ins.op_str}   ; {lbl}")
