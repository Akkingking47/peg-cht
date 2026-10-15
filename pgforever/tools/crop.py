# -*- coding: utf-8 -*-
r"""裁剪 PNG 指定区域并放大，便于精确定位界面元素坐标。"""
import struct
import sys
import zlib

def read_png(path):
    b = open(path, 'rb').read()
    assert b[:8] == b'\x89PNG\r\n\x1a\n'
    i = 8
    w = h = None
    idat = b''
    while i < len(b):
        ln = struct.unpack('>I', b[i:i+4])[0]
        tag = b[i+4:i+8]
        data = b[i+8:i+8+ln]
        if tag == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', data[:10])
            assert bd == 8 and ct == 2, 'only 8-bit RGB supported'
        elif tag == b'IDAT':
            idat += data
        elif tag == b'IEND':
            break
        i += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * 3
    rows = []
    pos = 0
    for _ in range(h):
        f = raw[pos]
        pos += 1
        line = bytearray(raw[pos:pos+stride])
        pos += stride
        if f == 1:
            for x in range(3, stride):
                line[x] = (line[x] + line[x-3]) & 0xFF
        elif f == 2:
            pass
        rows.append(bytes(line))
    return w, h, rows

def write_png(path, rows, w, h):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + r for r in rows)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b'')
    open(path, 'wb').write(png)

src = sys.argv[1]
out = sys.argv[2]
x0, y0, x1, y1 = (int(v) for v in sys.argv[3:7])
scale = int(sys.argv[7]) if len(sys.argv) > 7 else 2

w, h, rows = read_png(src)
x0 = max(0, x0); y0 = max(0, y0); x1 = min(w, x1); y1 = min(h, y1)
sub = [rows[y][x0*3:x1*3] for y in range(y0, y1)]
sw, sh = x1 - x0, y1 - y0
# 最近邻放大
big = []
for r in sub:
    line = bytearray()
    for i in range(scale):
        for x in range(sw):
            line += r[x*3:x*3+3]
    for i in range(scale):
        big.append(bytes(line))
write_png(out, big, sw*scale, sh*scale)
print('cropped %s from (%d,%d)-(%d,%d) x%d -> %s' % (out, x0, y0, x1, y1, scale, out))
