# -*- coding: utf-8 -*-
"""最小 Windows 调试器 v2（ctypes 结构体版）：抓 OpenGen.exe 首个访问违例现场。"""
import ctypes
import ctypes.wintypes as wt
import os
import struct
import sys

k32 = ctypes.windll.kernel32
GAME = r"D:\OpenPG2"
EXE = os.path.join(GAME, "OpenGen.exe")
DEBUG_ONLY_THIS_PROCESS = 0x00000002
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001

SECTIONS = [(".text", 0x401000, 0x400, 0x476C00), (".rdata", 0x878000, 0x477200, 0x477200),
            (".data", 0x971000, 0x8EE400, 0x56FA00), (".rsrc", 0x12AB000, 0xE5DE00, 0x5BEC00)]


def va2sec(va):
    for n, sva, rp, rs in SECTIONS:
        if sva <= va < sva + rs:
            return "%s+0x%X (FO 0x%X)" % (n, va - sva, rp + va - sva)
    return "模块外/未映射"


class EXCEPTION_RECORD(ctypes.Structure):
    _fields_ = [("ExceptionCode", wt.DWORD), ("ExceptionFlags", wt.DWORD),
                ("ExceptionRecord", ctypes.c_void_p), ("ExceptionAddress", ctypes.c_void_p),
                ("NumberParameters", wt.DWORD),
                ("ExceptionInformation", ctypes.c_void_p * 15)]


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
                ("LoadDll", LOAD_DLL_DEBUG_INFO),
                ("DebugString", OUTPUT_DEBUG_STRING_INFO),
                ("RipInfo", RIP_INFO),
                ("raw", ctypes.c_ubyte * 256)]


class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [("dwDebugEventCode", wt.DWORD), ("dwProcessId", wt.DWORD),
                ("dwThreadId", wt.DWORD), ("u", _U)]


class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPWSTR), ("lpDesktop", wt.LPWSTR),
                ("lpTitle", wt.LPWSTR), ("dwX", wt.DWORD), ("dwY", wt.DWORD),
                ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD), ("dwXCountChars", wt.DWORD),
                ("dwYCountChars", wt.DWORD), ("dwFillAttribute", wt.DWORD),
                ("dwFlags", wt.DWORD), ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", wt.HANDLE),
                ("hStdOutput", wt.HANDLE), ("hStdError", wt.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]


def read_mem(h, va, n):
    buf = ctypes.create_string_buffer(max(n, 1))
    got = ctypes.c_size_t()
    if not k32.ReadProcessMemory(h, ctypes.c_void_p(va), buf, n, ctypes.byref(got)):
        return b""
    return buf.raw[:got.value]


def get_context(tid):
    h = k32.OpenThread(0x0008 | 0x0040, False, tid)
    if not h:
        return None
    buf = ctypes.create_string_buffer(1024)
    struct.pack_into("<I", buf, 0, 0x00100007)
    regs = None
    if k32.GetThreadContext(h, buf):
        g = lambda o: struct.unpack_from("<I", buf, o)[0]
        regs = dict(edi=g(156), esi=g(160), ebx=g(164), edx=g(168), ecx=g(172),
                    eax=g(176), ebp=g(180), eip=g(184), esp=g(196))
    k32.CloseHandle(h)
    return regs


NAMES = {0xC0000005: "ACCESS_VIOLATION", 0x80000003: "BREAKPOINT", 0xC0000094: "DIV0",
         0xC00000FD: "STACK_OVERFLOW", 0xE06D7363: "CPP_EXCEPTION",
         0xC000001D: "ILLEGAL_INSTRUCTION", 0xC0000096: "PRIV_INSTR",
         0xC000008C: "ARRAY_BOUNDS"}


def main():
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()
    cmd = ctypes.create_unicode_buffer(EXE)
    if not k32.CreateProcessW(None, cmd, None, None, False, DEBUG_ONLY_THIS_PROCESS,
                              None, GAME, ctypes.byref(si), ctypes.byref(pi)):
        print("CreateProcess 失败 %d" % k32.GetLastError())
        return
    print("启动 pid=%d" % pi.dwProcessId)
    hproc = pi.hProcess
    ev = DEBUG_EVENT()
    dlls = 0
    trace = open("debugtrace.log", "w", encoding="utf-8")
    while True:
        if not k32.WaitForDebugEvent(ctypes.byref(ev), 10000):
            continue
        code = ev.dwDebugEventCode
        tid = ev.dwThreadId
        cont = DBG_CONTINUE
        if code == 1:                                  # EXCEPTION
            er = ev.u.Exception.ExceptionRecord
            ec = er.ExceptionCode & 0xFFFFFFFF
            ea = er.ExceptionAddress or 0
            print("\n[EXCEPTION] 0x%08X %s  firstChance=%d  EIP=0x%08X (%s)" %
                  (ec, NAMES.get(ec, "?"), ev.u.Exception.dwFirstChance, ea, va2sec(ea)))
            if ec == 0xC0000005:
                npar = er.NumberParameters
                info = [er.ExceptionInformation[i] or 0 for i in range(min(npar, 4))]
                if npar >= 2:
                    print("   %s 地址 0x%08X  (%s)" %
                          ({0: "读", 1: "写", 8: "执行"}.get(info[0], str(info[0])),
                           info[1], va2sec(info[1])))
                print("   params=%s" % ["0x%08X" % x for x in info])
                pg = read_mem(hproc, info[1], 32)
                print("   该地址处内存: %s" % (" ".join("%02X" % b for b in pg) if pg
                                              else "<不可读>"))
                regs = get_context(tid)
                if regs:
                    print("   寄存器 EAX=%08X EBX=%08X ECX=%08X EDX=%08X ESI=%08X EDI=%08X EBP=%08X ESP=%08X"
                          % (regs['eax'], regs['ebx'], regs['ecx'], regs['edx'],
                             regs['esi'], regs['edi'], regs['ebp'], regs['esp']))
                b = read_mem(hproc, max(0, ea - 24), 64)
                if b:
                    print("   EIP 前 24B + 后 40B:")
                    print("     %s" % " ".join("%02X" % x for x in b[:24]))
                    print("     %s" % " ".join("%02X" % x for x in b[24:]))
                stk = read_mem(hproc, regs['esp'] if regs else 0, 64)
                if stk:
                    vals = struct.unpack_from("<16I", stk, 0)
                    print("   栈顶: %s" % " ".join("%08X" % v for v in vals))
                cont = DBG_EXCEPTION_NOT_HANDLED
        elif code == 6:
            dlls += 1
        elif code == 8:
            ds = ev.u.DebugString
            raw = read_mem(hproc, ds.lpDebugStringData or 0, ds.nDebugStringLength)
            trace.write(raw.decode("gbk", "replace").rstrip() + "\n")
        elif code == 5:
            print("\n进程退出 exit=0x%08X" % struct.unpack("<I", struct.pack("<i",
                  ctypes.c_int(ev.u.raw[0]).value))[0] if False else "")
            break
        k32.ContinueDebugEvent(ev.dwProcessId, tid, cont)
    k32.TerminateProcess(hproc, 0)
    print("(已加载 DLL %d 个)" % dlls)


if __name__ == "__main__":
    main()
