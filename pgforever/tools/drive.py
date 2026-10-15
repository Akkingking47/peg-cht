# -*- coding: utf-8 -*-
r"""
PGForever 驱动脚本：截屏 / 点击 / 按键，用于逐个界面验证 UI 汉化效果。
用法:
  python drive.py shot  <out.png>
  python drive.py click <x> <y>            # 屏幕绝对坐标
  python drive.py move  <x> <y>            # 移动鼠标（用于看 tooltip / hover 面板）
  python drive.py key   <vk> [repeat]      # 虚拟键码，如 27=Esc 13=Enter 32=Space
  python drive.py seq   <out_prefix>       # 连续截图若干张（观察动画/延时界面）
"""
import ctypes
import struct
import sys
import time
import zlib
from ctypes import wintypes

user = ctypes.windll.user32
gdi = ctypes.windll.gdi32

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass
user.SetProcessDPIAware()


def find_hwnd():
    res = {}

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, lparam):
        if user.IsWindowVisible(hwnd):
            n = user.GetWindowTextLengthW(hwnd) + 1
            buf = ctypes.create_unicode_buffer(n)
            user.GetWindowTextW(hwnd, buf, n)
            if buf.value.startswith('PG Forever'):
                res['hwnd'] = hwnd
                res['title'] = buf.value
        return True

    user.EnumWindows(cb, 0)
    return res


def screenshot(out):
    info = find_hwnd()
    hwnd = info.get('hwnd')
    if hwnd:
        r = wintypes.RECT()
        user.GetWindowRect(hwnd, ctypes.byref(r))
        x, y, w, h = r.left, r.top, r.right - r.left, r.bottom - r.top
    else:
        x = y = 0
        w, h = user.GetSystemMetrics(0), user.GetSystemMetrics(1)

    hdc = user.GetDC(0)
    memdc = gdi.CreateCompatibleDC(hdc)
    hbmp = gdi.CreateCompatibleBitmap(hdc, w, h)
    gdi.SelectObject(memdc, hbmp)
    gdi.BitBlt(memdc, 0, 0, w, h, hdc, x, y, 0x00CC0020)

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

    rows = bytearray()
    for row in range(h):
        off = row * stride
        rows += b'\x00'
        px = buf[off:off + stride]
        for i in range(w):
            rows += bytes((px[i*4+2], px[i*4+1], px[i*4]))

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(rows), 6)) + chunk(b'IEND', b'')
    open(out, 'wb').write(png)
    gdi.DeleteObject(hbmp)
    gdi.DeleteDC(memdc)
    user.ReleaseDC(0, hdc)
    print('shot %s  %dx%d' % (out, w, h))


def click(x, y):
    user.SetCursorPos(int(x), int(y))
    time.sleep(0.15)
    user.mouse_event(0x0002, 0, 0, 0, 0)   # LEFTDOWN
    time.sleep(0.06)
    user.mouse_event(0x0004, 0, 0, 0, 0)   # LEFTUP
    print('click %s,%s' % (x, y))


def move(x, y):
    user.SetCursorPos(int(x), int(y))
    print('move %s,%s' % (x, y))


def key(vk, repeat=1):
    for _ in range(int(repeat)):
        user.keybd_event(vk, 0, 0, 0)
        time.sleep(0.05)
        user.keybd_event(vk, 0, 2, 0)
        time.sleep(0.25)
    print('key vk=%s x%s' % (vk, repeat))


cmd = sys.argv[1]
if cmd != 'launch':
    info = find_hwnd()
    print('window: %r' % info.get('title'))
if cmd == 'shot':
    screenshot(sys.argv[2])
elif cmd == 'click':
    click(sys.argv[2], sys.argv[3])
elif cmd == 'move':
    move(sys.argv[2], sys.argv[3])
elif cmd == 'key':
    key(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 1)
elif cmd == 'seq':
    pre = sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    gap = float(sys.argv[4]) if len(sys.argv) > 4 else 0.7
    for i in range(n):
        screenshot('%s_%d.png' % (pre, i))
        time.sleep(gap)
elif cmd == 'max':
    info = find_hwnd()
    hwnd = info.get('hwnd')
    user.ShowWindow(hwnd, 3)          # SW_MAXIMIZE
    user.SetForegroundWindow(hwnd)
    time.sleep(1.0)
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    print('maximized -> %d,%d %dx%d' % (r.left, r.top, r.right - r.left, r.bottom - r.top))
elif cmd == 'launch':
    import subprocess
    game = sys.argv[2] if len(sys.argv) > 2 else 'pg'
    wait = float(sys.argv[3]) if len(sys.argv) > 3 else 9.0
    DETACHED = 0x00000008 | 0x00000200       # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', game],
                         cwd=r'D:\PGForever1.021', creationflags=DETACHED,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('launched pid=%d game=%s' % (p.pid, game))
    time.sleep(wait)
    print('after %.1fs alive=%s' % (wait, p.poll() is None))
else:
    raise SystemExit('unknown cmd')
