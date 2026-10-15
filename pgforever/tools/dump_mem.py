# -*- coding: utf-8 -*-
r"""
运行时内存转储：启动游戏，扫描进程内存，找出 pgbrf 简报数据的真实形态。
目的：确认简报文本被读进内存后是 UTF-16 还是 UTF-8，以及被截断的位置。
"""
import ctypes
import ctypes as _ct
import os
import re
import struct
import subprocess
import sys
import time
from ctypes import wintypes

k32 = ctypes.windll.kernel32
user = ctypes.windll.user32

GAME = r'D:\PGForever1.021\PGForever.exe'
BRF = r'D:\PGForever1.021\PG\Scenario\0001.pgbrf'
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc\mem'
os.makedirs(OUT, exist_ok=True)

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

MEM_COMMIT = 0x1000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [('BaseAddress', ctypes.c_void_p),
                ('AllocationBase', ctypes.c_void_p),
                ('AllocationProtect', wintypes.DWORD),
                ('RegionSize', ctypes.c_size_t),
                ('State', wintypes.DWORD),
                ('Protect', wintypes.DWORD),
                ('Type', wintypes.DWORD)]


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


def read_mem(h, addr, size):
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size, ctypes.byref(got))
    if not ok:
        return None
    return buf.raw[:got.value]


def scan(h, needle, label, maxhits=20):
    """在进程内存里搜 needle，返回命中地址"""
    hits = []
    addr = 0
    mbi = MEMORY_BASIC_INFORMATION()
    mbi_size = ctypes.sizeof(mbi)
    while addr < 0x7FFFFFFF and len(hits) < maxhits:
        r = k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), mbi_size)
        if not r:
            break
        base = mbi.BaseAddress or 0
        size = mbi.RegionSize
        if (mbi.State == MEM_COMMIT and not (mbi.Protect & PAGE_GUARD)
                and not (mbi.Protect & PAGE_NOACCESS) and size < 64 * 1024 * 1024):
            data = read_mem(h, base, size)
            if data:
                i = 0
                while True:
                    j = data.find(needle, i)
                    if j < 0:
                        break
                    hits.append((base + j, data[max(0, j - 64):j + 256]))
                    i = j + 1
                    if len(hits) >= maxhits:
                        break
        addr = base + size
        if size == 0:
            addr += 0x1000
    print(f'  [{label}] 命中 {len(hits)} 处')
    for a, ctx in hits:
        print(f'    @ {a:#010x}')
        print(f'      UTF16: {ctx.decode("utf-16-le", "replace")[:80]!r}')
        print(f'      UTF8 : {ctx.decode("utf-8", "replace")[:80]!r}')
    return hits


def main():
    deployed = open(BRF, 'rb').read()
    print('当前 0001.pgbrf: %d 字节' % len(deployed))
    print('  UTF-8 首 60 字节:', deployed[:60])
    print('  UTF-16LE 解码:', deployed.decode('utf-8-sig')[:60])

    kill_all()
    p = subprocess.Popen([GAME, '/game', 'pg'], cwd=os.path.dirname(GAME))
    hwnd = find_hwnd(p.pid)
    if not hwnd:
        print('未找到窗口'); kill_all(); return
    print('pid=%d hwnd=%s' % (p.pid, hwnd))

    h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, p.pid)
    print('OpenProcess =>', h)
    if not h:
        print('无法打开进程'); kill_all(); return

    time.sleep(3.0)

    # 搜索简报中独特的中文串（UTF-16LE 与 UTF-8 两种形态都试）
    probes = [
        ('白色方案', '中文-白色方案'),
        ('库特诺', '中文-库特诺'),
        ('<p>', 'ASCII-<p>'),
        ('Fall Weiss', '英文-FallWeiss'),
        ('Your first mission', '英文-Your first'),
    ]
    for s, label in probes:
        print('=' * 70)
        print(f'搜索: {label}  ({s!r})')
        for enc in ('utf-16-le', 'utf-8', 'gbk'):
            try:
                needle = s.encode(enc)
            except Exception:
                continue
            scan(h, needle, f'{label} [{enc}]', maxhits=6)

    k32.CloseHandle(h)
    try:
        p.terminate()
    except Exception:
        pass
    kill_all()


if __name__ == '__main__':
    main()
