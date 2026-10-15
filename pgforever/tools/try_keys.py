# -*- coding: utf-8 -*-
r"""
键盘驱动测试：只靠按键推进界面，验证 pgeqp(装备名) / pgbrf(简报) 的中文能否显示。
启动 -> 确认前台 -> 发送按键 -> 每步截图
"""
import ctypes
import os
import struct
import subprocess
import sys
import time
import zlib
from ctypes import wintypes

user = ctypes.windll.user32
gdi = ctypes.windll.gdi32
user.SetProcessDPIAware()

OUTDIR = r'D:\DSH\军事游戏汉化\pgforever\poc'


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


def shot(hwnd, out, w=1200, h=800):
    user.SetWindowPos(hwnd, 0, 0, 0, w, h, 0x0040 | 0x0004)
    time.sleep(0.9)
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
        for i in range(ww):
            line[i*3], line[i*3+1], line[i*3+2] = px[i*4+2], px[i*4+1], px[i*4]
        rows.append(bytes(line))

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + x for x in rows)
    open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', ww, hh, 8, 2, 0, 0, 0))
                          + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
    gdi.DeleteObject(hbmp)
    gdi.DeleteDC(memdc)
    user.ReleaseDC(0, hdc)
    print('  shot %s' % os.path.basename(out))


def press(hwnd, vk, wait=1.5):
    fg = user.GetForegroundWindow()
    print('  key vk=%s (fg==game: %s)' % (vk, fg == hwnd))
    user.PostMessageW(hwnd, 0x0100, vk, 0)   # WM_KEYDOWN
    time.sleep(0.05)
    user.PostMessageW(hwnd, 0x0101, vk, 0)   # WM_KEYUP
    time.sleep(wait)


p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
hwnd = find_hwnd(25)
print('hwnd=%s' % hwnd)
if not hwnd:
    sys.exit('no window')
user.ShowWindow(hwnd, 3)
user.SetForegroundWindow(hwnd)
time.sleep(2)
print('foreground==game: %s' % (user.GetForegroundWindow() == hwnd))
shot(hwnd, os.path.join(OUTDIR, 'k0_menu.png'))

press(hwnd, 0x0D, 2.5)      # Enter
shot(hwnd, os.path.join(OUTDIR, 'k1_enter.png'))
press(hwnd, 0x0D, 2.5)      # Enter
shot(hwnd, os.path.join(OUTDIR, 'k2_enter.png'))
press(hwnd, 0x50, 2.5)      # P = purchase
shot(hwnd, os.path.join(OUTDIR, 'k3_p.png'))
press(hwnd, 0x1B, 2.0)      # Esc
shot(hwnd, os.path.join(OUTDIR, 'k4_esc.png'))
print('alive=%s' % (p.poll() is None))
