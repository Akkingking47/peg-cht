# -*- coding: utf-8 -*-
r"""
绕过 options 对话框：启动后不点列表项，直接点「开始!」进入简报。
用途：① 定位 pgbrf 中文的截断点 ② 验证长 ASCII 是否正常
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

CHUNK = '一二三四五六七八九十甲乙丙丁戊己庚辛壬癸'
ZH = '<p>' + ''.join(CHUNK + '[%d]' % (i * 20) for i in range(1, 8)) + '</p>\r\n'
LONG_ASCII = '<p>' + ('ABCDEFGHIJ' * 20) + '[END-200]' + ('KLMNOPQRST' * 20) + '[END-400]</p>\r\n'


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
        time.sleep(0.35)
        if user.GetForegroundWindow() == hwnd:
            return True
    return False


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


def click(hwnd, lx, ly, wait=2.2):
    force_focus(hwnd)
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    tgt = (r.left + lx, r.top + ly)
    user.SetCursorPos(*tgt)
    time.sleep(0.3)
    p = wintypes.POINT()
    user.GetCursorPos(ctypes.byref(p))
    if abs(p.x - tgt[0]) > 1 or abs(p.y - tgt[1]) > 1:
        user.SetCursorPos(tgt[0] + (tgt[0] - p.x), tgt[1] + (tgt[1] - p.y))
        time.sleep(0.2)
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.12)
    user.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(wait)


def run(tag, content):
    open(BRF, 'wb').write(content)
    p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
    hwnd = find_hwnd(25)
    print('[%s] hwnd=%s' % (tag, hwnd))
    user.SetWindowPos(hwnd, -1, 710, 220, 500, 600, 0x0040)
    time.sleep(2.5)
    force_focus(hwnd)
    time.sleep(1.0)
    click(hwnd, 245, 538)            # 开始!
    ox, oy, w, h, rows = grab(hwnd)
    save(os.path.join(OUTDIR, 'n_%s_1.png' % tag), w, h, rows)
    click(hwnd, 245, 538, 2.5)
    ox, oy, w, h, rows = grab(hwnd)
    save(os.path.join(OUTDIR, 'n_%s_2.png' % tag), w, h, rows)
    print('[%s] 已截图 n_%s_1.png / n_%s_2.png' % (tag, tag, tag))
    p.terminate()
    try:
        p.wait(timeout=6)
    except Exception:
        p.kill()
    time.sleep(1.0)


which = sys.argv[1] if len(sys.argv) > 1 else 'zh'
if which == 'zh':
    run('zh', ZH.encode('utf-8'))
else:
    run('ascii', LONG_ASCII.encode('utf-8'))
open(BRF, 'wb').write(open(BAK, 'rb').read())
print('已恢复原文')
