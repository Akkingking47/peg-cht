# -*- coding: utf-8 -*-
r"""
进入战斗，依次把鼠标移到若干六角格，每格保存一张全窗口截图。
之后人工/自动检查哪个格是河流、地名是否已汉化。

用法: python probe_river2.py [起点索引]
"""
import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
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


def hover(hwnd, x, y, pause=0.7):
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


def save_png(w, h, px, out, crop=None, scale=1):
    x0, y0, x1, y1 = crop if crop else (0, 0, w, h)
    rows = []
    for y in range(y0, y1):
        row = bytearray()
        for x in range(x0, x1):
            o = (y * w + x) * 3
            row += px[o:o + 3] * scale
        for _ in range(scale):
            rows.append(bytes(row))
    nh, nw = len(rows), (x1 - x0) * scale
    raw = b''.join(b'\x00' + r for r in rows)

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)

    open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' +
                          chunk(b'IHDR', struct.pack('>IIBBBBB', nw, nh, 8, 2, 0, 0, 0)) +
                          chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
    return nw, nh


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

    click(hwnd, int(W * 0.047), int(H * 0.054), 2.2)   # PG 徽章
    click(hwnd, int(W * 0.5), int(H * 0.62), 2.2)      # 开始
    click(hwnd, int(W * 0.5), int(H * 0.35), 4.5)      # 第一战役
    time.sleep(1.5)

    # 地图大致 (500..1240, 140..940)。六角格宽约 46px，高约 40px。
    # 取若干河网密集处（按截图目视：中部有明显河流）
    pts = [(560, 300), (640, 340), (700, 260), (780, 300), (860, 340),
           (620, 420), (700, 480), (800, 460), (900, 400), (1000, 380),
           (760, 560), (860, 600), (960, 640), (1060, 600), (1100, 500),
           (600, 600), (700, 700), (820, 720), (940, 780), (1060, 760)]
    for i, (x, y) in enumerate(pts):
        hover(hwnd, x, y, 0.75)
        w2, h2, px = grab(hwnd)
        tgt = os.path.join(POC, 'rv_%02d_%d_%d.png' % (i, x, y))
        save_png(w2, h2, px, tgt, crop=(520, 240, 1120, 900))
        print('  %2d (%4d,%4d) -> %s' % (i, x, y, os.path.basename(tgt)))
    print('完成')
    p.terminate()


if __name__ == '__main__':
    main()
