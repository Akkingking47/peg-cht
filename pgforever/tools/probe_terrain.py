# -*- coding: utf-8 -*-
r"""
启动游戏 -> 扫描内存中「地形名」附近的原始字节 -> 判断引擎是否做了 CP_ACP 转换。

思路：地形名在 MAPNAMES.STR 里是 UTF-8 字节（如 城市 = e5 9f 8e e5 b8 82）。
若引擎用 CP_ACP(UTF-8) 转成宽串，则内存中应出现 UTF-16 的「城市」；
若直接透传字节给 HTMLayout，则只出现 UTF-8 字节。
"""
import ctypes
import ctypes.wintypes as wt
import subprocess
import time

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
EXE = r'D:\PGForever1.021\PGForever.exe'


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD), ('th32ProcessID', wt.DWORD),
                ('th32DefaultHeapID', ctypes.c_void_p), ('th32ModuleID', wt.DWORD),
                ('cntThreads', wt.DWORD), ('th32ParentProcessID', wt.DWORD),
                ('pcPriClassBase', ctypes.c_long), ('dwFlags', wt.DWORD),
                ('szExeFile', ctypes.c_char * 260)]


class MBI(ctypes.Structure):
    _fields_ = [('BaseAddress', ctypes.c_void_p), ('AllocationBase', ctypes.c_void_p),
                ('AllocationProtect', wt.DWORD), ('RegionSize', ctypes.c_size_t),
                ('State', wt.DWORD), ('Protect', wt.DWORD), ('Type', wt.DWORD)]


def find_pid(name):
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)
    e = PROCESSENTRY32()
    e.dwSize = ctypes.sizeof(PROCESSENTRY32)
    ok = k32.Process32First(snap, ctypes.byref(e))
    while ok:
        if e.szExeFile.decode('mbcs', 'ignore').lower() == name.lower():
            k32.CloseHandle(snap)
            return e.th32ProcessID
        ok = k32.Process32Next(snap, ctypes.byref(e))
    k32.CloseHandle(snap)
    return None


def read_mem(pid):
    h = k32.OpenProcess(0x0410, False, pid)
    mbi = MBI()
    addr = 0
    blob = bytearray()
    while k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        if mbi.State == 0x1000 and mbi.Protect in (2, 4, 0x20, 0x40, 0x80):
            buf = ctypes.create_string_buffer(mbi.RegionSize)
            got = ctypes.c_size_t(0)
            if k32.ReadProcessMemory(h, ctypes.c_void_p(mbi.BaseAddress), buf,
                                     mbi.RegionSize, ctypes.byref(got)):
                blob += buf.raw[:got.value]
        addr = (mbi.BaseAddress or 0) + mbi.RegionSize
        if addr == 0:
            break
    k32.CloseHandle(h)
    return bytes(blob)


def main():
    proc = subprocess.Popen([EXE, '/game', 'pg'], cwd=r'D:\PGForever1.021')
    time.sleep(10)
    pid = find_pid('PGForever.exe') or proc.pid
    blob = read_mem(pid)
    print('pid=%d  mem=%.1f MB' % (pid, len(blob) / 1048576.0))

    names = ['开阔地', '海岸', '海洋', '港口', '河流', '山地', '机场',
             '沼泽', '城市', '起伏地', '森林', '沙漠', '要塞', '树篱地']
    print('\n%-8s %6s %6s %6s' % ('地形名', 'UTF16', 'UTF8', 'GBK'))
    for n in names:
        print('%-8s %6d %6d %6d' % (n, blob.count(n.encode('utf-16-le')),
                                    blob.count(n.encode('utf-8')), blob.count(n.encode('gbk'))))

    # 直接看 UTF-8 字节附近的上下文
    needle = '城市'.encode('utf-8')
    i = blob.find(needle)
    print('\n"城市" UTF-8 字节首次出现 @0x%X，周围 64 字节:' % i)
    print(' ', blob[max(0, i - 32):i + 32].hex(' '))

    proc.terminate()


main()
