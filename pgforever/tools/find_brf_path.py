# -*- coding: utf-8 -*-
"""定位简报(briefing)渲染路径：
1. 在 exe 中找 "BrfText" / "briefing" / ".pgbrf" 等字符串地址
2. 反汇编全代码，找引用这些字符串的函数（push 立即数 = 字符串 VA）
3. 在这些函数里找它们调用的 WideCharToMultiByte 站点
"""
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\PGForever1.021\PGForever.exe'
IMAGEBASE = 0x400000
raw = open(EXE, 'rb').read()

e_lfanew = struct.unpack_from('<I', raw, 0x3C)[0]
pe = e_lfanew
num_sec = struct.unpack_from('<H', raw, pe+6)[0]
sec_tbl = pe + 0x18 + struct.unpack_from('<H', raw, pe+0x14)[0]
secs = []
for i in range(num_sec):
    off = sec_tbl + i*0x28
    name = raw[off:off+8].split(b'\x00')[0].decode('latin1')
    vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', raw, off+8)
    secs.append((name, vaddr, raddr, vsize, rsize))

def va2off(va):
    rva = va - IMAGEBASE
    for (n, va_, ra_, vs, rs) in secs:
        if va_ <= rva < va_ + vs:
            return ra_ + (rva - va_)
    return None

def off2va(off):
    for (n, va_, ra_, vs, rs) in secs:
        if ra_ <= off < ra_ + rs:
            return IMAGEBASE + va_ + (off - ra_)
    return None

# 找目标字符串
targets = [b'BrfText', b'briefing', b'.pgbrf', b'pgbrf', b'Brf']
found = {}  # str -> list of VA
for t in targets:
    idx = 0
    while True:
        p = raw.find(t, idx)
        if p < 0:
            break
        # 必须位于某个节区内（数据/资源）
        va = off2va(p)
        if va:
            found.setdefault(t, []).append(va)
        idx = p + 1

print('=== 命中字符串 ===')
for t, vas in found.items():
    print('%s -> %d 处, 例 VA 0x%X' % (t, len(vas), vas[0] if vas else 0))

# 全代码反汇编，收集所有 push 立即数/lea 引用
md = Cs(CS_ARCH_X86, CS_MODE_32)
# 代码节 .text
text = [s for s in secs if s[0] == '.text'][0]
text_off, text_va, text_size = text[2], IMAGEBASE + text[1], text[3]
code = raw[text_off: text_off + text_size]

# 把字符串 VA 去重成集合
str_vas = set()
for vas in found.values():
    str_vas.update(vas)

# 找哪些函数引用了这些字符串：扫描 push imm32 == strVA
ref_funcs = {}  # strVA -> set of call-VA that referenced it
# 先收集所有函数起点（简单启发：call 目标 + 0x55 0x8b 0xec prologue）
# 这里直接逐指令扫描 push 立即数
print('\n=== 引用这些字符串的指令 ===')
for ins in md.disasm(code, text_va):
    if ins.mnemonic == 'push' and ins.op_str.startswith('0x'):
        val = int(ins.op_str, 16)
        if val in str_vas:
            print('  0x%X  push 0x%X  (%s)' % (ins.address, val,
                  [k for k,v in found.items() if val in v]))
