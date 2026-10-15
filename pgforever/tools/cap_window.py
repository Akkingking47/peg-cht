# -*- coding: utf-8 -*-
r"""
对已在运行的 PGForever 主窗口用 PrintWindow(flags=2) 截图。

为什么不用屏幕 BitBlt：
    本机桌面浏览器会遮挡游戏窗口，屏幕抓取会拿到被遮挡的内容；
    PrintWindow 让窗口自己重绘到内存 DC，不受遮挡影响。
    也刻意不调用 SetForegroundWindow —— 本机该调用恒失败。

用法: python cap_window.py <输出png>
"""
import ctypes
import subprocess
import sys
import time
import zlib
import struct
from ctypes import wintypes

EXE = r'D:\PGForever1.021\PGForever.exe'
CWD = r'D:\PGForever1.021'
OUT = sys.argv[1] if len(sys.argv) > 1 else r'D:\DSH\军事游戏汉化\pgforever\poc\cap.png'
LAUNCH = '--no-launch' not in sys.argv

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

gdi = ctypes.windll.gdi32
user = ctypes.windll.user32
user.SetProcessDPIAware()


def pids_of(name):
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ' + name, '/FO', 'CSV', '/NH'],
                         capture_output=True).stdout.decode('mbcs', 'ignore')
    res = []
    for line in out.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) > 1 and parts[0].lower() == name.lower():
            try:
                res.append(int(parts[1]))
            except ValueError:
                pass
    return res


def find_window(pid=None):
    res = {}

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, lparam):
        if not user.IsWindowVisible(hwnd):
            return True
        n = user.GetWindowTextLengthW(hwnd) + 1
        buf = ctypes.create_unicode_buffer(n)
        user.GetWindowTextW(hwnd, buf, n)
        p = wintypes.DWORD()
        user.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if buf.value and (pid is None or p.value == pid):
            res['hwnd'] = hwnd
            res['title'] = buf.value
            res['pid'] = p.value
        return True

    user.EnumWindows(cb, 0)
    return res


def find_game_window():
    """枚举所有顶层窗口，用窗口标题/类名识别游戏窗口（不依赖 tasklist 输出编码）。"""
    res = {}

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, lparam):
        if not user.IsWindowVisible(hwnd):
            return True
        n = user.GetWindowTextLengthW(hwnd) + 1
        buf = ctypes.create_unicode_buffer(n)
        user.GetWindowTextW(hwnd, buf, n)
        cls = ctypes.create_unicode_buffer(256)
        user.GetClassNameW(hwnd, cls, 256)
        p = wintypes.DWORD()
        user.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if buf.value and ('PG Forever' in buf.value or buf.value == 'PG Forever'):
            res['hwnd'] = hwnd
            res['title'] = buf.value
            res['pid'] = p.value
            res['class'] = cls.value
            return False
        return True

    user.EnumWindows(cb, 0)
    return res


if LAUNCH and not find_game_window().get('hwnd'):
    subprocess.Popen([EXE, '/game', 'pg'], cwd=CWD)
    print('已启动，等待 9s ...')
    time.sleep(9)

info = find_game_window()
hwnd = info.get('hwnd')
print('窗口: hwnd=%s title=%r pid=%s' % (hwnd, info.get('title', ''), info.get('pid')))
if not hwnd:
    print('未找到游戏窗口')
    sys.exit(1)

r = wintypes.RECT()
user.GetClientRect(hwnd, ctypes.byref(r))
w, h = r.right - r.left, r.bottom - r.top
print('客户区 %dx%d' % (w, h))

hdc = user.GetDC(hwnd)
memdc = gdi.CreateCompatibleDC(hdc)
hbmp = gdi.CreateCompatibleBitmap(hdc, w, h)
gdi.SelectObject(memdc, hbmp)
ok = user.PrintWindow(hwnd, memdc, 2)
print('PrintWindow ->', ok)


class BMIH(ctypes.Structure):
    _fields_ = [('biSize', wintypes.DWORD), ('biWidth', ctypes.c_int),
                ('biHeight', ctypes.c_int), ('biPlanes', wintypes.WORD),
                ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', ctypes.c_int),
                ('biYPelsPerMeter', ctypes.c_int), ('biClrUsed', wintypes.DWORD),
                ('biClrImportant', wintypes.DWORD)]


class BMI(ctypes.Structure):
    _fields_ = [('bmiHeader', BMIH), ('bmiColors', wintypes.DWORD * 3)]


bi = BMI()
bi.bmiHeader.biSize = ctypes.sizeof(BMIH)
bi.bmiHeader.biWidth = w
bi.bmiHeader.biHeight = -h
bi.bmiHeader.biPlanes = 1
bi.bmiHeader.biBitCount = 32
bi.bmiHeader.biCompression = 0

buf = ctypes.create_string_buffer(w * h * 4)
gdi.GetDIBits(memdc, hbmp, 0, h, buf, ctypes.byref(bi), 0)
bgra = buf.raw


def png_write(path, w, h, bgra):
    """手写 PNG：BGRA -> RGB，每行 filter 0。"""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        row = bgra[y * w * 4:(y + 1) * w * 4]
        for x in range(w):
            b, g, r = row[x * 4], row[x * 4 + 1], row[x * 4 + 2]
            raw += bytes((r, g, b))

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    out = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + \
        chunk(b'IDAT', zlib.compress(bytes(raw), 6)) + chunk(b'IEND', b'')
    open(path, 'wb').write(out)


png_write(OUT, w, h, bgra)
print('已保存', OUT)

gdi.DeleteObject(hbmp)
gdi.DeleteDC(memdc)
user.ReleaseDC(hwnd, hdc)
