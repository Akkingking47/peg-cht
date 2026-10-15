# -*- coding: utf-8 -*-
"""解析 PE 导入表，输出 IAT 槽位 -> DLL!函数名 映射。"""
import struct, json, sys

EXE = r'D:\PGForever1.021\PGForever.exe'
f = open(EXE, 'rb').read()

pe = struct.unpack_from('<I', f, 0x3C)[0]
nsec = struct.unpack_from('<H', f, pe + 6)[0]
opt = pe + 24
optsize = struct.unpack_from('<H', f, pe + 20)[0]
base = struct.unpack_from('<I', f, opt + 28)[0]
sect = opt + optsize

secs = []
for i in range(nsec):
    b = sect + i * 40
    nm = f[b:b + 8].rstrip(b'\0').decode()
    vs, va, rs, ro = struct.unpack_from('<IIII', f, b + 8)
    secs.append((nm, va, vs, ro, rs))


def r2o(rva):
    """RVA -> 文件偏移"""
    for nm, va, vs, ro, rs in secs:
        if va <= rva < va + max(vs, rs):
            return rva - va + ro
    return None


def r2o_va(va):
    """VA -> 文件偏移"""
    return r2o(va - base)


dd = opt + 0x60
imp_rva, imp_sz = struct.unpack_from('<II', f, dd + 8)
print('ImageBase = %08X' % base)
print('ImportDir RVA = %X  file = %X' % (imp_rva, r2o(imp_rva)))

o = r2o(imp_rva)
names = {}
i = 0
while True:
    off = o + i * 20
    ilt, ts, fc, nrva, iat = struct.unpack_from('<IIIII', f, off)
    if ilt == 0 and ts == 0 and fc == 0 and nrva == 0:
        break
    do = r2o(nrva)
    dll = f[do:f.index(b'\0', do)].decode()
    t = r2o(ilt) if ilt else r2o(iat)
    j = 0
    while True:
        v = struct.unpack_from('<I', f, t + j * 4)[0]
        if v == 0:
            break
        slot = base + iat + j * 4
        if v & 0x80000000:
            names[slot] = (dll, 'ord#%d' % (v & 0xffff))
        else:
            no = r2o(v & 0x7fffffff)
            nm = f[no + 2:f.index(b'\0', no + 2)].decode()
            names[slot] = (dll, nm)
        j += 1
    i += 1

print('total import slots = %d' % len(names))
print()
for want in [0x47f0cc, 0x47f0d0, 0x47f0d4, 0x47f0d8, 0x47f0e0, 0x47f0e4,
             0x47f120, 0x47f2b4, 0x47f2d0, 0x47f2d4, 0x47f338, 0x47f3b0]:
    print('%08X  %s' % (want, names.get(want)))

print()
print('=== HTMLayout 全部导入 ===')
for k, v in sorted(names.items()):
    if 'htmlayout' in v[0].lower():
        print('%08X  %s' % (k, v[1]))

json.dump({'%X' % k: list(v) for k, v in names.items()},
          open('iat_map.json', 'w'), indent=0)
print('\n-> iat_map.json')
