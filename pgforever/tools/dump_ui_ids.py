# -*- coding: utf-8 -*-
r"""
扫描 PGForever.exe 的进程内存，找出所有形如 Type/Unit/Hover 前缀的 UI 元素 id
以及伴随出现的可见文案（UTF-16LE），用于确认"某段文字到底由 htm 提供还是 exe 注入"。

用法: python dump_ui_ids.py [关键词...]
"""
import ctypes
import ctypes.wintypes as wt
import re
import sys

k32 = ctypes.WinDLL('kernel32', use_last_error=True)

TH32CS_SNAPPROCESS = 0x2
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
PAGE_READABLE = (0x02, 0x04, 0x20, 0x40)


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD),
                ('th32ProcessID', wt.DWORD), ('th32DefaultHeapID', ctypes.POINTER(ctypes.c_ulong)),
                ('th32ModuleID', wt.DWORD), ('cntThreads', wt.DWORD),
                ('th32ParentProcessID', wt.DWORD), ('pcPriClassBase', ctypes.c_long),
                ('dwFlags', wt.DWORD), ('szExeFile', ctypes.c_char * 260)]


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [('BaseAddress', ctypes.c_void_p), ('AllocationBase', ctypes.c_void_p),
                ('AllocationProtect', wt.DWORD), ('RegionSize', ctypes.c_size_t),
                ('State', wt.DWORD), ('Protect', wt.DWORD), ('Type', wt.DWORD)]


def find_pid(name):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == -1:
        return None
    e = PROCESSENTRY32()
    e.dwSize = ctypes.sizeof(PROCESSENTRY32)
    ok = k32.Process32First(snap, ctypes.byref(e))
    pid = None
    while ok:
        if e.szExeFile.decode('mbcs', 'ignore').lower() == name.lower():
            pid = e.th32ProcessID
            break
        ok = k32.Process32Next(snap, ctypes.byref(e))
    k32.CloseHandle(snap)
    return pid


def regions(pid):
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        raise OSError('OpenProcess failed: %d' % ctypes.get_last_error())
    mbi = MEMORY_BASIC_INFORMATION()
    addr = 0
    out = []
    while k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        if mbi.State == MEM_COMMIT and mbi.Protect in PAGE_READABLE:
            buf = ctypes.create_string_buffer(mbi.RegionSize)
            got = ctypes.c_size_t(0)
            if k32.ReadProcessMemory(h, ctypes.c_void_p(mbi.BaseAddress), buf,
                                     mbi.RegionSize, ctypes.byref(got)):
                out.append((mbi.BaseAddress, buf.raw[:got.value]))
        addr = (mbi.BaseAddress or 0) + mbi.RegionSize
        if addr == 0:
            break
    k32.CloseHandle(h)
    return out


def main():
    keys = sys.argv[1:] or ['TargetType', 'CloseDefense']
    pid = find_pid('PGForever.exe')
    if not pid:
        print('PGForever.exe 未运行')
        return
    print('PID =', pid)
    blob = b''.join(data for _, data in regions(pid))
    print('内存总量 = %.1f MB' % (len(blob) / 1048576.0))

    for k in keys:
        kw = k.encode('utf-16-le')
        hits = []
        start = 0
        while True:
            i = blob.find(kw, start)
            if i < 0:
                break
            # 回退到字符串起点（UTF-16 可见字符）
            s, e = i, i
            while s - 2 > 0 and 32 <= blob[s - 2] < 0x7f and blob[s - 1] == 0:
                s -= 2
            while e + 2 < len(blob) and (32 <= blob[e] < 0x7f or blob[e:e + 2] == b'\x00\x00'):
                if blob[e:e + 2] == b'\x00\x00':
                    break
                e += 2
            raw = blob[s:e]
            try:
                txt = raw.decode('utf-16-le')
            except Exception:
                txt = repr(raw)
            hits.append(txt)
            start = i + 2
        print('\n--- %s : %d 处 ---' % (k, len(hits)))
        for t in sorted(set(hits))[:25]:
            print('   ', t[:120])


main()
