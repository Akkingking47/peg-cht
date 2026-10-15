# -*- coding: utf-8 -*-
r"""启动游戏 -> 置顶窗口 -> PrintWindow 截图 -> 退出。
用法: python shot2.py <输出png> [等待秒数] [game]
不依赖点击，只抓当前画面（主菜单信息量已足够）。
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


def kill_all():
    subprocess.run(['taskkill', '/F', '/IM', 'PGForever.exe'], capture_output=True)
    time.sleep(0.8)


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


def shot(hwnd, out):
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
    for row in range(h):
        off = row * stride
        px = buf[off:off + stride]
        line = bytearray(w * 3)
        for i in range(w):
            line[i * 3], line[i * 3 + 1], line[i * 3 + 2] = px[i * 4 + 2], px[i * 4 + 1], px[i * 4]
        rows.append(bytes(line))
    gdi.DeleteObject(hbmp)
    gdi.DeleteDC(memdc)
    user.ReleaseDC(hwnd, hdc)

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b''.join(b'\x00' + x for x in rows)
    with open(out, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def main():
    out = sys.argv[1]
    wait = float(sys.argv[2]) if len(sys.argv) > 2 else 7.0
    game = sys.argv[3] if len(sys.argv) > 3 else 'pg'
    kill_all()
    p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', game], cwd=r'D:\PGForever1.021')
    hwnd = find_hwnd(p.pid)
    if not hwnd:
        print('未找到窗口')
        kill_all()
        return
    user.SetWindowPos(hwnd, -1, 710, 220, 500, 600, 0x0040)
    time.sleep(wait)
    shot(hwnd, out)
    print('已截图 %s' % out)
    try:
        p.terminate()
    except Exception:
        pass
    time.sleep(0.4)
    kill_all()


if __name__ == '__main__':
    main()
