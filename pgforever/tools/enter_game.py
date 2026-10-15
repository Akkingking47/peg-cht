# -*- coding: utf-8 -*-
r"""
进入游戏内的验证脚本：
关键改进——每次操作前把游戏窗口强制置前并校验焦点，避免输入丢失。
流程：菜单(开始!) -> 场景列表(开始!) -> 进入场景 -> 截图（简报/部署）
      -> 按 P 打开征募(验证 equipment.pgeqp 单位名)
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


def focus(hwnd):
    """强制把游戏置前并置顶"""
    user.ShowWindow(hwnd, 3)
    user.BringWindowToTop(hwnd)
    try:
        user.SetWindowPos(hwnd, -1, 0, 0, 1200, 800, 0x0040)   # HWND_TOPMOST
        user.SetWindowPos(hwnd, -2, 0, 0, 1200, 800, 0x0040)   # 取消 TOPMOST 但保持置顶
    except Exception:
        pass
    user.SetForegroundWindow(hwnd)
    fg = user.GetWindowThreadProcessId(user.GetForegroundWindow(), None)
    tid = user.GetWindowThreadProcessId(hwnd, None)
    cur = ctypes.windll.kernel32.GetCurrentThreadId()
    user.AttachThreadInput(cur, tid, True)
    user.SetForegroundWindow(hwnd)
    user.AttachThreadInput(cur, tid, False)
    time.sleep(0.5)
    return user.GetForegroundWindow() == hwnd


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


def gold(hwnd):
    ox, oy, w, h, rows = grab(hwnd)
    col = [0] * w
    rowc = [0] * h
    for y in range(int(h * 0.5), h):
        line = rows[y]
        for x in range(w):
            a, b_, c = line[x*3], line[x*3+1], line[x*3+2]
            if a > 150 and b_ > 120 and c < 130 and a - c > 60:
                col[x] += 1
                rowc[y] += 1
    rr = []
    cur = None
    for y in range(int(h * 0.5), h):
        if rowc[y] > 3:
            cur = [y, y] if cur is None else [cur[0], y]
        else:
            if cur:
                rr.append(tuple(cur)); cur = None
    if cur:
        rr.append(tuple(cur))
    cc = []
    cur = None
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
    return ox, oy, out


def click(hwnd, sx, sy):
    ok = focus(hwnd)
    user.SetCursorPos(int(sx), int(sy))
    time.sleep(0.4)
    cur = wintypes.POINT()
    user.GetCursorPos(ctypes.byref(cur))
    print('   click (%d,%d) focus=%s cursor=(%d,%d)' % (sx, sy, ok, cur.x, cur.y))
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.12)
    user.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(1.8)


def key(hwnd, vk, wait=2.0):
    ok = focus(hwnd)
    print('   key vk=%s focus=%s' % (vk, ok))
    user.keybd_event(vk, 0, 0, 0)
    time.sleep(0.08)
    user.keybd_event(vk, 0, 2, 0)
    time.sleep(wait)


p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
hwnd = find_hwnd(25)
print('hwnd=%s' % hwnd)
if not hwnd:
    raise SystemExit('no window')
print('focus ok:', focus(hwnd))
time.sleep(2.5)

for step in range(1, 5):
    ox, oy, btns = gold(hwnd)
    print('step %d: 金色按钮 %s' % (step, btns[:4]))
    if not btns:
        print('   未找到按钮，改用 Enter')
        key(hwnd, 0x0D, 2.5)
    else:
        click(hwnd, ox + btns[0][0], oy + btns[0][1])
    ox, oy, w, h, rows = grab(hwnd)
    save(os.path.join(OUTDIR, 'g%d.png' % step), w, h, rows)
    print('   已截图 g%d.png' % step)

# 尝试打开征募界面（P 键）
key(hwnd, 0x50, 2.5)
ox, oy, w, h, rows = grab(hwnd)
save(os.path.join(OUTDIR, 'g9_purchase.png'), w, h, rows)
print('done, alive=%s' % (p.poll() is None))
