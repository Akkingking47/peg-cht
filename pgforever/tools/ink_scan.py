# -*- coding: utf-8 -*-
r"""解析 shot2.py 产出的 PNG, 按行统计"文字墨迹"像素,
用于在无法目视截图时量化判断文本是否完整渲染。
用法: python ink_scan.py <png> [y0] [y1] [step]
"""
import struct
import sys
import zlib


def read_png(path):
    b = open(path, 'rb').read()
    assert b[:8] == b'\x89PNG\r\n\x1a\n', 'not png'
    i, w, h, idat = 8, None, None, b''
    while i < len(b):
        ln = struct.unpack('>I', b[i:i + 4])[0]
        tag = b[i + 4:i + 8]
        data = b[i + 8:i + 8 + ln]
        if tag == b'IHDR':
            w, h, bd, ct, cm, fm, il = struct.unpack('>IIBBBBB', data)
            assert bd == 8 and ct == 2 and il == 0, (bd, ct, il)
        elif tag == b'IDAT':
            idat += data
        elif tag == b'IEND':
            break
        i += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * 3
    rows = [raw[y * (stride + 1) + 1: y * (stride + 1) + 1 + stride] for y in range(h)]
    return w, h, rows


def main():
    path = sys.argv[1]
    w, h, rows = read_png(path)
    y0 = int(sys.argv[2]) if len(sys.argv) > 2 else 130
    y1 = int(sys.argv[3]) if len(sys.argv) > 3 else min(h, 360)
    step = int(sys.argv[4]) if len(sys.argv) > 4 else 1

    print('%s  %dx%d  区域 y=%d..%d' % (path.split('\\')[-1], w, h, y0, y1))
    print('%-6s %8s %8s' % ('y', '亮像素', '较亮'))
    band = []
    for y in range(y0, y1):
        px = rows[y]
        bri = 0
        mid = 0
        for x in range(0, w * 3 - 2, 3):
            r, g, bl = px[x], px[x + 1], px[x + 2]
            s = r + g + bl
            if s > 330:
                bri += 1
            elif s > 170:
                mid += 1
        band.append((y, bri, mid))
    for y, bri, mid in band:
        bar = '#' * (bri // 2)
        print('%4d  %6d  %6d  %s' % (y, bri, mid, bar))
    print()
    tot = sum(b[1] for b in band)
    print('该区域亮像素总数 = %d' % tot)


if __name__ == '__main__':
    main()
