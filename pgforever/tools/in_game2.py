# -*- coding: utf-8 -*-
r"""
进入游戏内部：窗口固定 500x600，用精确坐标点击。
目标：进到场景 -> 看简报(pgbrf) -> 按 P 看征募(equipment.pgeqp)。
窗口位置动态读取，坐标换算为屏幕坐标；全程保持 TOPMOST 以免被遮挡。
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
OUTDIR = r'D:\DSH\军事游戏汉化\pgforever\poc'
HWND_TOPMOST, HWND_NOTOPMOST = -1, -2
SWP_SHOWWINDOW = 0x0040


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


def grab(hwnd):
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
    gdi.DeleteObject(hbmp)
    gdi.DeleteDC(memdc)
    user.ReleaseDC(0, hdc)
    return r.left, r.top, w, h, rows


def save(path, w, h, rows):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + x for x in rows)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def click(hwnd, lx, ly):
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    sx, sy = r.left + lx, r.top + ly
    user.SetCursorPos(sx, sy)
    time.sleep(0.35)
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.12)
    user.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(1.8)


def key(hwnd, vk, wait=2.0):
    user.keybd_event(vk, 0, 0, 0)
    time.sleep(0.08)
    user.keybd_event(vk, 0, 2, 0)
    time.sleep(wait)


p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
hwnd = find_hwnd(25)
print('hwnd=%s' % hwnd)
user.SetWindowPos(hwnd, HWND_TOPMOST, 710, 220, 500, 600, SWP_SHOWWINDOW)
time.sleep(1.5)
user.SetForegroundWindow(hwnd)
time.sleep(1.0)
ox, oy, w, h, rows = grab(hwnd)
print('窗口 (%d,%d) %dx%d' % (ox, oy, w, h))
save(os.path.join(OUTDIR, 'i0.png'), w, h, rows)

# 1) 选中列表第一项（1939）
click(hwnd, 200, 148)
# 2) 底部「开始!」
click(hwnd, 245, 538)
ox, oy, w, h, rows = grab(hwnd)
save(os.path.join(OUTDIR, 'i1.png'), w, h, rows)
print('i1 已截图 (500x600)')

# 3) 再点几次「开始!」推进（场景列表 -> 场景）
for i in range(2, 5):
    click(hwnd, 245, 538)
    ox, oy, w, h, rows = grab(hwnd)
    save(os.path.join(OUTDIR, 'i%d.png' % i), w, h, rows)
    print('i%d 已截图' % i)

# 4) 尝试 P 打开征募
key(hwnd, 0x50, 2.5)
ox, oy, w, h, rows = grab(hwnd)
save(os.path.join(OUTDIR, 'i9_purchase.png'), w, h, rows)
print('i9_purchase 已截图')

user.SetWindowPos(hwnd, HWND_NOTOPMOST, 710, 220, 500, 600, SWP_SHOWWINDOW)
print('alive=%s' % (p.poll() is None))
