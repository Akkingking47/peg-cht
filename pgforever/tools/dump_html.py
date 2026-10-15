# -*- coding: utf-8 -*-
r"""
抓取运行时渲染出的 HTML 片段
============================
游戏启动后（战役列表已渲染），扫描进程内存，把所有含 HTML 标签特征的
字符串区域 dump 出来，重点找 "1939"/"1943" 等战役相关片段。
"""
import ctypes
import ctypes as _ct
import os
import re
import subprocess
import time
from ctypes import wintypes

k32 = ctypes.windll.kernel32
user = ctypes.windll.user32

GAME = r'D:\PGForever1.021\PGForever.exe'
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc\html_dump'

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


def main():
    os.makedirs(OUT, exist_ok=True)
    kill()
    p = subprocess.Popen([GAME, '/game', 'pg'], cwd=os.path.dirname(GAME))
    hwnd = find_hwnd(p.pid)
    if not hwnd:
        print('无窗口'); kill(); return
    h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, p.pid)
    print('pid=%d hwnd=%s h=%s' % (p.pid, hwnd, h))
    time.sleep(6.0)

    # 收集所有含 '19' + 中文/英文 的可读区域
    mbi = MBI()
    sz = ctypes.sizeof(mbi)
    addr = 0
    regions = []
    total = 0
    while addr < 0x7FFFFFFF:
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
                total += len(data)
                # 找战役关键字（英文原文 & 中文译文 & 标题）
                for key in (b'1939', b'1943', b'Husky', b'Barbarossa', b'Kharkov',
                            b'Poland', b'blitzkrieg'):
                    if key in data:
                        regions.append((base, data, key))
                        break
        addr = base + size
        if size == 0:
            addr += 0x1000

    print('扫描内存 %.1f MB, 命中区域 %d' % (total / 1048576.0, len(regions)))
    # 保存原始字节
    for base, data, key in regions:
        j = data.find(key)
        # 向前扩展到段落开头
        start = max(0, j - 0x100)
        seg = data[start:j + 0x800]
        with open(os.path.join(OUT, 'region_%08x.bin' % (base + start)), 'wb') as f:
            f.write(seg)
        print('原始片段 -> region_%08x.bin (%d 字节, key=%r)' % (base + start, len(seg), key))

    with open(os.path.join(OUT, 'regions.txt'), 'w', encoding='utf-8') as f:
        for base, data, key in regions:
            f.write('\n' + '=' * 78 + '\n')
            f.write('BASE %#010x  key=%r  size=%d\n' % (base, key, len(data)))
            # 在 data 中定位 key 的所有出现，dump 前后文
            i = 0
            cnt = 0
            while cnt < 6:
                j = data.find(key, i)
                if j < 0:
                    break
                seg = data[max(0, j - 200):j + 400]
                f.write('  --- off %#x ---\n' % (base + j))
                f.write('  A(ascii): %r\n' % seg.split(b'\x00')[0][:300])
                try:
                    f.write('  U(utf16): %r\n' % seg.decode('utf-16-le', 'replace')[:300])
                except Exception:
                    pass
                i = j + 1
                cnt += 1
    print('已写 -> %s/regions.txt' % OUT)

    k32.CloseHandle(h)
    try:
        p.terminate()
    except Exception:
        pass
    kill()


if __name__ == '__main__':
    main()
