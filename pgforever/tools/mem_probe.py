# -*- coding: utf-8 -*-
r"""
运行时截断探针（内存版）
========================
思路：
  1. 备份 0001.pgbrf
  2. 写入形如 <p>AAAA...AAAA</p> 的纯 ASCII 长串（每个字符唯一递增，便于定位）
     —— 用固定长度可打印 ASCII 字符集，避免 UTF-8 多字节干扰
  3. 启动游戏（首屏列表会加载该项简报）
  4. 扫描进程内存，找到我们写入的串，看它在内存中被截断/变形的位置
  5. 恢复备份

这样可判定：瓶颈在「读入」还是「显示」，以及截断阈值（字节 / 字符）。
"""
import ctypes
import ctypes as _ct
import os
import subprocess
import sys
import time
from ctypes import wintypes

k32 = ctypes.windll.kernel32
user = ctypes.windll.user32

GAME = r'D:\PGForever1.021\PGForever.exe'
BRF = r'D:\PGForever1.021\PG\Scenario\0001.pgbrf'

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


def scan_all(h, needle, maxhits=30):
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
                    hits.append((base + j, data))
                    i = j + 1
        addr = base + size
        if size == 0:
            addr += 0x1000
    return hits


def main():
    original = open(BRF, 'rb').read()
    print('原 0001.pgbrf: %d 字节' % len(original))
    try:
        # ---- 构造纯 ASCII 探针：唯一可识别的递增串 ----
        # 用 62 个可打印字符循环，但每 10 个插一个 [NNN] 标记
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        parts = []
        for i in range(1, 401):
            parts.append(chars[i % len(chars)])
            if i % 10 == 0:
                parts.append('[%03d]' % i)
        probe_body = ''.join(parts)
        probe = '<p>' + probe_body + '</p>\r\n'
        pb = probe.encode('utf-8')
        print('探针: 正文 %d 字符 / 全串 %d 字节' % (len(probe_body), len(pb)))
        print('探针尾部:', probe_body[-80:])
        open(BRF, 'wb').write(pb)

        kill()
        p = subprocess.Popen([GAME, '/game', 'pg'], cwd=os.path.dirname(GAME))
        hwnd = find_hwnd(p.pid)
        if not hwnd:
            print('未找到窗口'); return
        h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, p.pid)
        print('pid=%d hwnd=%s handle=%s' % (p.pid, hwnd, h))
        if not h:
            return
        time.sleep(4.0)

        # 搜 ASCII 探针（UTF-8 == 原文，因为纯 ASCII）
        for lbl, needle in [
            ('探针头部 a-zA-Z0-9', probe_body[:40].encode()),
            ('尾部标记 [400]', b'[400]'),
            ('中部标记 [200]', b'[200]'),
            ('中部标记 [300]', b'[300]'),
            ('<p>', b'<p>'),
            ('</p>', b'</p>'),
        ]:
            hits = scan_all(h, needle, maxhits=8)
            print('=' * 66)
            print('搜索 %s -> %d 处' % (lbl, len(hits)))
            for a, data in hits[:5]:
                rel = data.find(needle)
                ctx = data[max(0, rel - 40):rel + 160]
                print('  @%#010x' % a)
                # 尝试多种解码
                for enc in ('ascii', 'utf-16-le'):
                    try:
                        t = ctx.decode(enc, 'replace')
                        t = t.replace('\x00', '')
                        print('     %-8s %r' % (enc, t[:110]))
                    except Exception:
                        pass

        k32.CloseHandle(h)
    finally:
        try:
            p.terminate()
        except Exception:
            pass
        kill()
        open(BRF, 'wb').write(original)
        print('已恢复原文件')


if __name__ == '__main__':
    main()
