# -*- coding: utf-8 -*-
r"""
映射实验：确定引擎把 pgcam 的 UTF-16 文本转成显示串时的具体行为。

假设 H：引擎取每个 wchar 的低字节（Latin-1 式），再按 UTF-8 解析。
       若成立，则写入 3 个低字节为 E6 B3 A2 的字符（æ ³ ¢）应显示为「波」。

设计 5 个 Entry points 的显示名做对照探针。
"""
import ctypes
import os
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

text = open(BAK, 'rb').read().decode('utf-16')
lines = text.split('\r\n')

# 探针：UTF-8 字节 -> 对应低字节的 Latin-1 字符
def disguise(zh):
    return ''.join(chr(b) for b in zh.encode('utf-8'))

PROBES = [
    'æ³¢',                       # 低字节 E6 B3 A2 = UTF-8「波」
    disguise('波兰'),            # 低字节 = UTF-8「波兰」
    'µ',                         # 单字节 B5
    '波兰',                      # 明文中文（已知乱码，对照）
    'ABC',                       # 纯 ASCII（对照）
]
print('探针:', [(p, [hex(ord(c)) for c in p]) for p in PROBES[:3]])

n = 0
for i, l in enumerate(lines):
    if len(l.split('\t')) >= 6 and l.split('\t')[3].strip().isdigit() and l.split('\t')[4].strip().isdigit():
        cols = l.split('\t')
        if n < len(PROBES):
            cols[0] = PROBES[n]
            cols[2] = 'probe%d' % n
            lines[i] = '\t'.join(cols)
            n += 1
open(GAME, 'wb').write(('\ufeff' + '\r\n'.join(lines)).encode('utf-16-le'))
print('已写入 %d 个探针' % n)


def find_hwnd(timeout=25):
    end = time.time() + timeout
    while time.time() < end:
        res = {}

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def cb(h, l):
            if user.IsWindowVisible(h):
                m = user.GetWindowTextLengthW(h) + 1
                b = ctypes.create_unicode_buffer(m)
                user.GetWindowTextW(h, b, m)
                if b.value.startswith('PG Forever'):
                    res['h'] = h
            return True

        user.EnumWindows(cb, 0)
        if 'h' in res:
            return res['h']
        time.sleep(0.4)
    return None


def shot(hwnd, out, w=1200, h=700):
    user.SetWindowPos(hwnd, 0, 0, 0, w, h, 0x0040 | 0x0004)
    time.sleep(1.0)
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    ww, hh = r.right - r.left, r.bottom - r.top
    hdc = user.GetDC(0)
    memdc = gdi.CreateCompatibleDC(hdc)
    hbmp = gdi.CreateCompatibleBitmap(hdc, ww, hh)
    gdi.SelectObject(memdc, hbmp)
    gdi.BitBlt(memdc, 0, 0, ww, hh, hdc, r.left, r.top, 0x00CC0020)

    class BIH(ctypes.Structure):
        _fields_ = [('biSize', wintypes.DWORD), ('biWidth', ctypes.c_int), ('biHeight', ctypes.c_int),
                    ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                    ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', ctypes.c_int),
                    ('biYPelsPerMeter', ctypes.c_int), ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)]
    bih = BIH()
    bih.biSize = ctypes.sizeof(BIH)
    bih.biWidth, bih.biHeight = ww, -hh
    bih.biPlanes, bih.biBitCount, bih.biCompression = 1, 32, 0
    stride = ((ww * 32 + 31) // 32) * 4
    buf = ctypes.create_string_buffer(stride * hh)
    gdi.GetDIBits(memdc, hbmp, 0, hh, buf, ctypes.byref(bih), 0)
    rows = []
    for row in range(hh):
        off = row * stride
        px = buf[off:off + stride]
        line = bytearray(ww * 3)
        for i2 in range(ww):
            line[i2*3], line[i2*3+1], line[i2*3+2] = px[i2*4+2], px[i2*4+1], px[i2*4]
        rows.append(bytes(line))

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + x for x in rows)
    open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', ww, hh, 8, 2, 0, 0, 0))
                          + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
    gdi.DeleteObject(hbmp)
    gdi.DeleteDC(memdc)
    user.ReleaseDC(0, hdc)


p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
hwnd = find_hwnd(25)
if hwnd:
    user.SetForegroundWindow(hwnd)
    time.sleep(3.5)
    shot(hwnd, os.path.join(OUTDIR, 'map_probe.png'))
    print('截图完成')
p.terminate()
try:
    p.wait(timeout=6)
except Exception:
    p.kill()

# 恢复译文版（重新套用正式译表）
import json
os.system('')
print('注意：pg.pgcam 目前是探针内容，需重跑 apply_pg_cam.py 恢复')
