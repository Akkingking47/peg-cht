# -*- coding: utf-8 -*-
r"""
把游戏窗口设为 TOPMOST 后点击（解决被桌面浏览器遮挡导致点击打偏的问题），
进入场景后按 P 打开征募界面，验证 equipment.pgeqp 的中文显示。
结束时取消 TOPMOST。
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
user.SetProcessDPIAware()
OUTDIR = r'D:\DSH\军事游戏汉化\pgforever\poc'
HWND_TOPMOST, HWND_NOTOPMOST = -1, -2
SWP_SHOWWINDOW = 0x0040


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


def gold_buttons(hwnd):
    ox, oy, w, h, rows = grab(hwnd)
    col = [0] * w
    rowc = [0] * h
    for y in range(int(h * 0.45), h):
        line = rows[y]
        for x in range(w):
            a, b_, c = line[x*3], line[x*3+1], line[x*3+2]
            if a > 150 and b_ > 120 and c < 130 and a - c > 60:
                col[x] += 1
                rowc[y] += 1
    rr, cur = [], None
    for y in range(int(h * 0.45), h):
        if rowc[y] > 3:
            cur = [y, y] if cur is None else [cur[0], y]
        else:
            if cur:
                rr.append(tuple(cur)); cur = None
    if cur:
        rr.append(tuple(cur))
    cc, cur = [], None
    for x in range(w):
        if col[x] > 2:
            cur = [x, x] if cur is None else [cur[0], x]
        else:
            if cur:
                cc.append(tuple(cur)); cur = None
    if cur:
        cc.append(tuple(cur))
    out = []
    for (ya, yb) in rr:
        if yb - ya < 4:
            continue
        for (xa, xb) in cc:
            if xb - xa > 8:
                out.append(((xa + xb) // 2, (ya + yb) // 2))
    out.sort(key=lambda t: (t[1], t[0]))
    return ox, oy, w, h, out


def click(sx, sy):
    user.SetCursorPos(int(sx), int(sy))
    time.sleep(0.35)
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.12)
    user.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(2.0)


p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
hwnd = find_hwnd(25)
print('hwnd=%s' % hwnd)
user.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 1400, 1050, SWP_SHOWWINDOW)
time.sleep(1.5)
cur_fg = user.GetForegroundWindow()
print('topmost 设置后 fg==game: %s' % (cur_fg == hwnd))

for step in range(1, 6):
    ox, oy, w, h, btns = gold_buttons(hwnd)
    print('step%d 窗口(%d,%d %dx%d) 按钮=%s' % (step, ox, oy, w, h, btns[:3]))
    if step == 5:
        # 尝试 P 键打开征募
        user.keybd_event(0x50, 0, 0, 0)
        time.sleep(0.08)
        user.keybd_event(0x50, 0, 2, 0)
        time.sleep(2.5)
    elif btns:
        click(ox + btns[0][0], oy + btns[0][1])
    else:
        user.keybd_event(0x0D, 0, 0, 0)
        time.sleep(0.08)
        user.keybd_event(0x0D, 0, 2, 0)
        time.sleep(2.5)
    _, _, w2, h2, rows = grab(hwnd)
    save(os.path.join(OUTDIR, 't%d.png' % step), w2, h2, rows)
    print('  -> t%d.png' % step)

user.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 1400, 1050, SWP_SHOWWINDOW)
print('已取消 TOPMOST，alive=%s' % (p.poll() is None))
