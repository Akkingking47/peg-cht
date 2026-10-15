# -*- coding: utf-8 -*-
r"""
闭合环点击：点击后立即检测画面是否变化；无变化则换候选点重试。
用于绕过合成鼠标的坐标偏差，可靠地关闭 options 对话框并推进到简报。
同时在简报界面定位中文截断点（测试文本带 [20][40][60]… 标记）。
"""
import ctypes
import os
import struct
import subprocess
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
parts = []
for i in range(1, 8):
    parts.append(CHUNK)
    parts.append('[%d]' % (i * 20))
ZH = '<p>' + ''.join(parts) + '</p>\r\n'


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


def diff_ratio(a, b):
    n = min(len(a), len(b))
    d = 0
    for i in range(0, n, 7):
        if a[i] != b[i]:
            d += 1
    return d / (n / 7)


def click_raw(hwnd, lx, ly):
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    tgt = (r.left + lx, r.top + ly)
    for _ in range(3):
        user.SetCursorPos(*tgt)
        time.sleep(0.25)
        p = wintypes.POINT()
        user.GetCursorPos(ctypes.byref(p))
        if abs(p.x - tgt[0]) <= 1 and abs(p.y - tgt[1]) <= 1:
            break
        tgt = (tgt[0] + (tgt[0] - p.x), tgt[1] + (tgt[1] - p.y))   # 补偿偏差
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.12)
    user.mouse_event(0x0004, 0, 0, 0, 0)


def click_until_change(hwnd, points, label, wait=2.0):
    _, _, _, _, before = grab(hwnd)
    for (x, y) in points:
        force_focus(hwnd)
        click_raw(hwnd, x, y)
        time.sleep(wait)
        _, _, _, _, after = grab(hwnd)
        d = diff_ratio(before, after)
        print('    %s 点(%d,%d) 画面变化=%.3f' % (label, x, y, d))
        if d > 0.01:
            return True, after
    return False, before


open(BRF, 'wb').write(ZH.encode('utf-8'))
p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
hwnd = find_hwnd(25)
print('hwnd=%s focus=%s' % (hwnd, force_focus(hwnd) if hwnd else None))
user.SetWindowPos(hwnd, -1, 710, 220, 500, 600, 0x0040)
time.sleep(2.5)
force_focus(hwnd)
time.sleep(1.0)

# 1) 选中列表第一项 -> 弹出 options
ok, _ = click_until_change(hwnd, [(200, 148), (200, 140), (200, 158)], '选列表项')
# 2) 关闭 options（确定按钮附近多候选点）
ok2, _ = click_until_change(hwnd, [(200, 448), (200, 445), (195, 450), (210, 448), (185, 448)], '关对话框')
# 3) 开始 -> 简报
ok3, _ = click_until_change(hwnd, [(245, 538), (245, 540), (240, 538)], '开始')

ox, oy, w, h, rows = grab(hwnd)
save(os.path.join(OUTDIR, 'cut_final.png'), w, h, rows)
print('最终截图 cut_final.png  步骤成功: %s %s %s' % (ok, ok2, ok3))

p.terminate()
try:
    p.wait(timeout=6)
except Exception:
    p.kill()
open(BRF, 'wb').write(open(BAK, 'rb').read())
print('已恢复原文')
