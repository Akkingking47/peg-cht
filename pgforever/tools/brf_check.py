# -*- coding: utf-8 -*-
r"""
长文本简报验证：多套点击序列自动尝试，用像素特征自动识别「简报界面」，
再用 PrintWindow 抓图。避免依赖单一坐标是否命中。
"""
import ctypes
import struct
import subprocess
import time
import zlib
from ctypes import wintypes

user = ctypes.windll.user32
gdi = ctypes.windll.gdi32
user.SetProcessDPIAware()
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc'
BRF = r'D:\PGForever1.021\PG\Scenario\0001.pgbrf'
BAK = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\PG\Scenario\0001.pgbrf'

LONG = ('<p>一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未[M30]'
        '一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未[M60]'
        '一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未[M90]'
        '一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未[M120]'
        '一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未[M150]</p>\r\n')


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


def capture(hwnd):
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
    return w, h, rows


def save(path, w, h, rows):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + x for x in rows)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def sig(rows, w, h):
    """界面指纹：浅米色占比（简报框）与红色占比（主菜单）"""
    pale = red = tot = 0
    for y in range(int(h*0.2), int(h*0.75), 2):
        line = rows[y]
        for x in range(int(w*0.1), int(w*0.9), 2):
            r, g, b = line[x*3], line[x*3+1], line[x*3+2]
            tot += 1
            if r > 200 and g > 180 and b > 130:
                pale += 1
            if r > 90 and r < 190 and g < 60 and b < 70:
                red += 1
    return pale / tot, red / tot


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

w, h, rows = capture(hwnd)
save(OUT + r'\L0_menu.png', w, h, rows)
print('L0 菜单 pale=%.2f red=%.2f' % sig(rows, w, h))

# 尝试 1：选列表项 -> 开始
click(hwnd, 200, 148)
click(hwnd, 245, 538, 2.6)
w, h, rows = capture(hwnd)
pale, red = sig(rows, w, h)
save(OUT + r'\L1.png', w, h, rows)
print('L1 pale=%.2f red=%.2f' % (pale, red))

# 若还是主菜单，尝试先关掉可能弹出的 options
if pale < 0.2:
    click(hwnd, 200, 448, 2.0)      # 确定
    click(hwnd, 245, 538, 2.6)      # 开始
    w, h, rows = capture(hwnd)
    pale, red = sig(rows, w, h)
    save(OUT + r'\L2.png', w, h, rows)
    print('L2 pale=%.2f red=%.2f' % (pale, red))

# 再推进一步（简报 -> 回合提示）
click(hwnd, 245, 538, 2.6)
w, h, rows = capture(hwnd)
save(OUT + r'\L3.png', w, h, rows)
print('L3 pale=%.2f red=%.2f' % sig(rows, w, h))

p.terminate()
time.sleep(0.5)
kill_all()
open(BRF, 'wb').write(open(BAK, 'rb').read())
print('已恢复原文')
