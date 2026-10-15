# -*- coding: utf-8 -*-
r"""
pgbrf（战役简报）中文显示实验。
简报是 HTML 片段（<p>..</p>），由 HTMLayout 渲染。
分别测试 UTF-8 无 BOM / UTF-8 with BOM 两种写法，看中文能否正常显示。
流程：选中列表第一项 -> 「开始!」 -> 简报界面 -> 截图
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


def click(hwnd, lx, ly, wait=1.8):
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    user.SetCursorPos(r.left + lx, r.top + ly)
    time.sleep(0.3)
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.12)
    user.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(wait)


def run(tag, data):
    open(BRF, 'wb').write(data)
    p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
    hwnd = find_hwnd(25)
    if not hwnd:
        print('[%s] 无窗口' % tag)
        return
    user.SetWindowPos(hwnd, -1, 710, 220, 500, 600, 0x0040)
    user.SetForegroundWindow(hwnd)
    time.sleep(2.5)
    click(hwnd, 200, 148)          # 选列表第一项
    click(hwnd, 245, 538, 2.5)     # 开始 -> 简报
    ox, oy, w, h, rows = grab(hwnd)
    save(os.path.join(OUTDIR, 'brf_%s.png' % tag), w, h, rows)
    print('[%s] 已截图 brf_%s.png' % (tag, tag))
    p.terminate()
    try:
        p.wait(timeout=6)
    except Exception:
        p.kill()
    time.sleep(1.0)


run('utf8', ZH.encode('utf-8'))
run('utf8bom', b'\xef\xbb\xbf' + ZH.encode('utf-8'))
# 恢复原文
open(BRF, 'wb').write(open(BAK, 'rb').read())
print('已恢复 0001.pgbrf 原文')
