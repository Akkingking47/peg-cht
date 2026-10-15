# -*- coding: utf-8 -*-
"""从任意 VA 强制起反汇编（不依赖线性扫描），并手工解析 call 目标。"""
import struct, sys
from capstone import *

EXE = r'D:\PGForever1.021\PGForever.exe'
IMAGEBASE = 0x400000
raw = open(EXE, 'rb').read()
e_lfanew = struct.unpack_from('<I', raw, 0x3C)[0]
pe = e_lfanew
num_sec = struct.unpack_from('<H', raw, pe + 6)[0]
opt_size = struct.unpack_from('<H', raw, pe + 0x14)[0]
sec_tbl = pe + 0x18 + opt_size
SECTIONS = []
for i in range(num_sec):
    off = sec_tbl + i * 0x28
    name = raw[off:off + 8].rstrip(b'\x00').decode('latin1')
    vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', raw, off + 8)
    SECTIONS.append((name, vaddr, vsize, raddr, rsize))


def va2off(va):
    rva = va - IMAGEBASE
    for name, vaddr, vsize, raddr, rsize in SECTIONS:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return None


lo = int(sys.argv[1], 16)
n = int(sys.argv[2]) if len(sys.argv) > 2 else 120
off = va2off(lo)
print('VA %08X -> file %08X' % (lo, off))
seg = raw[off:off + n * 8]
print('bytes:', seg[:48].hex())
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
cnt = 0
for ins in md.disasm(seg, lo):
    print('%08X  %-10s %s   [%s]' % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex()))
    cnt += 1
    if cnt > n:
        break
