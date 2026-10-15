# -*- coding: utf-8 -*-
r"""
界面巡览 v2：启动 -> 固定窗口位置与尺寸 -> 每步截图 -> 自动定位金色按钮并点击。
关键改进：不再硬编码按钮坐标，而是在当前截图里按像素找按钮，再换算成屏幕坐标点击。
必须单进程跑完（游戏会随宿主 shell 结束而退出）。

步骤元素:
  ('shot', 名字)
  ('gold', 序号[, 区域])   点击金色按钮（在窗口下半部寻找，按 y 排序取第 n 个）
  ('key', 虚拟键码)
  ('wait', 秒)
  ('move', x, y)           窗口内相对坐标移动
"""
import ctypes
import struct
import subprocess
import sys
import time
import zlib
from ctypes import wintypes

user = ctypes.windll.user32
gdi = ctypes.windll.gdi32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass
user.SetProcessDPIAware()

EXE = r'D:\PGForever1.021\PGForever.exe'
CWD = r'D:\PGForever1.021'
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


def grab(x, y, w, h):
    """截取屏幕区域，返回 (w,h,rows) 其中每行是 RGB bytes"""
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
            line[i*3] = px[i*4+2]
            line[i*3+1] = px[i*4+1]
            line[i*3+2] = px[i*4]
        rows.append(bytes(line))
    gdi.DeleteObject(hbmp)
    gdi.DeleteDC(memdc)
    user.ReleaseDC(0, hdc)
    return w, h, rows


def save_png(path, w, h, rows):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + r for r in rows)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b'')
    open(path, 'wb').write(png)


def win_shot(hwnd, name):
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    w2, h2, rows = grab(r.left, r.top, w, h)
    path = '%s\\w2_%s.png' % (OUTDIR, name)
    save_png(path, w2, h2, rows)
    print('  [shot] %s %dx%d @ (%d,%d)' % (name, w2, h2, r.left, r.top))
    return r.left, r.top, w2, h2, rows


def gold_buttons(rows, w, h, frac_top=0.5):
    """在图像下半部找金色矩形按钮，返回按 y 排序的中心点列表"""
    def is_gold(r, g, b):
        return r > 150 and g > 120 and b < 130 and r - b > 60

    y0 = int(h * frac_top)
    col = [0] * w
    rowc = [0] * h
    for y in range(y0, h):
        line = rows[y]
        for x in range(w):
            r, g, b = line[x*3], line[x*3+1], line[x*3+2]
            if is_gold(r, g, b):
                col[x] += 1
                rowc[y] += 1
    # 行分段
    rowruns = []
    cur = None
    for y in range(y0, h):
        if rowc[y] > 3:
            cur = [y, y] if cur is None else [cur[0], y]
        else:
            if cur:
                rowruns.append(tuple(cur))
                cur = None
    if cur:
        rowruns.append(tuple(cur))
    # 列分段
    colruns = []
    cur = None
    for x in range(w):
        if col[x] > 2:
            cur = [x, x] if cur is None else [cur[0], x]
        else:
            if cur:
                colruns.append(tuple(cur))
                cur = None
    if cur:
        colruns.append(tuple(cur))
    out = []
    for (ya, yb) in rowruns:
        if yb - ya < 4:
            continue
        for (xa, xb) in colruns:
            if xb - xa < 8:
                continue
            out.append(((xa + xb) // 2, (ya + yb) // 2, xb - xa, yb - ya))
    out.sort(key=lambda t: (t[1], t[0]))
    return out


def click_at(sx, sy):
    user.SetCursorPos(int(sx), int(sy))
    time.sleep(0.25)
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.1)
    user.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.15)


STEPS = [
    ('wait', 1.5),
    ('shot', 'menu'),
]


def main():
    game = sys.argv[1] if len(sys.argv) > 1 else 'pg'
    outtag = sys.argv[2] if len(sys.argv) > 2 else 'menu'
    p = subprocess.Popen([EXE, '/game', game], cwd=CWD)
    print('launched pid=%d game=%s' % (p.pid, game))
    hwnd = find_hwnd(25)
    if not hwnd:
        print('!! 未找到游戏窗口')
        return
    user.SetWindowPos(hwnd, 0, 0, 0, 1400, 1000, 0x0040 | 0x0004)   # SWP_SHOWWINDOW | SWP_NOZORDER
    user.SetForegroundWindow(hwnd)
    time.sleep(1.5)
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    print('hwnd=%s rect %d,%d %dx%d' % (hwnd, r.left, r.top, r.right - r.left, r.bottom - r.top))

    for st in STEPS:
        kind = st[0]
        if kind == 'shot':
            win_shot(hwnd, st[1])
        elif kind == 'wait':
            time.sleep(st[1])
        elif kind == 'key':
            user.keybd_event(st[1], 0, 0, 0)
            time.sleep(0.06)
            user.keybd_event(st[1], 0, 2, 0)
            print('  [key] vk=%s' % st[1])
            time.sleep(st[2] if len(st) > 2 else 0.8)
        elif kind == 'gold':
            ox, oy, w, h, rows = win_shot(hwnd, 'before_gold%d' % st[1])
            btns = gold_buttons(rows, w, h)
            print('  [gold] 找到 %d 个金色按钮: %s' % (len(btns), [(b[0], b[1]) for b in btns][:6]))
            idx = st[1]
            if idx < len(btns):
                cx, cy = btns[idx][0], btns[idx][1]
                click_at(ox + cx, oy + cy)
                print('  [gold] 点击第 %d 个 -> 屏幕 (%d,%d)' % (idx, ox + cx, oy + cy))
                time.sleep(st[2] if len(st) > 2 else 1.5)
            else:
                print('  [gold] 序号越界，跳过')
    print('alive=%s' % (p.poll() is None))


main()
