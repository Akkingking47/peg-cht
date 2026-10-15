# -*- coding: utf-8 -*-
r"""启动游戏 → 等战役列表渲染 → PrintWindow 截图（免点击）"""
import ctypes
import os
import subprocess
import sys
import time

k32 = ctypes.windll.kernel32
user = ctypes.windll.user32
gdi = ctypes.windll.gdi32
GAME = r'D:\PGForever1.021\PGForever.exe'


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [('biSize', ctypes.c_uint32), ('biWidth', ctypes.c_int32),
                ('biHeight', ctypes.c_int32), ('biPlanes', ctypes.c_uint16),
                ('biBitCount', ctypes.c_uint16), ('biCompression', ctypes.c_uint32),
                ('biSizeImage', ctypes.c_uint32), ('biXPelsPerMeter', ctypes.c_int32),
                ('biYPelsPerMeter', ctypes.c_int32), ('biClrUsed', ctypes.c_uint32),
                ('biClrImportant', ctypes.c_uint32)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', ctypes.c_uint32 * 3)]


def kill():
    subprocess.run(['taskkill', '/F', '/IM', 'PGForever.exe'], capture_output=True)
    time.sleep(1.0)


def find_hwnd(pid, timeout=25):
    end = time.time() + timeout
    while time.time() < end:
        res = {}

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def cb(h, l):
            p = ctypes.c_ulong()
            user.GetWindowThreadProcessId(h, ctypes.byref(p))
            if p.value == pid:
                n = user.GetWindowTextLengthW(h) + 1
                b = ctypes.create_unicode_buffer(n)
                user.GetWindowTextW(h, b, n)
                if b.value.startswith('PG Forever'):
                    res['h'] = h
            return True
        user.EnumWindows(cb, 0)
        if 'h' in res:
            return res['h']
        time.sleep(0.3)
    return None


def shot(hwnd, path):
    r = ctypes.wintypes.RECT()
    user.GetClientRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    if w <= 0 or h <= 0:
        print('尺寸异常', w, h); return False
    hdc = user.GetDC(hwnd)
    mdc = gdi.CreateCompatibleDC(hdc)
    bmp = gdi.CreateCompatibleBitmap(hdc, w, h)
    gdi.SelectObject(mdc, bmp)
    # flags=2 → PW_RENDERFULLCONTENT
    ok = user.PrintWindow(hwnd, mdc, 2)
    bi = BITMAPINFO()
    bi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.bmiHeader.biWidth = w
    bi.bmiHeader.biHeight = -h
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 32
    bi.bmiHeader.biCompression = 0
    size = w * h * 4
    buf = ctypes.create_string_buffer(size)
    gdi.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    # BGRX -> 存 PNG
    from PIL import Image
    img = Image.frombuffer('RGB', (w, h), buf, 'raw', 'BGRX', 0, 1)
    img.save(path)
    gdi.DeleteObject(bmp)
    gdi.DeleteDC(mdc)
    user.ReleaseDC(hwnd, hdc)
    print('截图 %s (%dx%d) PrintWindow=%s' % (path, w, h, ok))
    return True


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else 'shot'
    out = r'D:\DSH\军事游戏汉化\pgforever\poc\cam_shot_%s.png' % tag
    kill()
    p = subprocess.Popen([GAME, '/game', 'pg'], cwd=os.path.dirname(GAME))
    hwnd = find_hwnd(p.pid)
    if not hwnd:
        print('无窗口'); kill(); return
    print('hwnd=%s' % hwnd)
    time.sleep(float(sys.argv[2]) if len(sys.argv) > 2 else 8.0)
    shot(hwnd, out)
    kill()


main()
