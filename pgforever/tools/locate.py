# -*- coding: utf-8 -*-
r"""在截图中按颜色定位 UI 元素（金色按钮），输出精确的 x/y 区间，避免目测误差。"""
import struct
import sys
import zlib


def read_png(path):
    b = open(path, 'rb').read()
    i = 8
    w = h = None
    idat = b''
    while i < len(b):
        ln = struct.unpack('>I', b[i:i+4])[0]
        tag = b[i+4:i+8]
        data = b[i+8:i+8+ln]
        if tag == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', data[:10])
        elif tag == b'IDAT':
            idat += data
        elif tag == b'IEND':
            break
        i += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * 3
    rows = []
    pos = 0
    prev = bytearray(stride)
    for _ in range(h):
        f = raw[pos]
        pos += 1
        line = bytearray(raw[pos:pos+stride])
        pos += stride
        if f == 1:
            for x in range(3, stride):
                line[x] = (line[x] + line[x-3]) & 0xFF
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif f == 3:
            for x in range(stride):
                a = line[x-3] if x >= 3 else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 0xFF
        elif f == 4:
            for x in range(stride):
                a = line[x-3] if x >= 3 else 0
                b_ = prev[x]
                c = prev[x-3] if x >= 3 else 0
                p = a + b_ - c
                pa, pb, pc = abs(p-a), abs(p-b_), abs(p-c)
                pr = a if (pa <= pb and pa <= pc) else (b_ if pb <= pc else c)
                line[x] = (line[x] + pr) & 0xFF
        rows.append(bytes(line))
        prev = line
    return w, h, rows


def is_gold(r, g, b):
    return r > 150 and g > 130 and b < 130 and r - b > 60


def is_text(r, g, b):
    """亮色文字像素（浅绿/浅黄/白），用于定位列表文本行"""
    return r + g + b > 330


MODE = sys.argv[6] if len(sys.argv) > 6 else 'gold'
PRED = is_text if MODE == 'text' else is_gold

path = sys.argv[1]
y0, y1 = int(sys.argv[2]), int(sys.argv[3])
x0, x1 = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 10**9)

w, h, rows = read_png(path)
y1 = min(y1, h)
x1 = min(x1, w)

# 逐行统计金色像素的 x 区间
col_hits = [0] * w
row_hits = [0] * h
for y in range(y0, y1):
    line = rows[y]
    for x in range(x0, x1):
        r, g, b = line[x*3], line[x*3+1], line[x*3+2]
        if PRED(r, g, b):
            col_hits[x] += 1
            row_hits[y] += 1

print('分析区域 x[%d,%d) y[%d,%d)' % (x0, x1, y0, y1))
print()
print('有金色像素的行（y : 数量）:')
runs = []
cur = None
for y in range(y0, y1):
    if row_hits[y] > 3:
        if cur is None:
            cur = [y, y]
        else:
            cur[1] = y
    else:
        if cur:
            runs.append(tuple(cur))
            cur = None
if cur:
    runs.append(tuple(cur))
for a, b_ in runs:
    print('  y %d - %d  (高 %d)' % (a, b_, b_ - a + 1))

print()
print('有金色像素的列区间（x 分段）:')
runs = []
cur = None
for x in range(x0, x1):
    if col_hits[x] > 2:
        if cur is None:
            cur = [x, x]
        else:
            cur[1] = x
    else:
        if cur:
            runs.append(tuple(cur))
            cur = None
if cur:
    runs.append(tuple(cur))
for a, b_ in runs:
    print('  x %d - %d  (宽 %d, 中心 %d)' % (a, b_, b_ - a + 1, (a + b_) // 2))
