# -*- coding: utf-8 -*-
r"""
pgcam 列表渲染受控实验
======================
目标：判定"第4项描述坏掉"是长度问题、位置问题还是别的原因。

变体（每次改一处，其余不动）：
  V1  baseline          —— 现状
  V2  d15 缩短到 4 字    —— 第4项描述改短
  V3  d12 加长到 40 字   —— 第1项描述加长
  V4  rows 只留 3 条     —— 减少入口点数量
  V5  d15 英文 123 字符  —— 第4项描述用英文原文（123字符）

用法: python exp_cam_series.py V1 V2 V3 ...
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
CAM = r'D:\PGForever1.021\PG\Scenario\pg.pgcam'
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc'


def kill():
    subprocess.run(['taskkill', '/F', '/IM', 'PGForever.exe'], capture_output=True)
    time.sleep(0.7)


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


def grab(hwnd, out):
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
    from PIL import Image
    im = Image.open(out).crop((5, 118, 490, 500))
    im = im.resize((485 * 3, 382 * 3), Image.LANCZOS)
    im.save(out.replace('.png', '_zoom.png'))


def find_entry(lines, n):
    """找第 n 个入口点行（名称以 19 开头的数据行）"""
    cnt = 0
    for i, l in enumerate(lines):
        if l[:2] == '19' and '\t' in l and not l.startswith('#'):
            if cnt == n:
                return i
            cnt += 1
    return None


def make_variant(orig_text, name):
    lines = orig_text.split('\r\n')

    def find(prefix):
        for i, l in enumerate(lines):
            if l.startswith(prefix + '\t'):
                return i
        return None

    if name == 'V2':      # 第4项描述 -> 3字
        i = find_entry(lines, 3)
        if i is None: return None
        f = lines[i].split('\t'); f[2] = '守住所'
        return '第4项描述 -> "守住所"(3字)'
    if name == 'V3':      # 第1项描述 -> 40字
        i = find_entry(lines, 0)
        if i is None: return None
        return '第1项(1939)描述 -> 40个"德"'
    if name == 'V4':      # 只留前 3 条入口
        return '只保留前3条入口点(4/5条清空)'
    if name == 'V5':      # 第4项 -> 英文原文123字符
        i = find_entry(lines, 3)
        if i is None: return None
        return '第4项描述 -> 英文原文(123字符)'
    if name == 'V6':      # 第4项 -> 40个"德"
        i = find_entry(lines, 3)
        if i is None: return None
        return '第4项描述 -> 40个"德"(40字/120字节)'
    if name == 'V7':      # 第4项 -> 24个"德"
        i = find_entry(lines, 3)
        if i is None: return None
        return '第4项描述 -> 24个"德"(与现状等长)'
    return None


def run_one(name, orig_bytes):
    t = orig_bytes.decode('utf-16')
    desc = make_variant(t, name)
    if desc is None:
        print('未知变体', name); return
    lines = t.split('\r\n')

    if name == 'V2':
        i = find_entry(lines, 3); f = lines[i].split('\t'); f[2] = '守住所'; lines[i] = '\t'.join(f)
    elif name == 'V3':
        i = find_entry(lines, 0); f = lines[i].split('\t'); f[2] = '德' * 40; lines[i] = '\t'.join(f)
    elif name == 'V4':
        out = []; cnt = 0
        for l in lines:
            if l[:2] == '19' and '\t' in l and not l.startswith('#'):
                if cnt < 3:
                    out.append(l); cnt += 1
                else:
                    ff = l.split('\t'); out.append('\t'.join([ff[0]] + [''] * (len(ff) - 1)))
            else:
                out.append(l)
        lines = out
    elif name == 'V5':
        i = find_entry(lines, 3); f = lines[i].split('\t')
        f[2] = 'With most of her forces committed to the eastern front, the Axis must defend the soft underbelly of Europe from the Allies.'
        lines[i] = '\t'.join(f)
    elif name == 'V6':
        i = find_entry(lines, 3); f = lines[i].split('\t'); f[2] = '德' * 40; lines[i] = '\t'.join(f)
    elif name == 'V7':
        i = find_entry(lines, 3); f = lines[i].split('\t'); f[2] = '德' * 24; lines[i] = '\t'.join(f)

    payload = '\r\n'.join(lines)
    open(CAM, 'wb').write(b'\xff\xfe' + payload.encode('utf-16-le'))
    print('[%s] %s  (文件 %d 字节)' % (name, desc, os.path.getsize(CAM)))

    kill()
    p = None
    try:
        p = subprocess.Popen([GAME, '/game', 'pg'], cwd=os.path.dirname(GAME))
        hwnd = find_hwnd(p.pid)
        if not hwnd:
            print('  无窗口'); return
        time.sleep(6.0)
        out = os.path.join(OUT, 'cam_%s.png' % name)
        grab(hwnd, out)
        print('  截图 -> cam_%s_zoom.png' % name)
    finally:
        if p:
            try:
                p.terminate()
            except Exception:
                pass
        kill()


def main():
    orig = open(CAM, 'rb').read()
    names = sys.argv[1:] or ['V1', 'V7', 'V2', 'V3', 'V4', 'V6']
    try:
        for n in names:
            if n == 'V1':
                open(CAM, 'wb').write(orig)
                print('[V1] baseline 现状')
                kill()
                p = subprocess.Popen([GAME, '/game', 'pg'], cwd=os.path.dirname(GAME))
                hwnd = find_hwnd(p.pid)
                if hwnd:
                    time.sleep(6.0)
                    grab(hwnd, os.path.join(OUT, 'cam_V1.png'))
                    print('  截图 -> cam_V1_zoom.png')
                try:
                    p.terminate()
                except Exception:
                    pass
                kill()
            else:
                run_one(n, orig)
    finally:
        open(CAM, 'wb').write(orig)
        print('=== 已恢复原始 pgcam ===')


if __name__ == '__main__':
    main()
