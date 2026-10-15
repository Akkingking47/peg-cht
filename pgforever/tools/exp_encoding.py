# -*- coding: utf-8 -*-
r"""
编码对照实验：把 pg.pgcam 以不同编码写入，各启动一次截图，找出引擎真正认的编码。
实验对象只改文件编码，译文内容完全一致。
"""
import ctypes
import os
import shutil
import struct
import subprocess
import time
import zlib
from ctypes import wintypes

user = ctypes.windll.user32
gdi = ctypes.windll.gdi32
user.SetProcessDPIAware()

GAME = r'D:\PGForever1.021\PG\Scenario\pg.pgcam'
BAK = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\PG\Scenario\pg.pgcam'
OUTDIR = r'D:\DSH\军事游戏汉化\pgforever\poc'

text = open(BAK, 'rb').read().decode('utf-16')     # 备份原文（UTF-16LE）
# 用固定探针字符串替换 Entry points 的描述，便于一眼判断编码是否正确
PROBE = '德国在欧洲发动一连串闪电战攻势，自波兰开始。测试ABCDE'
lines = text.split('\r\n')
for i, l in enumerate(lines):
    if l.startswith('1939\t'):
        cols = l.split('\t')
        cols[2] = PROBE
        lines[i] = '\t'.join(cols)
probe_text = '\r\n'.join(lines)


def find_hwnd(timeout=25):
    end = time.time() + timeout
    while time.time() < end:
        res = {}

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def cb(h, l):
            if user.IsWindowVisible(h):
                n = user.GetWindowTextLengthW(h) + 1
                b = ctypes.create_unicode_buffer(n)
                user.GetWindowTextW(h, b, n)
                if b.value.startswith('PG Forever'):
                    res['h'] = h
            return True

        user.EnumWindows(cb, 0)
        if 'h' in res:
            return res['h']
        time.sleep(0.4)
    return None


def shot(hwnd, out):
    user.SetWindowPos(hwnd, 0, 0, 0, 1200, 700, 0x0040 | 0x0004)
    time.sleep(1.2)
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = user.GetDC(0)
    memdc = gdi.CreateCompatibleDC(hdc)
    hbmp = gdi.CreateCompatibleBitmap(hdc, w, h)
    gdi.SelectObject(memdc, hbmp)
    gdi.BitBlt(memdc, 0, 0, w, h, hdc, r.left, r.top, 0x00CC0020)

    class BIH(ctypes.Structure):
        _fields_ = [('biSize', wintypes.DWORD), ('biWidth', ctypes.c_int), ('biHeight', ctypes.c_int),
                    ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                    ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', ctypes.c_int),
                    ('biYPelsPerMeter', ctypes.c_int), ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)]
    bih = BIH()
    bih.biSize = ctypes.sizeof(BIH)
    bih.biWidth, bih.biHeight = w, -h
    bih.biPlanes, bih.biBitCount, bih.biCompression = 1, 32, 0
    stride = ((w * 32 + 31) // 32) * 4
    buf = ctypes.create_string_buffer(stride * h)
    gdi.GetDIBits(memdc, hbmp, 0, h, buf, ctypes.byref(bih), 0)
    rows = []
    for row in range(h):
        off = row * stride
        px = buf[off:off + stride]
        line = bytearray(w * 3)
        for i in range(w):
            line[i*3], line[i*3+1], line[i*3+2] = px[i*4+2], px[i*4+1], px[i*4]
        rows.append(bytes(line))

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + x for x in rows)
    open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                          + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
    gdi.DeleteObject(hbmp)
    gdi.DeleteDC(memdc)
    user.ReleaseDC(0, hdc)


VARIANTS = [
    ('utf8bom', b'\xef\xbb\xbf' + probe_text.encode('utf-8')),
    ('utf8', probe_text.encode('utf-8')),
    ('utf16le', b'\xff\xfe' + probe_text.encode('utf-16-le')),
    ('gbk', probe_text.encode('gbk')),
]

for name, data in VARIANTS:
    open(GAME, 'wb').write(data)
    print('[%s] 写入 %d 字节' % (name, len(data)))
    p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
    hwnd = find_hwnd(20)
    if not hwnd:
        print('   未找到窗口')
        p.terminate()
        continue
    time.sleep(2.5)
    shot(hwnd, os.path.join(OUTDIR, 'enc_%s.png' % name))
    p.terminate()
    try:
        p.wait(timeout=6)
    except Exception:
        p.kill()
    time.sleep(1.0)

# 恢复为 UTF-16LE 版（当前正式方案）
open(GAME, 'wb').write(b'\xff\xfe' + probe_text.encode('utf-16-le'))
print('实验结束，已恢复 UTF-16LE 探针版')
