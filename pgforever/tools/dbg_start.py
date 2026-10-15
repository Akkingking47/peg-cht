# -*- coding: utf-8 -*-
r"""
启动即调试：CreateProcess(DEBUG_ONLY_THIS_PROCESS) 并在 CREATE_PROCESS 后
立即在 0x4016A6 下断，读栈参数。加了异常保护，避免卡死。
"""
import ctypes
import os
import struct
import subprocess
import sys
import time
from ctypes import wintypes

k32 = ctypes.windll.kernel32
GAME = r'D:\PGForever1.021\PGForever.exe'
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc\dbg'

DEBUG_ONLY_THIS_PROCESS = 0x00000002
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_BREAKPOINT = 0x80000003
EXCEPTION_SINGLE_STEP = 0x80000004
PROCESS_ALL = 0x1F0FFF
THREAD_ALL = 0x1F03FF
IMGBASE = 0x400000
BREAK_VA = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x4016A6


class EXCEPTION_RECORD(ctypes.Structure):
    pass


EXCEPTION_RECORD._fields_ = [
    ('ExceptionCode', wintypes.DWORD), ('ExceptionFlags', wintypes.DWORD),
    ('ExceptionRecord', ctypes.POINTER(EXCEPTION_RECORD)),
    ('ExceptionAddress', ctypes.c_void_p), ('NumberParameters', wintypes.DWORD),
    ('ExceptionInformation', ctypes.c_void_p * 15)]


class EXCEPTION_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('ExceptionRecord', EXCEPTION_RECORD), ('dwFirstChance', wintypes.DWORD)]


class CREATE_PROCESS_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('hFile', wintypes.HANDLE), ('hProcess', wintypes.HANDLE),
                ('hThread', wintypes.HANDLE), ('lpBaseOfImage', ctypes.c_void_p),
                ('dwDebugInfoFileOffset', wintypes.DWORD), ('nDebugInfoSize', wintypes.DWORD),
                ('lpThreadLocalBase', ctypes.c_void_p), ('lpStartAddress', ctypes.c_void_p),
                ('lpImageName', ctypes.c_void_p), ('fUnicode', wintypes.WORD)]


class DEBUG_EVENT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [('Exception', EXCEPTION_DEBUG_INFO),
                    ('CreateProcessInfo', CREATE_PROCESS_DEBUG_INFO),
                    ('raw', ctypes.c_byte * 160)]
    _fields_ = [('dwDebugEventCode', wintypes.DWORD), ('dwProcessId', wintypes.DWORD),
                ('dwThreadId', wintypes.DWORD), ('u', _U)]


class STARTUPINFO(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('lpReserved', wintypes.LPWSTR),
                ('lpDesktop', wintypes.LPWSTR), ('lpTitle', wintypes.LPWSTR),
                ('dwX', wintypes.DWORD), ('dwY', wintypes.DWORD),
                ('dwXSize', wintypes.DWORD), ('dwYSize', wintypes.DWORD),
                ('dwXCountChars', wintypes.DWORD), ('dwYCountChars', wintypes.DWORD),
                ('dwFillAttribute', wintypes.DWORD), ('dwFlags', wintypes.DWORD),
                ('wShowWindow', wintypes.WORD), ('cbReserved2', wintypes.WORD),
                ('lpReserved2', ctypes.c_void_p),
                ('hStdInput', wintypes.HANDLE), ('hStdOutput', wintypes.HANDLE),
                ('hStdError', wintypes.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [('hProcess', wintypes.HANDLE), ('hThread', wintypes.HANDLE),
                ('dwProcessId', wintypes.DWORD), ('dwThreadId', wintypes.DWORD)]


CONTEXT_FULL = 0x00010007


class CONTEXT(ctypes.Structure):
    _fields_ = [('ContextFlags', wintypes.DWORD), ('Dr0', wintypes.DWORD),
                ('Dr1', wintypes.DWORD), ('Dr2', wintypes.DWORD), ('Dr3', wintypes.DWORD),
                ('Dr6', wintypes.DWORD), ('Dr7', wintypes.DWORD),
                ('FloatSave', ctypes.c_byte * 112),
                ('SegGs', wintypes.DWORD), ('SegFs', wintypes.DWORD),
                ('SegEs', wintypes.DWORD), ('SegDs', wintypes.DWORD),
                ('Edi', wintypes.DWORD), ('Esi', wintypes.DWORD),
                ('Ebx', wintypes.DWORD), ('Edx', wintypes.DWORD),
                ('Ecx', wintypes.DWORD), ('Eax', wintypes.DWORD),
                ('Ebp', wintypes.DWORD), ('Eip', wintypes.DWORD),
                ('SegCs', wintypes.DWORD), ('EFlags', wintypes.DWORD),
                ('Esp', wintypes.DWORD), ('SegSs', wintypes.DWORD),
                ('ExtendedRegisters', ctypes.c_byte * 512)]


def rd(h, addr, n):
    if not addr or addr > 0x7FFFFFFF:
        return None
    buf = ctypes.create_string_buffer(n)
    got = ctypes.c_size_t(0)
    if k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)):
        return buf.raw[:got.value]
    return None


def u32(b, o=0):
    return struct.unpack_from('<I', b, o)[0] if b and len(b) >= o + 4 else None


def wr(h, addr, data):
    old = ctypes.c_ulong(0)
    k32.VirtualProtectEx(h, ctypes.c_void_p(addr), len(data), 0x40, ctypes.byref(old))
    got = ctypes.c_size_t(0)
    ok = k32.WriteProcessMemory(h, ctypes.c_void_p(addr), data, len(data), ctypes.byref(got))
    k32.VirtualProtectEx(h, ctypes.c_void_p(addr), len(data), old, ctypes.byref(old))
    k32.FlushInstructionCache(h, ctypes.c_void_p(addr), len(data))
    return ok


def main():
    os.makedirs(OUT, exist_ok=True)
    subprocess.run(['taskkill', '/F', '/IM', 'PGForever.exe'], capture_output=True)
    time.sleep(0.8)
    si = STARTUPINFO(); si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()
    cmd = ctypes.create_unicode_buffer(GAME + ' /game pg')
    ok = k32.CreateProcessW(GAME, cmd, None, None, False, DEBUG_ONLY_THIS_PROCESS,
                            None, os.path.dirname(GAME), ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        print('CreateProcess 失败', k32.GetLastError()); return
    pid, h = pi.dwProcessId, pi.hProcess
    print('pid=%d h=%s' % (pid, h))
    off = BREAK_VA - IMGBASE
    log = open(os.path.join(OUT, 'stack2.log'), 'w', encoding='utf-8')
    log.write('BREAK_VA=%X off=%X\n' % (BREAK_VA, off))
    bp_set = False
    hits = 0
    first_break_seen = False
    t0 = time.time()
    de = DEBUG_EVENT()
    while time.time() - t0 < 60:
        if not k32.WaitForDebugEvent(ctypes.byref(de), 1500):
            continue
        code = de.dwDebugEventCode
        cont = DBG_CONTINUE
        if code == 3:  # CREATE_PROCESS
            b = rd(h, IMGBASE + off, 1)
            log.write('CREATE_PROCESS, 原字节@%X=%s\n' % (BREAK_VA, b.hex() if b else '?'))
            if b and b[0] != 0xCC:
                wr(h, IMGBASE + off, b'\xcc')
                bp_set = True
                log.write('bp 已设置\n')
        elif code == 1:
            er = de.u.Exception.ExceptionRecord
            ec = er.ExceptionCode
            ea = er.ExceptionAddress or 0
            if ec == EXCEPTION_BREAKPOINT:
                if not first_break_seen:
                    # 这是系统初始断点
                    first_break_seen = True
                    log.write('系统断点 @%X\n' % ea)
                elif abs(ea - (IMGBASE + off)) < 4:
                    th = k32.OpenThread(THREAD_ALL, False, de.dwThreadId)
                    ctx = CONTEXT(); ctx.ContextFlags = CONTEXT_FULL
                    got = k32.GetThreadContext(th, ctypes.byref(ctx))
                    esp = ctx.Esp
                    log.write('\n=== HIT#%d @%X esp=%08X eax=%d(0x%X) esi=%08X edi=%08X ===\n'
                              % (hits, ea, esp, ctx.Eax, ctx.Eax, ctx.Esi, ctx.Edi))
                    st = rd(h, esp, 0xA0)
                    if st:
                        for k in range(0, 0x20, 4):
                            log.write('  [esp+%#04x] = %08X\n' % (k, u32(st, k)))
                        p_utf8 = u32(st, 4)
                        p_elem = u32(st, 0x8C)
                        log.write('  [esp+4]  -> %08X\n' % (p_utf8 or 0))
                        log.write('  [esp+0x8c]-> %08X  (应=hElem)\n' % (p_elem or 0))
                        if p_utf8 and 0x10000 < p_utf8 < 0x7FFFFFFF:
                            d = rd(h, p_utf8, 0x180)
                            if d:
                                z = d.find(b'\x00')
                                s = d[:z] if z >= 0 else d
                                log.write('  [esp+4]处内容: %s\n'
                                          % s[:280].decode('utf-8', 'replace'))
                                # 也按 utf-16 试
                                try:
                                    log.write('  (按UTF-16LE): %s\n'
                                              % d[:80].decode('utf-16le', 'replace'))
                                except Exception:
                                    pass
                    k32.CloseHandle(th)
                    hits += 1
                    if hits >= 6:
                        k32.ContinueDebugEvent(pid, de.dwThreadId, cont)
                        break
                else:
                    log.write('其他断点 @%X\n' % ea)
            else:
                cont = DBG_EXCEPTION_NOT_HANDLED
        k32.ContinueDebugEvent(pid, de.dwThreadId, cont)

    log.write('\nhits=%d\n' % hits)
    log.close()
    print('-> stack2.log hits=%d' % hits)
    k32.TerminateProcess(h, 0)


main()
