# -*- coding: utf-8 -*-
r"""
进入战斗并验证地形格信息渲染（PostMessage 合成点击）。

用户实机截图显示地块信息为 7 个方框 + (2,12)，根因是 MAPNAMES.STR 写成了 GBK
而该进程 CP_ACP=UTF-8 → 无效序列 → 替换字形。本脚本改为 UTF-8 后，进入一局
战役，检查 HoverHexInfo 是否渲染出中文地形名。

用法: python verify_terrain_ingame.py [输出png]
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
OUT = sys.argv[1] if len(sys.argv) > 1 else r'D:\DSH\军事游戏汉化\pgforever\poc\terrain_ingame.png'

WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0201, 0x0202
WM_MOUSEMOVE = 0x0200


class PE(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('c', wt.DWORD), ('pid', wt.DWORD),
                ('h', ctypes.c_void_p), ('m', wt.DWORD), ('t', wt.DWORD),
                ('pp', wt.DWORD), ('pr', ctypes.c_long), ('f', wt.DWORD),
                ('exe', ctypes.c_char * 260)]


def find_pid(name):
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)
    e = PE()
    e.dwSize = ctypes.sizeof(PE)
    ok = k32.Process32First(snap, ctypes.byref(e))
    while ok:
        if e.exe.decode('mbcs', 'ignore').lower() == name.lower():
            k32.CloseHandle(snap)
            return e.pid
        ok = k32.Process32Next(snap, ctypes.byref(e))
    k32.CloseHandle(snap)
    return None


def find_hwnd(title):
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


def click(hwnd, x, y, pause=1.2):
    lp = (y << 16) | x
    u32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    time.sleep(0.15)
    u32.PostMessageW(hwnd, WM_LBUTTONDOWN, 1, lp)
    time.sleep(0.08)
    u32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
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
    hwnd = find_hwnd('PG Forever')
    if not hwnd:
        print('未找到窗口')
        p.terminate()
        return
    r = wt.RECT()
    u32.GetClientRect(hwnd, ctypes.byref(r))
    print('窗口 %dx%d  hwnd=%s' % (r.right, r.bottom, hwnd))

    # 游戏选择界面：点左上「Panzer General」徽章（相对比例换算）
    sx, sy = r.right / 470.0, r.bottom / 595.0
    print('步骤1: 点击 Panzer General 徽章')
    click(hwnd, int(120 * sx), int(150 * sy), 2.0)
    shot(hwnd, OUT.replace('.png', '_s1.png'))

    # 战役列表 -> 开始
    print('步骤2: 点击 开始')
    click(hwnd, int(235 * sx), int(520 * sy), 2.5)
    shot(hwnd, OUT.replace('.png', '_s2.png'))

    print('步骤3: 点击第一个战役条目')
    click(hwnd, int(235 * sx), int(215 * sy), 2.5)
    shot(hwnd, OUT.replace('.png', '_s3.png'))

    time.sleep(2)
    shot(hwnd, OUT)
    print('存活:', find_pid('PGForever.exe') is not None)
    p.terminate()


main()
