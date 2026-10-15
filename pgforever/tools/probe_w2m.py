# -*- coding: utf-8 -*-
"""枚举 PGForever.exe 中所有 WideCharToMultiByte 调用点，并反汇编其参数准备段，
重点查看第 6 个参数 cbMultiByte 是如何计算的（N 还是 3N/4N）。
"""
import struct
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\PGForever1.021\PGForever.exe'
IMAGEBASE = 0x400000

raw = open(EXE, 'rb').read()
print('size', len(raw), 'md5', __import__('hashlib').md5(raw).hexdigest())

# ---- 解析 PE 节区，建立 VA -> 文件偏移 ----
assert raw[:2] == b'MZ'
e_lfanew = struct.unpack_from('<I', raw, 0x3C)[0]
pe = e_lfanew
assert raw[pe:pe+4] == b'PE\x00\x00'
num_sec = struct.unpack_from('<H', raw, pe+6)[0]
sec_tbl = pe + 0x18 + struct.unpack_from('<H', raw, pe+0x14)[0]
sections = []
for i in range(num_sec):
    off = sec_tbl + i*0x28
    name = raw[off:off+8].split(b'\x00')[0].decode('latin1')
    vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', raw, off+8)
    sections.append((name, vaddr, raddr, vsize, rsize))

def va2off(va):
    rva = va - IMAGEBASE
    for (name, vaddr, raddr, vsize, rsize) in sections:
        if vaddr <= rva < vaddr + vsize:
            return raddr + (rva - vaddr)
    return None

def off2va(off):
    for (name, vaddr, raddr, vsize, rsize) in sections:
        if raddr <= off < raddr + rsize:
            return IMAGEBASE + vaddr + (off - raddr)
    return None

# ---- 找 IAT 槽位：WideCharToMultiByte @ VA 0x47F2D0 ----
W2M_IAT_VA = 0x47F2D0
w2m_iat_off = va2off(W2M_IAT_VA)
print('WideCharToMultiByte IAT @ VA 0x%X  file 0x%X' % (W2M_IAT_VA, w2m_iat_off))

# 调用模式: ff 15 <4字节小端 IAT 地址> => ff 15 d0 f2 7f 00
call_pat = b'\xff\x15' + struct.pack('<I', W2M_IAT_VA)
sites = []
start = 0
while True:
    idx = raw.find(call_pat, start)
    if idx < 0:
        break
    sites.append(idx)
    start = idx + 1

print('找到 %d 个 WideCharToMultiByte 调用点 (file offset):' % len(sites))
for s in sites:
    print('  0x%X  (VA 0x%X)' % (s, off2va(s)))

# ---- 反汇编每个调用点前 0x90 字节 ----
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

def disasm_at(off, size=0xA0):
    # 找函数起点：向上找 55 8b ec
    begin = off
    # 简单方式：从 off-0x90 开始反汇编到 off+0x10
    seg_start = max(0, off - 0x90)
    chunk = raw[seg_start: off+0x14]
    out = []
    for ins in md.disasm(chunk, off2va(seg_start)):
        out.append(ins)
    return out

for s in sites:
    va = off2va(s)
    print('\n================= call @ file 0x%X  VA 0x%X =================' % (s, va))
    insns = disasm_at(s)
    # 只打印 call 之前的指令 + call 本身
    for ins in insns:
        mark = '  <<< CALL' if ins.address == va else ''
        print('  0x%X  %-14s %s' % (ins.address, (ins.mnemonic + ' ' + ins.op_str).strip(), mark))
