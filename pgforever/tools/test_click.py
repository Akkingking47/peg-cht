# -*- coding: utf-8 -*-
r"""
点击方式对比测试：mouse_event 注入 vs PostMessage 直投窗口消息。
用于判断游戏为何不响应合成点击。
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


def grab(x, y, w, h):
    hdc = user.GetDC(0)
    memdc = gdi.CreateCompatibleDC(hdc)
    hbmp = gdi.CreateCompatibleBitmap(hdc, w, h)
    gdi.SelectObject(memdc, hbmp)
    gdi.BitBlt(memdc, 0, 0, w, h, hdc, x, y, 0x00CC0020)

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
    return rows


def save_png(path, w, h, rows):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + r for r in rows)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
print('pid=%d' % p.pid)
hwnd = find_hwnd(25)
print('hwnd=%s' % hwnd)
user.SetWindowPos(hwnd, 0, 0, 0, 1400, 1000, 0x0040 | 0x0004)
r = wintypes.RECT()
user.GetWindowRect(hwnd, ctypes.byref(r))
W, H = r.right - r.left, r.bottom - r.top
print('rect %d,%d %dx%d' % (r.left, r.top, W, H))

# 定位金色按钮
rows = grab(r.left, r.top, W, H)
gold = []
y0 = int(H * 0.5)
rowc = [0] * H
col = [0] * W
for y in range(y0, H):
    line = rows[y]
    for x in range(W):
        rr, gg, bb = line[x*3], line[x*3+1], line[x*3+2]
        if rr > 150 and gg > 120 and bb < 130 and rr - bb > 60:
            rowc[y] += 1
            col[x] += 1
rowruns = []
cur = None
for y in range(y0, H):
    if rowc[y] > 3:
        cur = [y, y] if cur is None else [cur[0], y]
    else:
        if cur:
            rowruns.append(tuple(cur)); cur = None
if cur:
    rowruns.append(tuple(cur))
colruns = []
cur = None
for x in range(W):
    if col[x] > 2:
        cur = [x, x] if cur is None else [cur[0], x]
    else:
        if cur:
            colruns.append(tuple(cur)); cur = None
if cur:
    colruns.append(tuple(cur))
for (ya, yb) in rowruns:
    for (xa, xb) in colruns:
        if xb - xa > 8 and yb - ya > 4:
            gold.append(((xa + xb) // 2, (ya + yb) // 2))
gold.sort(key=lambda t: (t[1], t[0]))
print('金色按钮(窗口坐标): %s' % gold)

if not gold:
    raise SystemExit('未找到按钮')

bx, by = gold[0]
sx, sy = r.left + bx, r.top + by
print('目标按钮 窗口内(%d,%d) 屏幕(%d,%d)' % (bx, by, sx, sy))

pt = wintypes.POINT(bx, by)
tgt = user.WindowFromPoint(pt)          # 注意：这里是窗口坐标，用屏幕坐标才有意义
pts = wintypes.POINT(sx, sy)
tgt2 = user.WindowFromPoint(pts)
print('WindowFromPoint(窗口坐标)=%s   (屏幕坐标)=%s   本窗口=%s  相等=%s' % (tgt, tgt2, hwnd, tgt2 == hwnd))

# 方式 A: mouse_event
user.SetForegroundWindow(hwnd)
time.sleep(0.8)
print('foreground=%s（本窗口=%s）' % (user.GetForegroundWindow(), hwnd))
user.SetCursorPos(sx, sy)
time.sleep(0.3)
cur = wintypes.POINT(); user.GetCursorPos(ctypes.byref(cur))
print('光标实际位置 (%d,%d)' % (cur.x, cur.y))
user.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.12)
user.mouse_event(0x0004, 0, 0, 0, 0)
time.sleep(2.0)
rows2 = grab(r.left, r.top, W, H)
save_png(r'D:\DSH\军事游戏汉化\pgforever\poc\cmp_A_mouseevent.png', W, H, rows2)
print('方式A(mouse_event) 截图完成, 画面是否变化=%s' % (rows2 != rows))

# 方式 B: PostMessage 直投
cx = wintypes.POINT(bx, by)
user.ScreenToClient(hwnd, ctypes.byref(cx))
lp = (cx.y << 16) | (cx.x & 0xFFFF)
user.PostMessageW(hwnd, 0x0200, 0, lp)              # WM_MOUSEMOVE
time.sleep(0.2)
user.PostMessageW(hwnd, 0x0201, 1, lp)              # WM_LBUTTONDOWN (MK_LBUTTON)
time.sleep(0.12)
user.PostMessageW(hwnd, 0x0202, 0, lp)              # WM_LBUTTONUP
time.sleep(2.0)
rows3 = grab(r.left, r.top, W, H)
save_png(r'D:\DSH\军事游戏汉化\pgforever\poc\cmp_B_postmessage.png', W, H, rows3)
print('方式B(PostMessage) 截图完成, 画面是否变化=%s (客户端坐标 %d,%d)' % (rows3 != rows, cx.x, cx.y))
print('alive=%s' % (p.poll() is None))
