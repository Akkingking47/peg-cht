# -*- coding: utf-8 -*-
r"""
运行时「长度字段」探针
======================
目的：验证 exe 在把战役列表 HTML 交给 HTMLayout 时，
      长度参数用的是「字符数」还是「字节数」。

做法：启动游戏进入战役列表 → dump 出内存中的 HTML 段
      → 检查该 HTML 段前面 std::string 的 length 字段
      → 与「真实 UTF-8 字节数」「字符数」分别比对。

输出：poc/len_probe/*.txt
"""
import ctypes
import ctypes as _ct
import os
import struct
import subprocess
import time
from ctypes import wintypes

k32 = ctypes.windll.kernel32
user = ctypes.windll.user32
GAME = r'D:\PGForever1.021\PGForever.exe'
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc\len_probe'

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


def scan(h, keys, wait):
    time.sleep(wait)
    mbi = MBI()
    sz = ctypes.sizeof(mbi)
    addr = 0
    hits = []
    while addr < 0x7FFFFFFF:
        if not k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), sz):
            break
        base = mbi.BaseAddress or 0
        size = mbi.RegionSize
        if (mbi.State == MEM_COMMIT and not (mbi.Protect & PAGE_GUARD)
                and not (mbi.Protect & PAGE_NOACCESS) and 0 < size < 64 * 1024 * 1024):
            buf = ctypes.create_string_buffer(size)
            got = ctypes.c_size_t(0)
            if k32.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size, ctypes.byref(got)):
                data = buf.raw[:got.value]
                for k in keys:
                    i = data.find(k)
                    if i >= 0:
                        hits.append((base, data, k, i))
                        break
        addr = base + size
        if size == 0:
            addr += 0x1000
    return hits


def main():
    os.makedirs(OUT, exist_ok=True)
    kill()
    p = subprocess.Popen([GAME, '/game', 'pg'], cwd=os.path.dirname(GAME))
    hwnd = find_hwnd(p.pid)
    if not hwnd:
        print('无窗口'); kill(); return
    h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, p.pid)
    print('pid=%d hwnd=%s' % (p.pid, hwnd))

    # 战役列表 HTML 里的固定标记（UTF-8 版）
    keys = [b'<option value=1><div.caption>', b'<option value=4><div.caption>',
            b'<option value=5><div.caption>', b'id="ScnList"', b'ScnList']
    hits = scan(h, keys, wait=8.0)
    print('hit regions = %d' % len(hits))

    log = open(os.path.join(OUT, 'report.txt'), 'w', encoding='utf-8')
    for n, (base, data, k, i) in enumerate(hits):
        log.write('\n' + '=' * 78 + '\n')
        log.write('hit#%d base=%08X key=%r off=%#x\n' % (n, base, k, i))
        # 从命中点反查所属 std::string 的 length 字段
        for back in (0xC, 0x10, 0x14, 0x8, 0x4):
            if i - back - 4 < 0:
                continue
            L = struct.unpack_from('<I', data, i - back - 4)[0]
            if 0 < L < 200000:
                log.write('  猜测 length(数据前 %d 字节处) = %d\n' % (back + 4, L))
        # dump 段落
        st = max(0, i - 0x40)
        en = min(len(data), i + 0xA00)
        seg = data[st:en]
        raw = os.path.join(OUT, 'seg_%08x.bin' % (base + st))
        open(raw, 'wb').write(seg)
        log.write('  dump -> %s (%d bytes)\n' % (raw, len(seg)))
        # 打印可读部分
        try:
            txt = seg.decode('utf-8', 'replace')
        except Exception:
            txt = repr(seg)
        log.write('  UTF-8 解码:\n%s\n' % txt[:1200])
        # 字符数 / 字节数对比
        whole = data[i:i + 0x800]
        # 找到 HTML 结尾
        e = whole.find(b'</html>')
        if e < 0:
            e = whole.find(b'\x00')
        if e > 0:
            html = whole[:e]
            bcount = len(html)
            try:
                ccount = len(html.decode('utf-8'))
            except Exception:
                ccount = -1
            log.write('  该段 HTML: 字节数=%d  UTF-8 字符数=%d\n' % (bcount, ccount))
    log.close()
    print('->', os.path.join(OUT, 'report.txt'))
    kill()


main()
