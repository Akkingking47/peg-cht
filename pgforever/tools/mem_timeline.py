# -*- coding: utf-8 -*-
r"""
多时刻内存采样探针
==================
启动游戏后，在多个时间点：
  - PrintWindow 截图（看当前屏幕状态）
  - 扫描内存找 `0001.pgbrf` 的特征串
目的：确定简报数据何时被读入、以什么形态存在、何时被释放。
"""
import ctypes
import ctypes as _ct
import os
import struct
import subprocess
import time
import zlib
from ctypes import wintypes

k32 = ctypes.windll.kernel32
user = ctypes.windll.user32
gdi = ctypes.windll.gdi32
user.SetProcessDPIAware()

GAME = r'D:\PGForever1.021\PGForever.exe'
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc'
os.makedirs(OUT, exist_ok=True)

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01


class MBI(ctypes.Structure):
    _fields_ = [('BaseAddress', ctypes.c_void_p), ('AllocationBase', ctypes.c_void_p),
                ('AllocationProtect', wintypes.DWORD), ('RegionSize', ctypes.c_size_t),
                ('State', wintypes.DWORD), ('Protect', wintypes.DWORD), ('Type', wintypes.DWORD)]


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


def scan(h, needle, maxhits=10):
    hits = []
    addr = 0
    mbi = MBI()
    sz = ctypes.sizeof(mbi)
    while addr < 0x7FFFFFFF and len(hits) < maxhits:
        r = k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), sz)
        if not r:
            break
        base = mbi.BaseAddress or 0
        size = mbi.RegionSize
        if (mbi.State == MEM_COMMIT and not (mbi.Protect & PAGE_GUARD)
                and not (mbi.Protect & PAGE_NOACCESS) and 0 < size < 64 * 1024 * 1024):
            buf = ctypes.create_string_buffer(size)
            got = ctypes.c_size_t(0)
            if k32.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size, ctypes.byref(got)):
                data = buf.raw[:got.value]
                i = 0
                while len(hits) < maxhits:
                    j = data.find(needle, i)
                    if j < 0:
                        break
                    hits.append((base + j, data[j:j + 200]))
                    i = j + 1
        addr = base + size
        if size == 0:
            addr += 0x1000
    return hits


def main():
    brf = open(r'D:\PGForever1.021\PG\Scenario\0001.pgbrf', 'rb').read()
    print('当前 0001.pgbrf %d 字节' % len(brf))

    # 用「当前实际文件内容」的特征做探针：取前 30 字节 + 后 20 字节
    head = brf[:24]
    tail = brf[-24:]
    u16head = brf[:24].decode('utf-8', 'ignore').encode('utf-16-le')
    print('head(utf8)=%r' % head)
    print('tail(utf8)=%r' % tail)

    kill()
    p = subprocess.Popen([GAME, '/game', 'pg'], cwd=os.path.dirname(GAME))
    hwnd = find_hwnd(p.pid)
    if not hwnd:
        print('无窗口'); kill(); return
    h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, p.pid)
    print('pid=%d hwnd=%s h=%s' % (p.pid, hwnd, h))

    acc = 0.0
    for t in (1.5, 2.0, 2.5, 4.0):
        time.sleep(t)
        acc += t
        tag = '%04.1f' % acc
        grab(hwnd, os.path.join(OUT, 'mp_%s.png' % tag.replace('.', '_')))
        hh = scan(h, head, 4)
        ht = scan(h, tail, 4)
        hu = scan(h, u16head, 4)
        print('--- t=%.1fs  utf8head=%d utf8tail=%d u16head=%d' % (acc, len(hh), len(ht), len(hu)))
        for a, ctx in hh[:2]:
            print('    utf8head @%#x %r' % (a, ctx[:70]))
        for a, ctx in hu[:2]:
            try:
                print('    u16head  @%#x %r' % (a, ctx.decode('utf-16-le', 'replace')[:70]))
            except Exception:
                pass

    k32.CloseHandle(h)
    try:
        p.terminate()
    except Exception:
        pass
    kill()
    print('完成')


if __name__ == '__main__':
    main()
