# -*- coding: utf-8 -*-
r"""
最终验证：主菜单列表（pgcam 中文）+ 战役简报（pgbrf 中文）。
多轮尝试点击推进，用像素特征自动识别界面，PrintWindow 抓图（不受遮挡影响）。
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


def feats(rows, w, h):
    pale = red = tot = 0
    for y in range(int(h*0.18), int(h*0.78), 2):
        line = rows[y]
        for x in range(int(w*0.08), int(w*0.92), 2):
            r, g, b = line[x*3], line[x*3+1], line[x*3+2]
            tot += 1
            if r > 200 and g > 180 and b > 130:
                pale += 1
            if 90 < r < 200 and g < 70 and b < 80:
                red += 1
    return pale / tot, red / tot


def click(hwnd, lx, ly, wait=2.4):
    user.SetForegroundWindow(hwnd)
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    # 补偿合成鼠标的坐标偏差：设置后回读，偏差则二次校正
    for _ in range(2):
        user.SetCursorPos(r.left + lx, r.top + ly)
        time.sleep(0.3)
        p = wintypes.POINT()
        user.GetCursorPos(ctypes.byref(p))
        if abs(p.x - (r.left + lx)) <= 1 and abs(p.y - (r.top + ly)) <= 1:
            break
        user.SetCursorPos(2*(r.left + lx) - p.x, 2*(r.top + ly) - p.y)
        time.sleep(0.3)
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.12)
    user.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(wait)


kill_all()
p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
hwnd = find_hwnd(p.pid)
print('hwnd=%s' % hwnd)
user.SetWindowPos(hwnd, -1, 710, 220, 500, 600, 0x0040)
time.sleep(2.5)
user.SetForegroundWindow(hwnd)
time.sleep(1.5)

w, h, rows = capture(hwnd)
pale, red = feats(rows, w, h)
save(OUT + r'\F0_menu.png', w, h, rows)
print('F0 菜单 pale=%.2f red=%.2f' % (pale, red))

# 进入：选列表项 -> 开始；若出现 options 则点确定
for step in range(1, 7):
    click(hwnd, 200, 148)
    click(hwnd, 245, 538, 2.6)
    w, h, rows = capture(hwnd)
    pale, red = feats(rows, w, h)
    fn = OUT + r'\F%d.png' % step
    save(fn, w, h, rows)
    print('F%d pale=%.2f red=%.2f' % (step, pale, red))
    if pale > 0.3:
        print('  -> 判定到达简报界面（F%d.png）' % step)
        break
    # 可能是 options 对话框：点「确定」后继续
    click(hwnd, 200, 448, 2.0)

p.terminate()
time.sleep(0.5)
kill_all()
print('done')
