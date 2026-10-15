# -*- coding: utf-8 -*-
"""启动 PGForever 并按窗口截图，保存为 PNG（自实现编码，避免依赖 PIL）。"""
import ctypes
import struct
import subprocess
import sys
import time
import zlib
from ctypes import wintypes

EXE = r'D:\PGForever1.021\PGForever.exe'
CWD = r'D:\PGForever1.021'
OUT = sys.argv[1] if len(sys.argv) > 1 else r'D:\DSH\军事游戏汉化\pgforever\poc\poc1.png'
WAIT = float(sys.argv[2]) if len(sys.argv) > 2 else 9.0

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

gdi = ctypes.windll.gdi32
user = ctypes.windll.user32
user.SetProcessDPIAware()

proc = subprocess.Popen([EXE, '/game', 'pg'], cwd=CWD)
print('started pid=%d, waiting %.1fs ...' % (proc.pid, WAIT))
time.sleep(WAIT)


def find_window():
    """找到游戏主窗口句柄"""
    res = {}

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, lparam):
        if user.IsWindowVisible(hwnd):
            length = user.GetWindowTextLengthW(hwnd) + 1
            buf = ctypes.create_unicode_buffer(length)
            user.GetWindowTextW(hwnd, buf, length)
            pid = wintypes.DWORD()
            user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == proc.pid and buf.value:
                res['hwnd'] = hwnd
                res['title'] = buf.value
        return True

    user.EnumWindows(cb, 0)
    return res


info = find_window()
hwnd = info.get('hwnd')
print('window: hwnd=%s title=%r' % (hwnd, info.get('title', '')))

if hwnd:
    user.ShowWindow(hwnd, 3)          # SW_MAXIMIZE
    user.SetForegroundWindow(hwnd)
    time.sleep(1.2)
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    x, y = max(r.left, 0), max(r.top, 0)
    w, h = r.right - r.left, r.bottom - r.top
    print('rect: %d,%d %dx%d' % (x, y, w, h))
else:
    x, y = 0, 0
    w = user.GetSystemMetrics(0)
    h = user.GetSystemMetrics(1)
    print('fallback to full screen %dx%d' % (w, h))

hdc = user.GetDC(0)
memdc = gdi.CreateCompatibleDC(hdc)
hbmp = gdi.CreateCompatibleBitmap(hdc, w, h)
gdi.SelectObject(memdc, hbmp)
gdi.BitBlt(memdc, 0, 0, w, h, hdc, x, y, 0x00CC0020)  # SRCCOPY


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [('biSize', wintypes.DWORD), ('biWidth', ctypes.c_int), ('biHeight', ctypes.c_int),
                ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', ctypes.c_int),
                ('biYPelsPerMeter', ctypes.c_int), ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)]


bih = BITMAPINFOHEADER()
bih.biSize = ctypes.sizeof(BITMAPINFOHEADER)
bih.biWidth = w
bih.biHeight = -h            # top-down
bih.biPlanes = 1
bih.biBitCount = 32
bih.biCompression = 0
stride = ((w * 32 + 31) // 32) * 4
buf = ctypes.create_string_buffer(stride * h)
gdi.GetDIBits(memdc, hbmp, 0, h, buf, ctypes.byref(bih), 0)

raw_rows = b''
for row in range(h):
    off = row * stride
    line = bytearray()
    px = buf[off:off + stride]
    for i in range(w):
        b, g, r_, a = px[i*4], px[i*4+1], px[i*4+2], px[i*4+3]
        line += bytes((r_, g, b))
    raw_rows += bytes([0]) + bytes(line)


def chunk(tag, data):
    c = struct.pack('>I', len(data)) + tag + data
    return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)


png = b'\x89PNG\r\n\x1a\n'
png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
png += chunk(b'IDAT', zlib.compress(raw_rows, 6))
png += chunk(b'IEND', b'')
open(OUT, 'wb').write(png)
print('saved: %s (%dx%d, %d KB)' % (OUT, w, h, len(png)//1024))

gdi.DeleteObject(hbmp)
gdi.DeleteDC(memdc)
user.ReleaseDC(0, hdc)
print('pid still alive: %s' % (proc.poll() is None))
