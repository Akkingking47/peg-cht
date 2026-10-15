# -*- coding: utf-8 -*-
"""通用：对每个「路径模板」VA，找出它的 push 点，并回溯最近的「目录全局」赋值。

用法:  python _dirtrace.py 0x8F6458 0x8FE038 ...
全局:
  0x11951A8 GameRoot   0x11951AC EfileRoot   0x11951B0 LangDir
纯 ASCII 脚本（避免 PS/GBK 误读问题；这里是 Python 但同样保持 ASCII）。
"""
import struct
import sys
import pathlib
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
    secs.append((nm, va + imgbase, vsz, fo, rsz))

GLOBALS = {0x11951A8: "GameRoot", 0x11951AC: "EfileRoot", 0x11951B0: "LangDir"}


def va2fo(va):
    for nm, sva, vsz, fo, rsz in secs:
        if sva <= va < sva + max(vsz, rsz):
            return fo + (va - sva)
    return None


def fo2va(fo):
    for nm, sva, vsz, f0, rsz in secs:
        if f0 <= fo < f0 + rsz:
            return sva + (fo - f0)
    return None


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True


def cstr(va):
    fo = va2fo(va)
    if fo is None:
        return None
    e = b.index(b"\0", fo)
    return b[fo:e].decode("latin1")


def find_push(tgt):
    """返回所有 push <tgt> 的地址（VA）。"""
    out = []
    pat = struct.pack("<I", tgt)
    start = 0
    while True:
        i = b.find(pat, start)
        if i < 0:
            break
        start = i + 1
        for back in range(1, 9):
            va = fo2va(i - back)
            if va is None:
                continue
            for ins in md.disasm(b[va2fo(va):va2fo(va) + back + 4], va):
                if ins.address == va and ins.mnemonic == "push" and \
                   ins.operands and ins.operands[0].type == 2 and \
                   ins.operands[0].imm == tgt:
                    out.append(va)
                break
    return sorted(set(out))


def trace(site):
    """回溯 site 前 0x60 字节，找最近的目录全局引用。"""
    fo = va2fo(site)
    va_start = fo2va(fo - 0x60)
    res = []
    for ins in md.disasm(b[va2fo(va_start):fo + 8], va_start):
        if ins.address > site + 6:
            break
        txt = "%s %s" % (ins.mnemonic, ins.op_str)
        for g, nm in GLOBALS.items():
            if ("0x%x" % g) in txt or ("[0x%x]" % g) in txt:
                res.append((ins.address, txt))
    return res


def main():
    for a in sys.argv[1:]:
        tgt = int(a, 16)
        name = cstr(tgt)
        sites = find_push(tgt)
        print("=" * 78)
        print("TEMPLATE VA %08X  %r   push-sites=%d" % (tgt, name, len(sites)))
        for s in sites:
            tr = trace(s)
            lbl = tr[-1][1] if tr else "<no dir global in 0x60>"
            print("   site %08X -> %s" % (s, lbl))
            for addr, t in tr:
                print("        %08X  %s" % (addr, t))


main()
