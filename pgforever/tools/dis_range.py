# -*- coding: utf-8 -*-
"""反汇编指定 VA 范围，并列出对该范围内的所有 call 来源。"""
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


text = next(s for s in SECTIONS if s[0] == '.text')
_, tvaddr, tvsize, traddr, trsize = text
code = raw[traddr:traddr + trsize]
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
insns = list(md.disasm(code, IMAGEBASE + tvaddr))
by_va = {i.address: k for k, i in enumerate(insns)}


def func_start(va):
    k = by_va.get(va)
    if k is None:
        return None
    for j in range(k, max(0, k - 4000), -1):
        a = insns[j]
        if a.mnemonic == 'push' and a.op_str == 'ebp' and j + 1 < len(insns):
            b = insns[j + 1]
            if b.mnemonic == 'mov' and b.op_str.replace(' ', '') == 'ebp,esp':
                return a.address
    return None


lo = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x46D05C
hi = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x46D750

print('=== 反汇编 %08X .. %08X ===' % (lo, hi))
for ins in insns:
    if lo <= ins.address < hi:
        print('%08X  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))

print('\n=== 谁 call 到 [%08X, %08X) ===' % (lo, hi))
found = 0
for ins in insns:
    if ins.mnemonic == 'call' and ins.operands and ins.operands[0].type == CS_OP_IMM:
        t = ins.operands[0].imm
        if lo <= t < hi:
            found += 1
            print('  %08X -> %08X   (func_start=%s)' % (ins.address, t, func_start(ins.address)))
if not found:
    print('  (无直接 call)')

print('\n=== 谁 push/jmp 引用该范围（含 jmp/lea）===')
found = 0
for ins in insns:
    for op in ins.operands:
        v = None
        if op.type == CS_OP_IMM:
            v = op.imm
        elif op.type == CS_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
            v = op.mem.disp
        if v is not None and lo <= v < hi and ins.address != v:
            if ins.mnemonic in ('jmp', 'lea', 'mov', 'push', 'call'):
                found += 1
                if found < 40:
                    print('  %08X  %-6s %s' % (ins.address, ins.mnemonic, ins.op_str))
if not found:
    print('  (无)')
