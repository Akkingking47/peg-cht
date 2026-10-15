# -*- coding: utf-8 -*-
r"""
进入战斗，逐格 hover，截取全窗口的 hover 文本行（右栏 y≈505..575），
拼成一张纵向总览图，便于直接读出每个地块的地名/河名是否已汉化。

用法: python probe_river3.py
"""
import ctypes
import ctypes.wintypes as wt
import subprocess
import time
import zlib
import struct
import os

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
u32 = ctypes.WinDLL('user32', use_last_error=True)
g32 = ctypes.WinDLL('gdi32', use_last_error=True)

EXE = r'D:\PGForever1.021\PGForever.exe'
CWD = r'D:\PGForever1.021'
POC = r'D:\DSH\军事游戏汉化\pgforever\poc'
WM_LBUTTONDOWN, WM_LBUTTONUP, WM_MOUSEMOVE = 0x0201, 0x0202, 0x0200


def find_hwnd(title):
    res = {}

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def cb(hwnd, lp):
        n = u32.GetWindowTextLengthW(hwnd) + 1
        b = ctypes.create_unicode_buffer(n)
        u32.GetWindowTextW(hwnd, b, n)
        if b.value == title:
            res['h'] = hwnd
            return False
        return True

    u32.EnumWindows(cb, 0)
    return res.get('h')


def click(hwnd, x, y, pause=1.5):
    lp = (y << 16) | x
    u32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    time.sleep(0.12)
    u32.PostMessageW(hwnd, WM_LBUTTONDOWN, 1, lp)
    time.sleep(0.06)
    u32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    time.sleep(pause)


def hover(hwnd, x, y, pause=0.6):
    u32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, (y << 16) | x)
    time.sleep(pause)


def grab(hwnd):
    r = wt.RECT()
    u32.GetClientRect(hwnd, ctypes.byref(r))
    w, h = r.right, r.bottom
    hdc = u32.GetDC(hwnd)
    memdc = g32.CreateCompatibleDC(hdc)
    bmp = g32.CreateCompatibleBitmap(hdc, w, h)
    g32.SelectObject(memdc, bmp)
    u32.PrintWindow(hwnd, memdc, 2)

    class BMIH(ctypes.Structure):
        _fields_ = [('biSize', wt.DWORD), ('biWidth', ctypes.c_int), ('biHeight', ctypes.c_int),
                    ('biPlanes', wt.WORD), ('biBitCount', wt.WORD), ('biCompression', wt.DWORD),
                    ('biSizeImage', wt.DWORD), ('biXPelsPerMeter', ctypes.c_int),
                    ('biYPelsPerMeter', ctypes.c_int), ('biClrUsed', wt.DWORD),
                    ('biClrImportant', wt.DWORD)]

    class BMI(ctypes.Structure):
        _fields_ = [('bmiHeader', BMIH), ('bmiColors', wt.DWORD * 3)]

    bi = BMI()
    bi.bmiHeader.biSize = ctypes.sizeof(BMIH)
    bi.bmiHeader.biWidth = w
    bi.bmiHeader.biHeight = -h
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 32
    buf = ctypes.create_string_buffer(w * h * 4)
    g32.GetDIBits(memdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    px = bytearray(w * h * 3)
    raw = buf.raw
    for y in range(h):
        base = y * w * 4
        for x in range(w):
            o = base + x * 4
            px[(y * w + x) * 3 + 0] = raw[o + 2]
            px[(y * w + x) * 3 + 1] = raw[o + 1]
            px[(y * w + x) * 3 + 2] = raw[o]
    g32.DeleteObject(bmp)
    g32.DeleteDC(memdc)
    u32.ReleaseDC(hwnd, hdc)
    return w, h, bytes(px)


def write_png(path, nw, nh, rows):
    raw = b''.join(b'\x00' + r for r in rows)

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)

    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' +
                           chunk(b'IHDR', struct.pack('>IIBBBBB', nw, nh, 8, 2, 0, 0, 0)) +
                           chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def main():
    p = subprocess.Popen([EXE, '/game', 'pg'], cwd=CWD)
    time.sleep(9)
    hwnd = find_hwnd('PG Forever')
    if not hwnd:
        print('未找到窗口')
        return
    r = wt.RECT()
    u32.GetClientRect(hwnd, ctypes.byref(r))
    W, H = r.right, r.bottom
    print('窗口 %dx%d' % (W, H))

    click(hwnd, int(W * 0.047), int(H * 0.054), 2.2)
    click(hwnd, int(W * 0.5), int(H * 0.62), 2.2)
    click(hwnd, int(W * 0.5), int(H * 0.35), 4.5)
    time.sleep(1.5)

    # hover 文本行在真实坐标 y 505..575，x 1650..1920
    X0, X1, Y0, Y1 = 1640, 1920, 500, 580

    pts = [(x, y)
           for y in range(180, 900, 52)
           for x in range(540, 1200, 55)]
    print('共 %d 个采样点' % len(pts))

    strips = []
    labels = []
    for i, (x, y) in enumerate(pts):
        hover(hwnd, x, y, 0.42)
        w2, h2, px = grab(hwnd)
        row = bytearray()
        for yy in range(Y0, Y1):
            for xx in range(X0, X1):
                o = (yy * w2 + xx) * 3
                row += px[o:o + 3]
        strips.append(bytes(row))
        labels.append((x, y))
        if (i + 1) % 20 == 0:
            print('  ...%d/%d' % (i + 1, len(pts)))

    # 拼成总览：每行间隔 2px 深色分隔
    cw = X1 - X0
    rows = []
    for s in strips:
        for yy in range(Y1 - Y0):
            rows.append(s[yy * cw * 3:(yy + 1) * cw * 3])
        rows.append(b'\x00' * cw * 3)
    nh = len(rows)
    write_png(os.path.join(POC, 'river_strips.png'), cw, nh, rows)
    print('总览 -> river_strips.png (%dx%d), 共 %d 条' % (cw, nh, len(strips)))
    # 同时写出坐标对照
    with open(os.path.join(POC, 'river_strips.txt'), 'w', encoding='utf-8') as fh:
        for i, (x, y) in enumerate(labels):
            fh.write('%3d  (%4d,%4d)\n' % (i, x, y))
    p.terminate()


if __name__ == '__main__':
    main()
