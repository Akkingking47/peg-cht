# -*- coding: utf-8 -*-
r"""
验证长中文简报是否完整（避免 178 个简报白干）。
写入一段带位置标记的长中文，用 PrintWindow 抓取简报界面。
"""
import ctypes
import struct
import subprocess
import time
import zlib
from ctypes import wintypes

user = ctypes.windll.user32
gdi = ctypes.windll.gdi32
k32 = ctypes.windll.kernel32
user.SetProcessDPIAware()
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc'
BRF = r'D:\PGForever1.021\PG\Scenario\0001.pgbrf'
BAK = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\PG\Scenario\0001.pgbrf'

# 长文本：每 30 字一个 ASCII 标记，共约 150 字
LONG = ('<p>一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未[M30]'
        '一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未[M60]'
        '一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未[M90]'
        '一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未[M120]'
        '一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未[M150]'
        '</p>\r\n')
print('长文本 %d 字节 / %d 字符' % (len(LONG.encode('utf-8')), len(LONG)))


def kill_all():
    subprocess.run(['taskkill', '/F', '/IM', 'PGForever.exe'], capture_output=True)
    time.sleep(1.0)


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


def pw(hwnd, out):
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = user.GetWindowDC(hwnd)
    memdc = gdi.CreateCompatibleDC(hdc)
    hbmp = gdi.CreateCompatibleBitmap(hdc, w, h)
    gdi.SelectObject(memdc, hbmp)
    user.PrintWindow(hwnd, memdc, 2)

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
    user.ReleaseDC(hwnd, hdc)

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + x for x in rows)
    open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                          + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def click(hwnd, lx, ly, wait=2.2):
    user.SetForegroundWindow(hwnd)
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    user.SetCursorPos(r.left + lx, r.top + ly)
    time.sleep(0.35)
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.12)
    user.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(wait)


open(BRF, 'wb').write(LONG.encode('utf-8'))
kill_all()
p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
hwnd = find_hwnd(p.pid)
print('hwnd=%s' % hwnd)
user.SetWindowPos(hwnd, -1, 710, 220, 500, 600, 0x0040)
time.sleep(2.5)
user.SetForegroundWindow(hwnd)
time.sleep(1.5)
pw(hwnd, OUT + r'\v0_menu.png')
click(hwnd, 200, 148)
click(hwnd, 245, 538, 3.0)
pw(hwnd, OUT + r'\v1_brief.png')
click(hwnd, 245, 538, 3.0)
pw(hwnd, OUT + r'\v2_next.png')
p.terminate()
time.sleep(0.5)
kill_all()
open(BRF, 'wb').write(open(BAK, 'rb').read())
print('已恢复原文，截图: v0_menu / v1_brief / v2_next')
