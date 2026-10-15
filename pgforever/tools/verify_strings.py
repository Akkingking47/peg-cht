# -*- coding: utf-8 -*-
r"""
一体化验证：启动 PGForever -> 扫描进程内存 -> 检查目标字符串是否以正确形态加载。

之所以不分成多次命令：本机从 shell 后台启动的进程，会在父命令结束时一起退出，
必须「启动 + 扫描」放在同一个进程生命周期内完成。

用法: python verify_strings.py <词1> [词2 ...]
"""
import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
import time

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
EXE = r'D:\PGForever1.021\PGForever.exe'
CWD = r'D:\PGForever1.021'


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
    if not h:
        return b''
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
    words = sys.argv[1:]
    proc = subprocess.Popen([EXE, '/game', 'pg'], cwd=CWD)
    print('已启动 pid=%d，等待 10s ...' % proc.pid)
    time.sleep(10)

    pid = find_pid('PGForever.exe') or proc.pid
    blob = read_mem(pid)
    print('扫描 pid=%d，内存 %.1f MB\n' % (pid, len(blob) / 1048576.0))

    for w in words:
        u16 = blob.count(w.encode('utf-16-le'))
        u8 = blob.count(w.encode('utf-8'))
        gbk = blob.count(w.encode('gbk')) if all(ord(c) < 0x10000 for c in w) else -1
        flag = '★ 已加载(UTF-16)' if u16 else ('  仅字节形式' if (u8 or gbk) else '  未找到')
        print('  %-10s UTF-16=%-4d UTF-8=%-4d GBK=%-4d  %s' % (w, u16, u8, gbk, flag))

    proc.terminate()


main()
