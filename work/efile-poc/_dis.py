# -*- coding: utf-8 -*-
"""反汇编 OpenGen.exe 关键函数区，自动标注字符串立即数。
用法: python _dis.py 0x7BCB40 0x160 [标签]
"""
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

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

def dis(va_start, length, label=""):
    fo = va2fo(va_start)
    if fo is None:
        print("bad va"); return
    print("=" * 96)
    print(f"### {label}  VA 0x{va_start:08X} (len 0x{length:X})")
    print("=" * 96)
    code = b[fo:fo+length]
    for ins in md.disasm(code, va_start):
        ann = ""
        for op in ins.operands:
            if op.type == 2:  # IMM
                imm = op.imm & 0xFFFFFFFF
                s = read_cstr(imm)
                if s:
                    ann = f"   ; \"{s}\""
                    break
                # 也可能是有符号
        print(f"  0x{ins.address:08X}  {ins.bytes.hex(' '):<30s} {ins.mnemonic:<7s} {ins.op_str:<34s}{ann}")

if __name__ == "__main__":
    va = int(sys.argv[1], 16)
    ln = int(sys.argv[2], 16)
    lb = sys.argv[3] if len(sys.argv) > 3 else ""
    dis(va, ln, lb)
