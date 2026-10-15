# -*- coding: utf-8 -*-
r"""
pgbrf 中文显示实验 v3：强化焦点接管 + 逐步截图。
每次点击前用 AttachThreadInput 强制把游戏置为前台并校验，避免输入丢失。
"""
import ctypes
import os
import struct
import subprocess
import sys
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

ZH = ('<p>你在「白色方案」行动中的第一个任务——征服波兰——是在9月10日之前夺取库特诺与罗兹这两座关键城市。'
      '这样就能抢在法国与英国对德国发动进攻之前征服波兰。若能在9月10日之前达成这些目标，'
      '你可能会获得额外的兵力用于进攻华沙。</p>\r\n')


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
            user.ShowWindow(hwnd, 9)          # SW_RESTORE
            user.BringWindowToTop(hwnd)
            user.SetForegroundWindow(hwnd)
            user.SetFocus(hwnd)
            user.AttachThreadInput(cur, t1, False)
            user.AttachThreadInput(cur, t2, False)
        except Exception:
            pass
        time.sleep(0.4)
        if user.GetForegroundWindow() == hwnd:
            return True
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


def click(hwnd, lx, ly, wait=2.0):
    ok = force_focus(hwnd)
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    sx, sy = r.left + lx, r.top + ly
    user.SetCursorPos(sx, sy)
    time.sleep(0.3)
    pos = wintypes.POINT()
    user.GetCursorPos(ctypes.byref(pos))
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.12)
    user.mouse_event(0x0004, 0, 0, 0, 0)
    print('    click(%d,%d)->screen(%d,%d) cursor=(%d,%d) focus=%s'
          % (lx, ly, sx, sy, pos.x, pos.y, ok))
    time.sleep(wait)


def run(tag, data):
    open(BRF, 'wb').write(data)
    p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
    hwnd = find_hwnd(25)
    if not hwnd:
        print('[%s] 无窗口' % tag)
        return
    user.SetWindowPos(hwnd, -1, 710, 220, 500, 600, 0x0040)
    time.sleep(2.0)
    print('[%s] focus=%s' % (tag, force_focus(hwnd)))
    time.sleep(1.5)

    seq = [(200, 148), (200, 448), (245, 538), (245, 538), (245, 538)]
    for i, (x, y) in enumerate(seq):
        ox, oy, w, h, rows = grab(hwnd)
        save(os.path.join(OUTDIR, 'c_%s_%d.png' % (tag, i)), w, h, rows)
        print('  [%s] step%d 截图 c_%s_%d.png' % (tag, i, tag, i))
        click(hwnd, x, y)
    ox, oy, w, h, rows = grab(hwnd)
    save(os.path.join(OUTDIR, 'c_%s_9.png' % tag), w, h, rows)
    print('  [%s] 最终截图 c_%s_9.png' % (tag, tag))
    p.terminate()
    try:
        p.wait(timeout=6)
    except Exception:
        p.kill()
    time.sleep(1.0)


run('zh', ZH.encode('utf-8'))
open(BRF, 'wb').write(open(BAK, 'rb').read())
print('已恢复原文')
