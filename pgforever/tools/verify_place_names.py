# -*- coding: utf-8 -*-
r"""
进入战役 -> 战场地图，验证「地名（MAPNAMES.STR 记录 14+）」的实际渲染。
复用 verify_terrain_ingame.py 的 PostMessage + PrintWindow 手法。

用法: python verify_place_names.py [出图前缀]
"""
import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
import time
import zlib
import struct

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
u32 = ctypes.WinDLL('user32', use_last_error=True)
g32 = ctypes.WinDLL('gdi32', use_last_error=True)

EXE = r'D:\PGForever1.021\PGForever.exe'
CWD = r'D:\PGForever1.021'
PRE = sys.argv[1] if len(sys.argv) > 1 else r'D:\DSH\军事游戏汉化\pgforever\poc\place'

WM_LBUTTONDOWN, WM_LBUTTONUP, WM_MOUSEMOVE = 0x0201, 0x0202, 0x0200


class PE(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('c', wt.DWORD), ('pid', wt.DWORD),
                ('h', ctypes.c_void_p), ('m', wt.DWORD), ('t', wt.DWORD),
                ('pp', wt.DWORD), ('pr', ctypes.c_long), ('f', wt.DWORD),
                ('exe', ctypes.c_char * 260)]


def find_hwnd(title='PG Forever'):
    res = {}

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def cb(hwnd, lp):
        n = u32.GetWindowTextLengthW(hwnd) + 1
        b = ctypes.create_unicode_buffer(n)
        u32.GetWindowTextW(hwnd, b, n)
        if b.value == title:
            res['h'] = hwnd
            return False
        return True

    u32.EnumWindows(cb, 0)
    return res.get('h')


def click(hwnd, x, y, pause=1.5):
    lp = (y << 16) | x
    u32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    time.sleep(0.15)
    u32.PostMessageW(hwnd, WM_LBUTTONDOWN, 1, lp)
    time.sleep(0.08)
    u32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    time.sleep(pause)


def move(hwnd, x, y, pause=1.0):
    u32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, (y << 16) | x)
    time.sleep(pause)


def shot(hwnd, out):
    r = wt.RECT()
    u32.GetClientRect(hwnd, ctypes.byref(r))
    w, h = r.right, r.bottom
    hdc = u32.GetDC(hwnd)
    memdc = g32.CreateCompatibleDC(hdc)
    bmp = g32.CreateCompatibleBitmap(hdc, w, h)
    g32.SelectObject(memdc, bmp)
    u32.PrintWindow(hwnd, memdc, 2)

    class BMIH(ctypes.Structure):
        _fields_ = [('biSize', wt.DWORD), ('biWidth', ctypes.c_int), ('biHeight', ctypes.c_int),
                    ('biPlanes', wt.WORD), ('biBitCount', wt.WORD), ('biCompression', wt.DWORD),
                    ('biSizeImage', wt.DWORD), ('biXPelsPerMeter', ctypes.c_int),
                    ('biYPelsPerMeter', ctypes.c_int), ('biClrUsed', wt.DWORD),
                    ('biClrImportant', wt.DWORD)]

    class BMI(ctypes.Structure):
        _fields_ = [('bmiHeader', BMIH), ('bmiColors', wt.DWORD * 3)]

    bi = BMI()
    bi.bmiHeader.biSize = ctypes.sizeof(BMIH)
    bi.bmiHeader.biWidth = w
    bi.bmiHeader.biHeight = -h
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 32
    buf = ctypes.create_string_buffer(w * h * 4)
    g32.GetDIBits(memdc, bmp, 0, h, buf, ctypes.byref(bi), 0)

    raw = bytearray()
    for y in range(h):
        raw.append(0)
        row = buf.raw[y * w * 4:(y + 1) * w * 4]
        for x in range(w):
            raw += bytes((row[x * 4 + 2], row[x * 4 + 1], row[x * 4]))

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + \
            struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

    open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' +
                          chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) +
                          chunk(b'IDAT', zlib.compress(bytes(raw), 6)) + chunk(b'IEND', b''))
    g32.DeleteObject(bmp)
    g32.DeleteDC(memdc)
    u32.ReleaseDC(hwnd, hdc)
    print('  截图 ->', out)


def main():
    p = subprocess.Popen([EXE, '/game', 'pg'], cwd=CWD)
    time.sleep(9)
    hwnd = find_hwnd()
    if not hwnd:
        print('未找到窗口')
        p.terminate()
        return
    r = wt.RECT()
    u32.GetClientRect(hwnd, ctypes.byref(r))
    sx, sy = r.right / 470.0, r.bottom / 595.0
    print('窗口 %dx%d' % (r.right, r.bottom))

    print('步骤1: Panzer General')
    click(hwnd, int(120 * sx), int(150 * sy), 2.0)

    print('步骤2: 开始')
    click(hwnd, int(235 * sx), int(520 * sy), 2.5)

    print('步骤3: 第一个战役')
    click(hwnd, int(235 * sx), int(215 * sy), 2.5)
    shot(hwnd, PRE + '_campaign.png')

    print('步骤4: 选场景/继续')
    click(hwnd, int(235 * sx), int(430 * sy), 3.0)
    shot(hwnd, PRE + '_s4.png')

    print('步骤5: 点画面中央进入')
    click(hwnd, int(235 * sx), int(300 * sy), 3.0)
    shot(hwnd, PRE + '_s5.png')

    print('步骤6: 悬停地图格（触发格信息）')
    for i, (mx, my) in enumerate([(250, 300), (300, 350), (200, 280), (350, 250)]):
        move(hwnd, int(mx * sx), int(my * sy), 1.2)
        shot(hwnd, '%s_hover%d.png' % (PRE, i + 1))

    time.sleep(1)
    shot(hwnd, PRE + '_final.png')
    p.terminate()


main()
