# -*- coding: utf-8 -*-
"""用 UTF-16 宽串找 "BrfText"/"briefing" 引用，并从 SetElementHtml 调用点反查简报注入路径。"""
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

# 1) UTF-16 宽串搜索
def find_utf16(sub):
    w = b''.join(bytes([c, 0]) for c in sub)
    out = []
    idx = 0
    while True:
        p = raw.find(w, idx)
        if p < 0:
            break
        va = off2va(p)
        if va:
            out.append(va)
        idx = p + 1
    return out

for s in [b'BrfText', b'briefing', b'Brf']:
    vas = find_utf16(s)
    if vas:
        print('UTF16 "%s" -> %d 处: %s' % (s.decode(), len(vas), [hex(v) for v in vas[:8]]))

# 2) SetElementHtml IAT = 0x47F0E0 -> 找所有 call [0x47F0E0]
SEH_VA = 0x47F0E0
seh_iat_off = va2off(SEH_VA)
call_pat = b'\xff\x15' + struct.pack('<I', SEH_VA)
sites = []
start = 0
while True:
    idx = raw.find(call_pat, start)
    if idx < 0:
        break
    sites.append(off2va(idx))
    start = idx + 1
print('\nSetElementHtml 调用点 (%d):' % len(sites))
for v in sites:
    print('  0x%X' % v)

# 3) 对每个调用点，向上反汇编找 html_length（第3参数）来源
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
text = [s for s in secs if s[0] == '.text'][0]
text_off, text_va, text_size = text[2], IMAGEBASE + text[1], text[3]
code = raw[text_off: text_off + text_size]

# 反查 push 立即数引用 "BrfText" 宽串 VA 的指令
brf_vas = find_utf16(b'BrfText')
ref_brf = []
for ins in md.disasm(code, text_va):
    if ins.mnemonic == 'push' and ins.op_str.startswith('0x'):
        try:
            val = int(ins.op_str, 16)
        except ValueError:
            continue
        if val in brf_vas:
            ref_brf.append(ins.address)
print('\n引用 "BrfText" 宽串的指令: %s' % [hex(x) for x in ref_brf])
