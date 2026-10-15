# -*- coding: utf-8 -*-
"""
定位转换调用点（修正版）
========================
关键更正：exe 内部有一个 W2M 封装函数，调用点形如 `call 0x46D64A`
而非 `call [IAT]`，之前的扫描漏掉了它们。

本脚本：
  1) 列出所有 `call <imm>` 指向的目标，按被调次数排序（找热点函数）
  2) 专门列出所有指向 W2M/MB2W 相关地址的调用
"""
import struct
from collections import Counter
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


def rva2off(rva):
    for name, vaddr, vsize, raddr, rsize in SECTIONS:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return None


def off2rva(off):
    for name, vaddr, vsize, raddr, rsize in SECTIONS:
        if raddr <= off < raddr + rsize:
            return vaddr + (off - raddr)
    return None


text = next(s for s in SECTIONS if s[0] == '.text')
tname, tvaddr, tvsize, traddr, trsize = text
TEXT_VA = IMAGEBASE + tvaddr
code = raw[traddr:traddr + trsize]
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

insns = list(md.disasm(code, TEXT_VA))
print('指令数:', len(insns))
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


# ---- 统计所有 call <imm> ----
callcnt = Counter()
callers = {}
for k, ins in enumerate(insns):
    if ins.mnemonic != 'call' or not ins.operands:
        continue
    op = ins.operands[0]
    if op.type == CS_OP_IMM:
        callcnt[op.imm] += 1
        callers.setdefault(op.imm, []).append(ins.address)

print('\n===== 被调用次数 TOP 40（call imm）=====')
for tgt, c in callcnt.most_common(40):
    fs = func_start(tgt)
    print('  target=%08X  n=%-4d  func_start=%s' % (tgt, c, ('%08X' % fs) if fs else '?'))

# ---- 特别列出 W2M 封装链 ----
print('\n===== 指向 0x46D64A / 0x46D05C 附近的调用 =====')
for tgt in sorted(callcnt):
    if 0x46D000 <= tgt <= 0x46E400:
        print('  target=%08X n=%d' % (tgt, callcnt[tgt]))
