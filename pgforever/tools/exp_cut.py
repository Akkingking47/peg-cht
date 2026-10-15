# -*- coding: utf-8 -*-
r"""
定位 pgbrf 的截断点：写入一段带位置标记的中文，观察哪些标记还能显示出来。
标记用 ASCII 方括号数字，便于识别。
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
k32 = ctypes.windll.kernel32
user.SetProcessDPIAware()
OUTDIR = r'D:\DSH\军事游戏汉化\pgforever\poc'
BRF = r'D:\PGForever1.021\PG\Scenario\0001.pgbrf'
BAK = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\PG\Scenario\0001.pgbrf'

# 每 20 个汉字打一个标记
CHUNK = '一二三四五六七八九十甲乙丙丁戊己庚辛壬癸'
parts = []
for i in range(1, 8):
    parts.append(CHUNK * 1)
    parts.append('[%d]' % (i * 20))
ZH = '<p>' + ''.join(parts) + '</p>\r\n'
print('测试文本字节数 %d，字符数 %d' % (len(ZH.encode('utf-8')), len(ZH)))
print('内容: ' + ZH[:80])


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


def force_focus(hwnd):
    for _ in range(3):
        try:
            fg = user.GetForegroundWindow()
            t1 = user.GetWindowThreadProcessId(fg, None)
            t2 = user.GetWindowThreadProcessId(hwnd, None)
            cur = k32.GetCurrentThreadId()
            user.AttachThreadInput(cur, t1, True)
            user.AttachThreadInput(cur, t2, True)
            user.ShowWindow(hwnd, 9)
            user.BringWindowToTop(hwnd)
            user.SetForegroundWindow(hwnd)
            user.AttachThreadInput(cur, t1, False)
            user.AttachThreadInput(cur, t2, False)
        except Exception:
            pass
        time.sleep(0.4)
        if user.GetForegroundWindow() == hwnd:
            return True
    return user.GetForegroundWindow() == hwnd


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


def click(hwnd, lx, ly, wait=2.0):
    force_focus(hwnd)
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    user.SetCursorPos(r.left + lx, r.top + ly)
    time.sleep(0.3)
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.12)
    user.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(wait)


open(BRF, 'wb').write(ZH.encode('utf-8'))
p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
hwnd = find_hwnd(25)
if hwnd:
    user.SetWindowPos(hwnd, -1, 710, 220, 500, 600, 0x0040)
    time.sleep(2.0)
    print('focus=%s' % force_focus(hwnd))
    time.sleep(1.5)
    click(hwnd, 200, 148)
    # 用 Enter 确认 options 对话框（鼠标点击有像素偏差，容易点空）
    for _ in range(2):
        force_focus(hwnd)
        user.keybd_event(0x0D, 0, 0, 0)
        time.sleep(0.08)
        user.keybd_event(0x0D, 0, 2, 0)
        time.sleep(2.0)
    ox, oy, w, h, rows = grab(hwnd)
    save(os.path.join(OUTDIR, 'cut_a.png'), w, h, rows)
    click(hwnd, 245, 538)
    time.sleep(1.0)
    ox, oy, w, h, rows = grab(hwnd)
    save(os.path.join(OUTDIR, 'cut_test.png'), w, h, rows)
    print('已截图 cut_test.png')
p.terminate()
try:
    p.wait(timeout=6)
except Exception:
    p.kill()
open(BRF, 'wb').write(open(BAK, 'rb').read())
print('已恢复原文')
