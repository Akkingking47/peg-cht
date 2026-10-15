# -*- coding: utf-8 -*-
r"""
静态分析 PGForever.exe 的导入表，找出编码转换与 HTMLayout 接口。
目的：判断数据文件文本走的是窄字符(ANSI/UTF-8 字节)还是宽字符路径，
从而解释 UTF-16 数据文件里的中文为何乱码，以及能否通过改 exe 修正。
"""
import struct

EXE = r'D:\PGForever1.021\PGForever.exe'
b = open(EXE, 'rb').read()
e = struct.unpack_from('<I', b, 0x3c)[0]
nsec = struct.unpack_from('<H', b, e+6)[0]
sizeopt = struct.unpack_from('<H', b, e+20)[0]
optoff = e + 24
magic = struct.unpack_from('<H', b, optoff)[0]
ddoff = optoff + (112 if magic == 0x20b else 96)

secs = []
so = optoff + sizeopt
for i in range(nsec):
    o = so + i*40
    name = b[o:o+8].rstrip(b'\x00').decode()
    vs, va, srd, prd = struct.unpack_from('<IIII', b, o+8)
    secs.append((name, va, vs, prd, srd))


def rva2off(rva):
    for name, va, vs, prd, srd in secs:
        if va <= rva < va + max(vs, srd):
            return prd + (rva - va)
    return None


# 导入表
imp_rva, imp_size = struct.unpack_from('<II', b, ddoff + 8)
print('导入表 RVA=%08X size=%d' % (imp_rva, imp_size))

imports = {}
off = rva2off(imp_rva)
while off:
    d = b[off:off+20]
    if len(d) < 20 or d == b'\x00'*20:
        break
    name_rva = struct.unpack_from('<I', d, 12)[0]
    if name_rva == 0:
        break
    no = rva2off(name_rva)
    end = b.index(b'\x00', no)
    lib = b[no:end].decode()
    thunk = struct.unpack_from('<I', d, 16)[0]
    names = []
    if thunk:
        to = rva2off(thunk)
        while to:
            v = struct.unpack_from('<I', b, to)[0]
            if v == 0:
                break
            if v & 0x80000000:
                names.append('ordinal#%d' % (v & 0xFFFF))
            else:
                ho = rva2off(v + 2)
                he = b.index(b'\x00', ho)
                names.append(b[ho:he].decode())
            to += 4
    imports[lib] = names
    off += 20

print()
print('=== 导入的 DLL ===')
for lib in imports:
    print('  %-28s %d 个函数' % (lib, len(imports[lib])))

KEY = ('MultiByteToWideChar', 'WideCharToMultiByte', 'GetACP', 'GetOEMCP', 'IsDBCSLeadByte',
       'CreateFont', 'TextOut', 'DrawText', 'lstrlen', 'lstrcpy', 'wsprintf', 'sprintf')
print()
print('=== 编码/文本相关导入 ===')
found = False
for lib, names in imports.items():
    for n in names:
        if n in KEY or 'MultiByte' in n or 'WideChar' in n:
            print('  %-24s %s' % (lib, n))
            found = True
if not found:
    print('  (无 MultiByteToWideChar / WideCharToMultiByte 导入)')

print()
print('=== HTMLayout 相关导入 ===')
for lib, names in imports.items():
    if 'htmlayout' in lib.lower():
        for n in sorted(names):
            print('  %s' % n)

print()
print('=== kernel32 中与代码页/转换相关的 ===')
for n in sorted(imports.get('KERNEL32.DLL', []) + imports.get('kernel32.dll', [])):
    if any(k in n.lower() for k in ('codepage', 'convert', 'acp', 'string')):
        print('  %s' % n)
