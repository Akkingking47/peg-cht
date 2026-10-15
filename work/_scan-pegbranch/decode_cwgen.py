# -*- coding: utf-8 -*-
"""只读比对：从两个安装目录的 CWGEN.dat 里解出 HEX.S16[0]（荣誉榜）并导出 PNG。
不写任何游戏文件；输出只落在工作区证据目录。"""
import struct, zlib, os, hashlib

OUT = r"D:\DSH\军事游戏汉化\work\_scan-pegbranch"
os.makedirs(OUT, exist_ok=True)

def parse(path):
    b = open(path, 'rb').read()
    n = struct.unpack_from('<I', b, 0)[0]
    dirEnd = struct.unpack_from('<I', b, 4)[0]
    ents = []
    for i in range(n):
        o = 8 + i * 17
        name = b[o:o + 13].rstrip(b'\0').decode('latin-1')
        off = struct.unpack_from('<I', b, o + 13)[0]
        ents.append((name, off))
    return b, n, dirEnd, ents

def decode_icon(b, off, idx):
    nicons = struct.unpack_from('<I', b, off)[0]
    rec = off + 4 + idx * 40
    w, h, sx, sy, fw, fh, starts, nbytes, comp, load = struct.unpack_from('<10I', b, rec)
    index_end = off + 4 + nicons * 40
    data = b[index_end + starts: index_end + starts + nbytes]
    return dict(nicons=nicons, w=w, h=h, sx=sx, sy=sy, fw=fw, fh=fh,
                starts=starts, nbytes=nbytes, comp=comp, data=data)

def rle_decode(data, npix):
    out = []
    i = 0
    while len(out) < npix and i + 2 < len(data):
        cnt = data[i]; rgb = data[i + 1] | (data[i + 2] << 8); i += 3
        out.extend([rgb] * cnt)
    return out[:npix], i

def rgb565(v):
    r = (v >> 11) & 0x1F; g = (v >> 5) & 0x3F; bl = v & 0x1F
    return (r * 255 // 31, g * 255 // 63, bl * 255 // 31)

def write_png(path, pix, w, h):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        base = y * w
        for x in range(w):
            r, g, b = rgb565(pix[base + x])
            raw += bytes((r, g, b))
    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    open(path, 'wb').write(png)

for tag, p in (('official', r'D:\Program Files\PeG\CWGEN.dat'),
               ('branch',   r'D:\Program Files\PeG-1\CWGEN.dat')):
    b, n, de, ents = parse(p)
    offs = [o for nm, o in ents if nm.upper() == 'HEX.S16']
    print('%s: %s' % (tag, p))
    print('  nFiles=%d dirEnd=%d  md5=%s' % (n, de, hashlib.md5(b).hexdigest()))
    print('  HEX.S16 目录项偏移=%s' % (offs,))
    info = decode_icon(b, offs[0], 0)
    print('  icon0: 记录 %dx%d  full=%dx%d starts=%d nbytes=%d comp=%d (该文件共 %d 个图形)'
          % (info['w'], info['h'], info['fw'], info['fh'], info['starts'],
             info['nbytes'], info['comp'], info['nicons']))
    pix, used = rle_decode(info['data'], info['fw'] * info['fh'])
    print('  解码: 像素=%d  消耗字节=%d/%d  颜色数=%d'
          % (len(pix), used, info['nbytes'], len(set(pix))))
    out = os.path.join(OUT, 'honor-%s.png' % tag)
    write_png(out, pix, info['fw'], info['fh'])
    print('  导出 %s' % out)
print('DONE')
