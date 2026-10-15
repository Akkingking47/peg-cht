# -*- coding: utf-8 -*-
"""调试器 v3：解析 fault 所在模块 + Wow64 上下文 + 栈回溯；正常版会跑满并报告「未崩溃」。

用法: python dbgrun2.py [等待秒数]
"""
import ctypes
import ctypes.wintypes as wt
import os
import struct
import sys

k32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi
GAME = r"D:\OpenPG2"
EXE = os.path.join(GAME, "OpenGen.exe")
DEBUG_ONLY_THIS_PROCESS = 0x00000002
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001


class EXCEPTION_RECORD(ctypes.Structure):
    _fields_ = [("ExceptionCode", wt.DWORD), ("ExceptionFlags", wt.DWORD),
                ("ExceptionRecord", ctypes.c_void_p), ("ExceptionAddress", ctypes.c_void_p),
                ("NumberParameters", wt.DWORD), ("ExceptionInformation", ctypes.c_void_p * 15)]


class EXCEPTION_DEBUG_INFO(ctypes.Structure):
    _fields_ = [("ExceptionRecord", EXCEPTION_RECORD), ("dwFirstChance", wt.DWORD)]


class CREATE_PROCESS_DEBUG_INFO(ctypes.Structure):
    _fields_ = [("hFile", wt.HANDLE), ("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                ("lpBaseOfImage", ctypes.c_void_p), ("dwDebugInfoFileOffset", wt.DWORD),
                ("nDebugInfoSize", wt.DWORD), ("lpThreadLocalBase", ctypes.c_void_p),
                ("lpStartAddress", ctypes.c_void_p), ("lpImageName", ctypes.c_void_p),
                ("fUnicode", wt.WORD)]


class LOAD_DLL_DEBUG_INFO(ctypes.Structure):
    _fields_ = [("hFile", wt.HANDLE), ("lpBaseOfDll", ctypes.c_void_p),
                ("dwDebugInfoFileOffset", wt.DWORD), ("nDebugInfoSize", wt.DWORD),
                ("lpImageName", ctypes.c_void_p), ("fUnicode", wt.WORD)]


class OUTPUT_DEBUG_STRING_INFO(ctypes.Structure):
    _fields_ = [("lpDebugStringData", ctypes.c_void_p), ("fUnicode", wt.WORD),
                ("nDebugStringLength", wt.WORD)]


class RIP_INFO(ctypes.Structure):
    _fields_ = [("dwError", wt.DWORD), ("dwType", wt.DWORD)]


class _U(ctypes.Union):
    _fields_ = [("Exception", EXCEPTION_DEBUG_INFO),
                ("CreateProcessInfo", CREATE_PROCESS_DEBUG_INFO),
                ("LoadDll", LOAD_DLL_DEBUG_INFO), ("DebugString", OUTPUT_DEBUG_STRING_INFO),
                ("RipInfo", RIP_INFO), ("raw", ctypes.c_ubyte * 256)]


class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [("dwDebugEventCode", wt.DWORD), ("dwProcessId", wt.DWORD),
                ("dwThreadId", wt.DWORD), ("u", _U)]


class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("a", ctypes.c_byte * 64)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]


class MODULEINFO(ctypes.Structure):
    _fields_ = [("lpBaseOfDll", ctypes.c_void_p), ("SizeOfImage", wt.DWORD),
                ("EntryPoint", ctypes.c_void_p)]


def read_mem(h, va, n):
    buf = ctypes.create_string_buffer(max(n, 1))
    got = ctypes.c_size_t()
    if not k32.ReadProcessMemory(h, ctypes.c_void_p(va), buf, n, ctypes.byref(got)):
        return b""
    return buf.raw[:got.value]


def modules(h):
    psapi.EnumProcessModules.argtypes = [wt.HANDLE, ctypes.c_void_p, wt.DWORD,
                                        ctypes.POINTER(wt.DWORD)]
    psapi.GetModuleBaseNameW.argtypes = [wt.HANDLE, ctypes.c_void_p, wt.LPWSTR, wt.DWORD]
    psapi.GetModuleInformation.argtypes = [wt.HANDLE, ctypes.c_void_p,
                                          ctypes.POINTER(MODULEINFO), wt.DWORD]
    arr = (ctypes.c_void_p * 512)()
    need = wt.DWORD()
    if not psapi.EnumProcessModules(h, ctypes.byref(arr), ctypes.sizeof(arr),
                                    ctypes.byref(need)):
        return []
    out = []
    for i in range(need.value // ctypes.sizeof(ctypes.c_void_p)):
        hm = ctypes.c_void_p(arr[i])
        if not hm.value:
            continue
        buf = ctypes.create_unicode_buffer(512)
        psapi.GetModuleBaseNameW(h, hm, buf, 512)
        mi = MODULEINFO()
        psapi.GetModuleInformation(h, hm, ctypes.byref(mi), ctypes.sizeof(mi))
        out.append((hm.value or 0, mi.SizeOfImage, buf.value))
    return out


DLLS = []


def resolve(mods, va):
    for base, name in sorted(DLLS, key=lambda x: -x[0]):
        if base <= va:
            return "%s + 0x%X" % (os.path.basename(name), va - base)
    for base, size, name in mods:
        if base <= va < base + max(size, 0x1000):
            return "%s + 0x%X" % (name, va - base)
    return "<未知模块>"


def ctx32(tid):
    h = k32.OpenThread(0x0008 | 0x0040, False, tid)
    if not h:
        return None
    buf = ctypes.create_string_buffer(1024)
    struct.pack_into("<I", buf, 0, 0x00100007)
    r = None
    try:
        fn = k32.Wow64GetThreadContext
    except AttributeError:
        fn = None
    if fn and fn(h, buf):
        g = lambda o: struct.unpack_from("<I", buf, o)[0]
        r = dict(edi=g(156), esi=g(160), ebx=g(164), edx=g(168), ecx=g(172), eax=g(176),
                 ebp=g(180), eip=g(184), esp=g(196))
    k32.CloseHandle(h)
    return r


def main():
    wait = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()
    cmd = ctypes.create_unicode_buffer(EXE)
    if not k32.CreateProcessW(None, cmd, None, None, False, DEBUG_ONLY_THIS_PROCESS,
                              None, GAME, ctypes.byref(si), ctypes.byref(pi)):
        print("CreateProcess 失败")
        return
    print("启动 pid=%d" % pi.dwProcessId)
    h = pi.hProcess
    ev = DEBUG_EVENT()
    trace = open(sys.argv[2] if len(sys.argv) > 2 else "debugtrace.log", "w", encoding="utf-8")
    idle_ms, crashes, alive = 0, 0, False
    while True:
        if not k32.WaitForDebugEvent(ctypes.byref(ev), 1000):
            idle_ms += 1000
            if idle_ms >= wait * 1000:
                alive = True
                break
            continue
        idle_ms = 0
        code, tid = ev.dwDebugEventCode, ev.dwThreadId
        cont = DBG_CONTINUE
        if code == 1:
            er = ev.u.Exception.ExceptionRecord
            ec = er.ExceptionCode & 0xFFFFFFFF
            ea = er.ExceptionAddress or 0
            first = ev.u.Exception.dwFirstChance
            if ec != 0x80000003:
                mods = modules(h)
                print("\n[EXCEPTION] 0x%08X firstChance=%d EIP=0x%08X  (%s)" %
                      (ec, first, ea, resolve(mods, ea)))
                if ec == 0xC0000005:
                    crashes += 1
                    np = er.NumberParameters
                    inf = [er.ExceptionInformation[i] or 0 for i in range(min(np, 4))]
                    print("   %s 地址 0x%08X" % ({0: "读", 1: "写", 8: "执行"}.get(inf[0],
                          str(inf[0])), inf[1]))
                    b = read_mem(h, max(0, ea - 8), 24)
                    print("   EIP 处字节: %s" % " ".join("%02X" % x for x in b))
                    r = ctx32(tid)
                    if r:
                        print("   EAX=%08X EBX=%08X ECX=%08X EDX=%08X ESI=%08X EDI=%08X EBP=%08X ESP=%08X"
                              % (r['eax'], r['ebx'], r['ecx'], r['edx'], r['esi'],
                                 r['edi'], r['ebp'], r['esp']))
                        chain, ebp = [], r['ebp']
                        for _ in range(12):
                            if not ebp:
                                break
                            fr = read_mem(h, ebp, 8)
                            if s := fr:
                                nxt, ra = struct.unpack("<II", fr)
                                chain.append(ra)
                                if nxt <= ebp:
                                    break
                                ebp = nxt
                            else:
                                break
                        print("   栈回溯:")
                        for ra in chain:
                            print("      0x%08X  %s  (%s)" %
                                  (ra, resolve(mods, ra), "exe" if 0x400000 <= ra < 0x1900000 else ""))
                    cont = DBG_EXCEPTION_NOT_HANDLED
        elif code == 6:
            k32.GetFinalPathNameByHandleW.restype = wt.DWORD
            buf = ctypes.create_unicode_buffer(512)
            k32.GetFinalPathNameByHandleW(ev.u.LoadDll.hFile, buf, 512, 0)
            DLLS.append((ev.u.LoadDll.lpBaseOfDll or 0, buf.value))
            print("  [DLL] 0x%08X %s" % (ev.u.LoadDll.lpBaseOfDll or 0, buf.value))
        elif code == 8:
            ds = ev.u.DebugString
            trace.write(read_mem(h, ds.lpDebugStringData or 0, ds.nDebugStringLength)
                        .decode("gbk", "replace") + "\n")
        k32.ContinueDebugEvent(ev.dwProcessId, tid, cont)
        if code == 5:
            print("\n进程退出")
            break
    if alive:
        print("\n== 运行 %d 秒无异常：**启动正常** ==" % wait)
    print("访问违例次数: %d" % crashes)
    k32.TerminateProcess(h, 0)


if __name__ == "__main__":
    main()
