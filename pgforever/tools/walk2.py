# -*- coding: utf-8 -*-
r"""最小化所有其它窗口后再驱动游戏, 解决 SetForegroundWindow 失败导致点击无效。
用法: python walk2.py <前缀>
"""
import ctypes
import struct
import subprocess
import sys
import time
import zlib
from ctypes import wintypes
import ctypes as _ct

user = ctypes.windll.user32
gdi = ctypes.windll.gdi32
user.SetProcessDPIAware()
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc'
SW_MINIMIZE = 6


def minimize_all_others(keep_pid=None):
    """把除 keep_pid 之外的所有可见顶层窗口最小化"""
    n = 0

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(h, l):
        nonlocal n
        if not user.IsWindowVisible(h):
            return True
        if user.GetWindowTextLengthW(h) == 0:
            return True
        if keep_pid is not None:
            p = wintypes.DWORD()
            user.GetWindowThreadProcessId(h, ctypes.byref(p))
            if p.value == keep_pid:
                return True
        # 跳过 shell 窗口
        cls = ctypes.create_unicode_buffer(256)
        user.GetClassNameW(h, cls, 256)
        if cls.value in ('Shell_TrayWnd', 'Shell_SecondaryTrayWnd', 'Progman', 'WorkerW'):
            return True
        user.ShowWindow(h, SW_MINIMIZE)
        n += 1
        return True

    user.EnumWindows(cb, 0)
    return n


def kill_all():
    subprocess.run(['taskkill', '/F', '/IM', 'PGForever.exe'], capture_output=True)
    time.sleep(0.9)


def find_hwnd(pid, timeout=25):
    end = time.time() + timeout
    while time.time() < end:
        res = {}

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def cb(h, l):
            if user.IsWindowVisible(h):
                n = user.GetWindowTextLengthW(h) + 1
                b = ctypes.create_unicode_buffer(n)
                user.GetWindowTextW(h, b, n)
                p = wintypes.DWORD()
                user.GetWindowThreadProcessId(h, ctypes.byref(p))
                if p.value == pid and b.value.startswith('PG Forever'):
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
    hdc = user.GetWindowDC(hwnd)
    memdc = gdi.CreateCompatibleDC(hdc)
    hbmp = gdi.CreateCompatibleBitmap(hdc, w, h)
    gdi.SelectObject(memdc, hbmp)
    user.PrintWindow(hwnd, memdc, 2)

    class BIH(ctypes.Structure):
        _fields_ = [('biSize', wintypes.DWORD), ('biWidth', _ct.c_int), ('biHeight', _ct.c_int),
                    ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                    ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', _ct.c_int),
                    ('biYPelsPerMeter', _ct.c_int), ('biClrUsed', wintypes.DWORD),
                    ('biClrImportant', wintypes.DWORD)]

    bih = BIH()
    bih.biSize = ctypes.sizeof(BIH)
    bih.biWidth, bih.biHeight = w, -h
    bih.biPlanes, bih.biBitCount, bih.biCompression = 1, 32, 0
    stride = ((w * 32 + 31) // 32) * 4
    buf = ctypes.create_string_buffer(stride * h)
    gdi.GetDIBits(memdc, hbmp, 0, h, buf, ctypes.byref(bih), 0)
    rows = []
    ink = 0
    for row in range(h):
        off = row * stride
        px = buf[off:off + stride]
        line = bytearray(w * 3)
        for i in range(w):
            b_, g_, r_ = px[i * 4], px[i * 4 + 1], px[i * 4 + 2]
            line[i * 3], line[i * 3 + 1], line[i * 3 + 2] = r_, g_, b_
            if r_ + g_ + b_ > 330:
                ink += 1
        rows.append(bytes(line))
    gdi.DeleteObject(hbmp)
    gdi.DeleteDC(memdc)
    user.ReleaseDC(hwnd, hdc)

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b''.join(b'\x00' + x for x in rows)
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
    return png, ink


def click(hwnd, lx, ly, wait=1.8):
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    user.SetCursorPos(r.left + lx, r.top + ly)
    time.sleep(0.3)
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.1)
    user.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(wait)


def main():
    pre = sys.argv[1] if len(sys.argv) > 1 else 'x'
    kill_all()
    minimized = minimize_all_others()
    print('已最小化其它窗口: %d 个' % minimized)
    time.sleep(0.6)

    p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
    hwnd = find_hwnd(p.pid)
    if not hwnd:
        print('未找到窗口')
        kill_all()
        return
    user.SetWindowPos(hwnd, -1, 710, 220, 500, 600, 0x0040)
    time.sleep(2.0)
    for _ in range(5):
        user.SetForegroundWindow(hwnd)
        time.sleep(0.4)
        if user.GetForegroundWindow() == hwnd:
            break
    fg = user.GetForegroundWindow() == hwnd
    print('游戏是否前台: %s' % fg)

    stats = []

    def frame(name):
        png, ink = grab(hwnd)
        open(r'%s\%s_%s.png' % (OUT, pre, name), 'wb').write(png)
        stats.append((name, ink))

    frame('s0')
    seq = [(200, 148, 'a1'), (245, 538, 'a2'), (245, 538, 'a3'),
           (245, 538, 'a4'), (245, 538, 'a5'), (245, 538, 'a6')]
    for x, y, nm in seq:
        click(hwnd, x, y)
        frame(nm)
    for nm, ink in stats:
        print('%-6s 墨迹=%d' % (nm, ink))
    try:
        p.terminate()
    except Exception:
        pass
    time.sleep(0.4)
    kill_all()


if __name__ == '__main__':
    main()
