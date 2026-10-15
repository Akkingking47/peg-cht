# -*- coding: utf-8 -*-
r"""
pgcam 描述长度实验
==================
假设：战役列表第 4 项(1943 West)描述失败，是因为其"原文"长度(123 字符)超限。
实验：把该行描述替换为不同长度的内容，观察哪些能正常显示。
      为了让实验对照清晰，所有变体统一用 <中文> + 长度标记 的形式。

用法：python exp_pgcam_len.py <变体编号>
"""
import ctypes
import ctypes as _ct
import os
import struct
import subprocess
import sys
import time
import zlib
from ctypes import wintypes

k32 = ctypes.windll.kernel32
user = ctypes.windll.user32
gdi = ctypes.windll.gdi32
user.SetProcessDPIAware()

GAME = r'D:\PGForever1.021\PGForever.exe'
CAM = r'D:\PGForever1.021\Default\Scenario\pg.pgcam'
BK = r'D:\DSH\军事游戏汉化\pgforever\backup\Default_Scenario_pg.pgcam.orig'
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc'


def kill():
    subprocess.run(['taskkill', '/F', '/IM', 'PGForever.exe'], capture_output=True)
    time.sleep(0.8)


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
        time.sleep(0.3)
    return None


def grab(hwnd, out, x0, y0, x1, y1, scale=3):
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = user.GetWindowDC(hwnd)
    memdc = gdi.CreateCompatibleDC(hdc)
    hbmp = gdi.CreateCompatibleBitmap(hdc, w, h)
    gdi.SelectObject(memdc, hbmp)
    user.PrintWindow(hwnd, memdc, 2)

    class BIH(ctypes.Structure):
        _fields_ = [('biSize', wintypes.DWORD), ('biWidth', _ct.c_int), ('biHeight', _ct.c_int),
                    ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD),
                    ('biCompression', wintypes.DWORD), ('biSizeImage', wintypes.DWORD),
                    ('biXPelsPerMeter', _ct.c_int), ('biYPelsPerMeter', _ct.c_int),
                    ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)]
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
            line[i * 3], line[i * 3 + 1], line[i * 3 + 2] = px[i * 4 + 2], px[i * 4 + 1], px[i * 4]
        rows.append(bytes(line))
    gdi.DeleteObject(hbmp); gdi.DeleteDC(memdc); user.ReleaseDC(hwnd, hdc)

    def ch(tag, d):
        return struct.pack('>I', len(d)) + tag + d + struct.pack('>I', zlib.crc32(tag + d) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + x for x in rows)
    with open(out, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                + ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))
    # 顺带裁剪
    from PIL import Image
    im = Image.open(out).crop((x0, y0, x1, y1))
    im = im.resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.LANCZOS)
    im.save(out.replace('.png', '_crop.png'))


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else 'A'
    orig = open(CAM, 'rb').read()
    # 备份一次
    if not os.path.exists(BK):
        os.makedirs(os.path.dirname(BK), exist_ok=True)
        open(BK, 'wb').write(orig)
        print('已备份 -> %s' % BK)

    t = orig.decode('utf-16')
    # 找到 1943 West 行
    lines = t.split('\r\n')
    idx = None
    for i, l in enumerate(lines):
        if l.startswith('1943 West\t'):
            idx = i
            break
    assert idx is not None, '未找到 1943 West 行'
    old = lines[idx]
    f = old.split('\t')

    # 变体：不同长度的中文描述 + 数字标记
    variants = {
        'A':  ('这是一段五十字的中文描述用于测试长度阈值看看会不会被截断掉啊', 30),
        'B':  ('这是一段中文描述测试长度阈值', 14),
        'C':  ('中' * 60, 60),
        'D':  ('中' * 90, 90),
        'E':  ('中' * 120, 120),
        'F':  ('A' * 60, 60),
        'G':  ('A' * 123, 123),
    }
    newdesc, n = variants[variant]
    f[2] = newdesc
    lines[idx] = '\t'.join(f)
    print('变体 %s: 长度目录=%d 实际=%d' % (variant, n, len(newdesc)))
    result = '\r\n'.join(lines)
    open(CAM, 'wb').write(b'\xff\xfe' + result.encode('utf-16-le'))
    print('已写入, 新文件 %d 字节' % os.path.getsize(CAM))

    kill()
    try:
        p = subprocess.Popen([GAME, '/game', 'pg'], cwd=os.path.dirname(GAME))
        hwnd = find_hwnd(p.pid)
        if not hwnd:
            print('无窗口'); return
        time.sleep(6.0)
        out = os.path.join(OUT, 'cam_%s.png' % variant)
        grab(hwnd, out, 5, 120, 480, 480)
        print('截图 ->', out)
    finally:
        try:
            p.terminate()
        except Exception:
            pass
        kill()
        open(CAM, 'wb').write(orig)
        print('已恢复 pgcam')


if __name__ == '__main__':
    main()
