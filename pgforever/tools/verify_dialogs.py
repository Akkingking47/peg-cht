# -*- coding: utf-8 -*-
r"""
对话框渲染验证（无需输入）：
把待验证的 UI htm 临时复制到启动时加载的 menu.htm 位置，启动游戏截图，然后恢复。
用于在无法注入鼠标点击的环境里，逐个确认每个界面的中文渲染、字体与排版。
"""
import ctypes
import os
import shutil
import struct
import subprocess
import sys
import time
import zlib
from ctypes import wintypes

user = ctypes.windll.user32
gdi = ctypes.windll.gdi32
user.SetProcessDPIAware()

UI = r'D:\PGForever1.021\Default\UI'
ORIG = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\Default\UI'
OUTDIR = r'D:\DSH\军事游戏汉化\pgforever\poc'
EXE = r'D:\PGForever1.021\PGForever.exe'
CWD = r'D:\PGForever1.021'

TARGETS = sys.argv[1:] if len(sys.argv) > 1 else ['settings.htm']


def find_hwnd(timeout=20):
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


def shot_window(hwnd, out, newsize=(1200, 900)):
    if newsize:
        user.SetWindowPos(hwnd, 0, 0, 0, newsize[0], newsize[1], 0x0040 | 0x0004)
        time.sleep(1.2)
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

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + r_ for r_ in rows)
    open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                          + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
    gdi.DeleteObject(hbmp)
    gdi.DeleteDC(memdc)
    user.ReleaseDC(0, hdc)
    print('    shot %s %dx%d' % (os.path.basename(out), w, h))


menu = os.path.join(UI, 'menu.htm')
menu_backup = os.path.join(OUTDIR, '_menu_ui_backup.htm')
shutil.copy2(menu, menu_backup)
print('已备份当前 menu.htm -> %s' % menu_backup)

for i, t in enumerate(TARGETS):
    src = os.path.join(UI, t)
    if not os.path.exists(src):
        print('跳过（不存在）: %s' % t)
        continue
    print('[%d/%d] %s' % (i + 1, len(TARGETS), t))
    shutil.copy2(src, menu)
    p = subprocess.Popen([EXE, '/game', 'pg'], cwd=CWD)
    hwnd = find_hwnd(20)
    if not hwnd:
        print('    !! 未找到窗口')
        p.terminate()
        time.sleep(1)
        continue
    time.sleep(2.5)
    name = t.replace('.htm', '')
    try:
        shot_window(hwnd, os.path.join(OUTDIR, 'dlg_%s.png' % name))
    except Exception as e:
        print('    截图失败: %s' % e)
    p.terminate()
    try:
        p.wait(timeout=6)
    except Exception:
        p.kill()
    time.sleep(1.0)

shutil.copy2(menu_backup, menu)
print('已恢复 menu.htm')
