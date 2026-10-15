# -*- coding: utf-8 -*-
r"""
精确测定简报文本截断点。
探针：纯中文循环，每隔 step 个字符插入一个 ASCII 标记，直到 maxc 个字符。
截图后看最后出现的标记即可判定阈值。
"""
import ctypes
import os
import re
import struct
import subprocess
import sys
import time
import zlib
from ctypes import wintypes
import ctypes as _ct

user = ctypes.windll.user32
gdi = ctypes.windll.gdi32
user.SetProcessDPIAware()

OUT = r'D:\DSH\军事游戏汉化\pgforever\poc'
BRF = r'D:\PGForever1.021\PG\Scenario\0001.pgbrf'
DEPLOYED = None  # 运行前先把已部署译文读进来，跑完恢复

CN = '甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥'
STEP = 20
MAXC = 400


def build_probe(maxc=MAXC, step=STEP):
    """生成带密标记的长中文"""
    tags = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    parts = []
    ci, ti = 0, 0
    s = []
    for i in range(1, maxc + 1):
        s.append(CN[i % len(CN)])
        if i % step == 0:
            s.append('[%s%d]' % (tags[ti % len(tags)], i))
            ti += 1
    return '<p>' + ''.join(s) + '</p>\r\n'


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
                    ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                    ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', _ct.c_int),
                    ('biYPelsPerMeter', _ct.c_int), ('biClrUsed', wintypes.DWORD),
                    ('biClrImportant', wintypes.DWORD)]

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
    gdi.DeleteObject(hbmp)
    gdi.DeleteDC(memdc)
    user.ReleaseDC(hwnd, hdc)

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b''.join(b'\x00' + x for x in rows)
    with open(out, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def click(hwnd, lx, ly, wait=1.8):
    r = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(r))
    user.SetCursorPos(r.left + lx, r.top + ly)
    time.sleep(0.35)
    user.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.12)
    user.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(wait)


def main():
    # 保存当前已部署译文
    deployed = open(BRF, 'rb').read()

    TEXT = build_probe()
    body = re.sub(r'<[^>]+>', '', TEXT)
    n_han = len(re.findall(r'[\u4e00-\u9fff]', body))
    print('探针: 字符 %d / 汉字 %d / UTF-8 %d 字节' % (len(body), n_han, len(TEXT.encode('utf-8'))))

    open(BRF, 'wb').write(TEXT.encode('utf-8'))
    kill_all()
    p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
    hwnd = find_hwnd(p.pid)
    if not hwnd:
        print('未找到窗口')
        kill_all()
        open(BRF, 'wb').write(deployed)
        return
    print('hwnd=%s' % hwnd)
    user.SetWindowPos(hwnd, -1, 710, 220, 500, 600, 0x0040)  # HWND_TOPMOST
    time.sleep(1.5)
    user.SetForegroundWindow(hwnd)
    time.sleep(1.2)
    grab(hwnd, OUT + r'\cut_m0.png')
    click(hwnd, 200, 148)          # 选中列表首项
    grab(hwnd, OUT + r'\cut_m1.png')
    click(hwnd, 245, 538)          # 开始!
    grab(hwnd, OUT + r'\cut_b1.png')
    click(hwnd, 245, 538)
    grab(hwnd, OUT + r'\cut_b2.png')
    click(hwnd, 245, 538)
    grab(hwnd, OUT + r'\cut_b3.png')
    print('已截图 cut_m0/m1, cut_b1/b2/b3')
    try:
        p.terminate()
    except Exception:
        pass
    time.sleep(0.5)
    kill_all()
    open(BRF, 'wb').write(deployed)
    print('已恢复已部署译文')


if __name__ == '__main__':
    main()
