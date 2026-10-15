# -*- coding: utf-8 -*-
"""按 IAT 槽位 VA 反查导入函数名（用 OriginalFirstThunk/INT）。"""
import struct
EXE = r'D:\PGForever1.021\PGForever.exe'
IMAGEBASE = 0x400000
raw = open(EXE, 'rb').read()
e_lfanew = struct.unpack_from('<I', raw, 0x3C)[0]
pe = e_lfanew
opt = pe + 0x18
imp_rva, imp_size = struct.unpack_from('<II', raw, opt + 0x60 + 8)  # skip Export(0) -> Import(1)

def rva2off(rva):
    num_sec = struct.unpack_from('<H', raw, pe+6)[0]
    sec_tbl = pe + 0x18 + struct.unpack_from('<H', raw, pe+0x14)[0]
    for i in range(num_sec):
        off = sec_tbl + i*0x28
        vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', raw, off+8)
        if vaddr <= rva < vaddr + vsize:
            return raddr + (rva - vaddr)
    return None

# 预先建立 IAT VA -> 函数名 映射
slot2name = {}
descr = rva2off(imp_rva)
while True:
    oft, _, _, name_rva, ft = struct.unpack_from('<IIIII', raw, descr)
    if ft == 0:
        break
    dll = raw[rva2off(name_rva):].split(b'\x00')[0].decode('latin1', 'replace')
    # INT 数组 (oft) 与 IAT 数组 (ft) 平行
    int_off = rva2off(oft) if oft else None
    iat_off = rva2off(ft)
    j = 0
    while True:
        if int_off is None:
            (val,) = struct.unpack_from('<I', raw, iat_off + j*4)
        else:
            (val,) = struct.unpack_from('<I', raw, int_off + j*4)
        if val == 0:
            break
        iat_va = IMAGEBASE + ft + j*4
        if val & 0x80000000:
            nm = 'ord%d' % (val & 0x7fffffff)
        else:
            no = rva2off(val)
            if no is None:
                nm = '?'
            else:
                nm = raw[no+2:].split(b'\x00')[0].decode('latin1', 'replace')
        slot2name[iat_va] = dll + '!' + nm
        j += 1
    descr += 0x14

watch = [0x47F0D0, 0x47F0D8, 0x47F0CC, 0x47F0A0, 0x47F0D4, 0x47F120, 0x47F108,
         0x47F118, 0x47F154, 0x47F20C, 0x47F210, 0x47F338, 0x47F3B0, 0x47F3C4,
         0x47F2D0, 0x47F2D4, 0x47F2D8, 0x47F0E0]
print('=== 关心的 IAT 槽位 ===')
for va in watch:
    print('  0x%X -> %s' % (va, slot2name.get(va, '?? not-in-imports')))

print('\n=== 全部 *WideChar*/*MultiByte* ===')
for va, nm in slot2name.items():
    if 'WideChar' in nm or 'MultiByte' in nm:
        print('  0x%X  %s' % (va, nm))
print('\n=== 全部 HTMLayout* ===')
for va, nm in slot2name.items():
    if 'HTML' in nm.upper():
        print('  0x%X  %s' % (va, nm))
