# -*- coding: utf-8 -*-
r"""
进入战斗后，扫描地图六角格，找出渲染出「河」字的地块信息，验证河流名汉化。

做法：进入战斗后，把鼠标 PostMessage 到地图区域各六角格中心，
每次截图并裁剪右侧 HoverHexInfo 文本区，检测是否出现「河」字，
命中则保存放大图。

用法: python probe_river_ingame.py
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


def click(hwnd, x, y, pause=0.7):
    lp = (y << 16) | x
    u32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    time.sleep(0.12)
    u32.PostMessageW(hwnd, WM_LBUTTONDOWN, 1, lp)
    time.sleep(0.06)
    u32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    time.sleep(pause)


def hover(hwnd, x, y, pause=0.55):
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
        for x in range(w):
            o = y * w * 4
            px[(y * w + x) * 3 + 0] = raw[o + x * 4 + 2]
            px[(y * w + x) * 3 + 1] = raw[o + x * 4 + 1]
            px[(y * w + x) * 3 + 2] = raw[o + x * 4 + 0]
    g32.DeleteObject(bmp)
    g32.DeleteDC(memdc)
    u32.ReleaseDC(hwnd, hdc)
    return w, h, bytes(px)


def save_png(w, h, px, out, crop=None, scale=1):
    x0, y0, x1, y1 = crop if crop else (0, 0, w, h)
    cw, chh = x1 - x0, y1 - y0
    rows = []
    for y in range(y0, y1):
        row = bytearray()
        for x in range(x0, x1):
            o = (y * w + x) * 3
            row += px[o:o + 3] * scale
        for _ in range(scale):
            rows.append(bytes(row))
    nh = len(rows)
    nw = cw * scale
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

    click(hwnd, int(W * 0.047), int(H * 0.054), 2.0)      # PG 徽章
    click(hwnd, int(W * 0.5), int(H * 0.62), 2.0)         # 开始
    click(hwnd, int(W * 0.5), int(H * 0.35), 4.0)         # 第一战役
    time.sleep(2)

    # 地图约在 (500..1240, 100..940)（1920x1080 下），扫格心
    best = []
    xs = list(range(int(W * 0.28), int(W * 0.63), 46))
    ys = list(range(int(H * 0.12), int(H * 0.85), 40))
    n = 0
    for y in ys:
        for x in xs:
            hover(hwnd, x, y, 0.42)
            w2, h2, px = grab(hwnd)
            # HoverHexInfo 文本区：右栏 x 1460..1880, y 560..760
            cx0, cy0, cx1, cy1 = int(W * 0.755), int(H * 0.50), int(W * 0.985), int(H * 0.72)
            # 检测黄字像素（河字笔画）
            ink = 0
            for yy in range(cy0, cy1):
                for xx in range(cx0, cx1):
                    o = (yy * w2 + xx) * 3
                    rr, gg, bb = px[o], px[o + 1], px[o + 2]
                    if rr > 150 and gg > 110 and bb < 120:
                        ink += 1
            if ink > 120:
                n += 1
                tgt = os.path.join(POC, 'riv_p%s_%d_%d.png' % (n, x, y))
                save_png(w2, h2, px, tgt, crop=(cx0, cy0, cx1, cy1), scale=3)
                best.append((x, y, ink, tgt))
                print('  命中 #%d (%d,%d) ink=%d -> %s' % (n, x, y, ink, os.path.basename(tgt)))
                if n >= 6:
                    break
        if n >= 6:
            break

    print('扫描完成，命中 %d 处' % len(best))
    p.terminate()


if __name__ == '__main__':
    main()
