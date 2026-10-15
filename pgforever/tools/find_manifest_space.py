# -*- coding: utf-8 -*-
r"""精确遍历 PE 资源目录，定位 RT_MANIFEST 的数据 RVA / 大小，确定可用空间。"""
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
    nm = b[o:o+8].rstrip(b'\x00').decode()
    vs, va, srd, prd = struct.unpack_from('<IIII', b, o+8)
    secs.append((nm, va, vs, prd, srd))


def rva2off(rva):
    for nm, va, vs, prd, srd in secs:
        if va <= rva < va + max(vs, srd):
            return prd + (rva - va)
    return None


rsrc_rva, rsrc_sz = struct.unpack_from('<II', b, ddoff + 2*8)
base = rva2off(rsrc_rva)          # 资源节起始文件偏移
print('资源节 RVA=%08X 文件偏移=0x%X size=%d' % (rsrc_rva, base, rsrc_sz))
print()


def rd(off, fmt):
    return struct.unpack_from(fmt, b, off)


def name_of(off):
    n = rd(off, '<I')[0]
    if n & 0x80000000:
        so = base + (n & 0x7FFFFFFF)
        ln = rd(so, '<H')[0]
        return b[so+2:so+2+ln*2].decode('utf-16-le')
    return n


def walk(off, level, path):
    nn, ni = rd(off+12, '<HH')
    for i in range(nn + ni):
        eo = off + 16 + i*8
        nm, sub = rd(eo, '<II')
        label = name_of(eo)
        if level == 2:
            drva, dsz, cp, res = rd(base + sub, '<IIII')
            doff = rva2off(drva)
            print('  %s data RVA=%08X off=0x%X size=%d codepage=%d' % ('  '*level + str(path + [label]), drva, doff, dsz, cp))
            if 24 in path or str(24) in [str(x) for x in path]:
                print()
                print('  >>> RT_MANIFEST 数据区: 文件偏移 0x%X .. 0x%X (%d 字节)' % (doff, doff+dsz, dsz))
                seg = b[doff:doff+dsz]
                s = seg.find(b'<assembly')
                cl = seg.find(b'</assembly>')
                print('  >>> XML 起始偏移 %d，XML 长度 %d' % (s, cl + 11 - s))
                print('  >>> 可用扩展空间 = %d 字节（数据区尾部）' % (dsz - (cl + 11)))
                tail = seg[cl+11:cl+11+80]
                print('  >>> XML 之后的字节: %r' % tail[:60])
        else:
            walk(base + sub, level + 1, path + [label])


walk(base, 0, [])
