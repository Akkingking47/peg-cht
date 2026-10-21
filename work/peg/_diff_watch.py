# -*- coding: utf-8 -*-
"""只读差分观察器：每 0.4 秒对几片关键内存做快照比对，只打印“变了的地址”。
用来找出“点选单位”到底改了哪个变量（游戏仍在跑时用）。
用法：python work\\peg\\_diff_watch.py [秒数，默认 100]
只 ReadProcessMemory，绝不写目标进程。
"""
import ctypes as C
import struct
import sys
import time

k32 = C.WinDLL("kernel32", use_last_error=True)
k32.CreateToolhelp32Snapshot.restype = C.c_void_p
k32.CreateToolhelp32Snapshot.argtypes = [C.c_uint32, C.c_uint32]
k32.OpenProcess.restype = C.c_void_p
k32.OpenProcess.argtypes = [C.c_uint32, C.c_int, C.c_uint32]
k32.ReadProcessMemory.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p, C.c_size_t,
                                  C.POINTER(C.c_size_t)]
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

REGIONS = [
    ("dirty/scroll缓存", 0x498D00, 0x100),
    ("滚动与视口", 0x4AF200, 0x200),
    ("extent/范围表头", 0x622D00, 0x200),
    ("疑似选中变量", 0x686F00, 0x200),
    ("地图面指针区", 0x655500, 0x100),
    ("0x6505a0 表", 0x650500, 0x100),
    ("0x61f0c0 缓冲", 0x61F000, 0x200),
    ("迷雾/占有表", 0x67E800, 0x100),
]
QUIET_IF_MORE = 24


class PROCESSENTRY32(C.Structure):
    _fields_ = [("dwSize", C.c_uint32), ("cntUsage", C.c_uint32),
                ("th32ProcessID", C.c_uint32), ("th32DefaultHeapID", C.c_void_p),
                ("th32ModuleID", C.c_uint32), ("cntThreads", C.c_uint32),
                ("th32ParentProcessID", C.c_uint32), ("pcPriClassBase", C.c_int32),
                ("dwFlags", C.c_uint32), ("szExeFile", C.c_char * 260)]


k32.Process32First.argtypes = [C.c_void_p, C.POINTER(PROCESSENTRY32)]
k32.Process32Next.argtypes = [C.c_void_p, C.POINTER(PROCESSENTRY32)]


def find_pid():
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)
    pe = PROCESSENTRY32()
    pe.dwSize = C.sizeof(PROCESSENTRY32)
    pid = None
    if k32.Process32First(snap, C.byref(pe)):
        while True:
            if pe.szExeFile.lower() == b"peg030.exe":
                pid = pe.th32ProcessID
                break
            if not k32.Process32Next(snap, C.byref(pe)):
                break
    k32.CloseHandle(snap)
    return pid


def rd(proc, addr, n):
    buf = C.create_string_buffer(n)
    got = C.c_size_t(0)
    if not k32.ReadProcessMemory(proc, C.c_void_p(addr), buf, n, C.byref(got)):
        return None
    return buf.raw[:got.value]


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 100.0
    pid = find_pid()
    if not pid:
        print("没找到 PeG030.exe")
        return 1
    proc = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    print("pid=%d 观察 %.0f 秒；每 0.4 秒打印一次“变了的地址”" % (pid, secs))
    prev = {}
    for name, base, ln in REGIONS:
        prev[base] = (name, ln, rd(proc, base, ln))
    t0 = time.time()
    while time.time() - t0 < secs:
        time.sleep(0.4)
        for base, (name, ln, old) in prev.items():
            new = rd(proc, base, ln)
            if new is None or old is None:
                if old is not None:
                    print("[%5.1fs] %s：读不到了（游戏退出？）" % (time.time() - t0, name))
                prev[base] = (name, ln, new)
                continue
            if new == old:
                continue
            diffs = []
            for off in range(0, min(len(old), len(new)) - 3, 4):
                o = struct.unpack_from("<I", old, off)[0]
                n = struct.unpack_from("<I", new, off)[0]
                if o != n:
                    diffs.append((off, o, n))
            if len(diffs) > QUIET_IF_MORE:
                print("[%5.1fs] %s：%d 处变化（噪声区，略）首处 %08X %08X->%08X"
                      % (time.time() - t0, name, len(diffs), base + diffs[0][0],
                         diffs[0][1], diffs[0][2]))
            else:
                for off, o, n in diffs:
                    print("[%5.1fs] %s：%08X  %08X -> %08X  (%d -> %d)"
                          % (time.time() - t0, name, base + off, o, n, o, n))
            prev[base] = (name, ln, new)
            sys.stdout.flush()
    k32.CloseHandle(proc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
