# -*- coding: utf-8 -*-
r"""
最小调试器：在 exe 的 0x401680（HTMLayoutSetElementHtml 调用前的包装函数）入口
下断点，读取此时 esi[4]（HTML 数据指针）以及它 -0xC 处的 length 字段，
并 dump 该缓冲区前若干字节。

用 DEBUG 权限 OpenProcess + 手工写 int3 + WaitForDebugEvent 循环。
"""
import ctypes
import ctypes as _ct
import os
import struct
import subprocess
import sys
import time
from ctypes import wintypes

k32 = ctypes.windll.kernel32
user = ctypes.windll.user32
GAME = r'D:\PGForever1.021\PGForever.exe'
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc\dbg'

DEBUG_ONLY_THIS_PROCESS = 0x00000002
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_BREAKPOINT = 0x80000003
EXCEPTION_SINGLE_STEP = 0x80000004
PROCESS_ALL = 0x1F0FFF
THREAD_ALL = 0x1F03FF

BREAK_VA = 0x401680


class STARTUPINFO(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('lpReserved', wintypes.LPWSTR),
                ('lpDesktop', wintypes.LPWSTR), ('lpTitle', wintypes.LPWSTR),
                ('dwX', wintypes.DWORD), ('dwY', wintypes.DWORD),
                ('dwXSize', wintypes.DWORD), ('dwYSize', wintypes.DWORD),
                ('dwXCountChars', wintypes.DWORD), ('dwYCountChars', wintypes.DWORD),
                ('dwFillAttribute', wintypes.DWORD), ('dwFlags', wintypes.DWORD),
                ('wShowWindow', wintypes.WORD), ('cbReserved2', wintypes.WORD),
                ('lpReserved2', ctypes.POINTER(ctypes.c_byte)),
                ('hStdInput', wintypes.HANDLE), ('hStdOutput', wintypes.HANDLE),
                ('hStdError', wintypes.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [('hProcess', wintypes.HANDLE), ('hThread', wintypes.HANDLE),
                ('dwProcessId', wintypes.DWORD), ('dwThreadId', wintypes.DWORD)]


class EXCEPTION_RECORD(ctypes.Structure):
    pass


EXCEPTION_RECORD._fields_ = [
    ('ExceptionCode', wintypes.DWORD), ('ExceptionFlags', wintypes.DWORD),
    ('ExceptionRecord', ctypes.POINTER(EXCEPTION_RECORD)),
    ('ExceptionAddress', ctypes.c_void_p), ('NumberParameters', wintypes.DWORD),
    ('ExceptionInformation', ctypes.c_void_p * 15)]


class EXCEPTION_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('ExceptionRecord', EXCEPTION_RECORD), ('dwFirstChance', wintypes.DWORD)]


class CREATE_THREAD_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('hThread', wintypes.HANDLE), ('lpThreadLocalBase', ctypes.c_void_p),
                ('lpStartAddress', ctypes.c_void_p)]


class CREATE_PROCESS_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('hFile', wintypes.HANDLE), ('hProcess', wintypes.HANDLE),
                ('hThread', wintypes.HANDLE), ('lpBaseOfImage', ctypes.c_void_p),
                ('dwDebugInfoFileOffset', wintypes.DWORD),
                ('nDebugInfoSize', wintypes.DWORD),
                ('lpThreadLocalBase', ctypes.c_void_p),
                ('lpStartAddress', ctypes.c_void_p),
                ('lpImageName', ctypes.c_void_p), ('fUnicode', wintypes.WORD)]


class EXIT_THREAD_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('dwExitCode', wintypes.DWORD)]


class EXIT_PROCESS_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('dwExitCode', wintypes.DWORD)]


class LOAD_DLL_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('hFile', wintypes.HANDLE), ('lpBaseOfDll', ctypes.c_void_p),
                ('dwDebugInfoFileOffset', wintypes.DWORD),
                ('nDebugInfoSize', wintypes.DWORD), ('lpImageName', ctypes.c_void_p),
                ('fUnicode', wintypes.WORD)]


class UNLOAD_DLL_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('lpBaseOfDll', ctypes.c_void_p)]


class OUTPUT_DEBUG_STRING_INFO(ctypes.Structure):
    _fields_ = [('lpDebugStringData', ctypes.c_void_p), ('fUnicode', wintypes.WORD),
                ('nDebugStringLength', wintypes.WORD)]


class RIP_INFO(ctypes.Structure):
    _fields_ = [('dwError', wintypes.DWORD), ('dwType', wintypes.DWORD)]


class _U(ctypes.Union):
    _fields_ = [('Exception', EXCEPTION_DEBUG_INFO),
                ('CreateThread', CREATE_THREAD_DEBUG_INFO),
                ('CreateProcessInfo', CREATE_PROCESS_DEBUG_INFO),
                ('ExitThread', EXIT_THREAD_DEBUG_INFO),
                ('ExitProcess', EXIT_PROCESS_DEBUG_INFO),
                ('LoadDll', LOAD_DLL_DEBUG_INFO),
                ('UnloadDll', UNLOAD_DLL_DEBUG_INFO),
                ('DebugString', OUTPUT_DEBUG_STRING_INFO),
                ('RipInfo', RIP_INFO)]


class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [('dwDebugEventCode', wintypes.DWORD), ('dwProcessId', wintypes.DWORD),
                ('dwThreadId', wintypes.DWORD), ('u', _U)]


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
    buf = ctypes.create_string_buffer(n)
    got = ctypes.c_size_t(0)
    if k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)):
        return buf.raw[:got.value]
    return None


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

    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()
    cmd = ctypes.create_unicode_buffer(GAME + ' /game pg')
    ok = k32.CreateProcessW(GAME, cmd, None, None, False,
                            DEBUG_ONLY_THIS_PROCESS, None,
                            os.path.dirname(GAME), ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        print('CreateProcess 失败', k32.GetLastError())
        return
    print('pid=%d' % pi.dwProcessId)
    h = pi.hProcess
    base = None
    bp_set = False
    hits = 0
    log = open(os.path.join(OUT, 'dbg.log'), 'w', encoding='utf-8')
    t0 = time.time()

    de = DEBUG_EVENT()
    while time.time() - t0 < 45:
        if not k32.WaitForDebugEvent(ctypes.byref(de), 800):
            if k32.GetExitCodeProcess(h, ctypes.byref(wintypes.DWORD())):
                pass
            continue
        code = de.dwDebugEventCode
        cont = DBG_CONTINUE
        if code == 3:  # CREATE_PROCESS
            base = de.u.CreateProcessInfo.lpBaseOfImage
            log.write('CreateProcess base=%X\n' % base)
            # 下断点
            if base:
                off = BREAK_VA - 0x400000
                b = rd(h, base + off, 1)
                if b and b[0] != 0xCC:
                    wr(h, base + off, b'\xcc')
                    log.write('bp set at %X (orig %02X)\n' % (base + off, b[0]))
                    bp_set = True
        elif code == 1:  # EXCEPTION
            er = de.u.Exception.ExceptionRecord
            ec = er.ExceptionCode
            if ec == EXCEPTION_BREAKPOINT:
                addr = er.ExceptionAddress or 0
                target = (base or 0) + (BREAK_VA - 0x400000)
                # 首次系统断点
                if not bp_set:
                    log.write('系统断点 @%X\n' % addr)
                elif abs(addr - target) < 8:
                    th = k32.OpenThread(THREAD_ALL, False, de.dwThreadId)
                    ctx = CONTEXT()
                    ctx.ContextFlags = CONTEXT_FULL
                    k32.GetThreadContext(th, ctypes.byref(ctx))
                    log.write('\n=== HIT #%d @%X esi=%08X edi=%08X eax=%08X ===\n'
                              % (hits, addr, ctx.Esi, ctx.Edi, ctx.Eax))
                    # 0x401680: mov esi,ecx  ⇒ esi = this; [esi+4] = 数据指针
                    this = ctx.Esi
                    p4 = rd(h, this + 4, 4)
                    if p4:
                        dataptr = struct.unpack('<I', p4)[0]
                        log.write('this=%08X  [this+4]=%08X\n' % (this, dataptr))
                        if 0x10000 < dataptr < 0x7FFFFFFF:
                            hdr = rd(h, dataptr - 0x20, 0x40)
                            tail = rd(h, dataptr, 0x200)
                            if hdr:
                                L = struct.unpack_from('<I', hdr, 0x20 - 0x20 + 0xC)[0] \
                                    if len(hdr) >= 0x10 else -1
                                # dataptr-0xC
                                L2 = struct.unpack_from('<I', rd(h, dataptr - 0xC, 4) or b'\0\0\0\0', 0)[0]
                                log.write('  [dataptr-0xC] = %d (0x%X)\n' % (L2, L2))
                                log.write('  hdr(-0x20..+0x20) = %s\n' % hdr.hex())
                            if tail:
                                log.write('  data[0:0x120] = %s\n' % tail[:0x120].hex())
                                log.write('  as utf8: %s\n'
                                          % tail[:0x120].decode('utf-8', 'replace'))
                    k32.CloseHandle(th)
                    hits += 1
                    if hits >= 12:
                        log.close()
                        k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, cont)
                        break
                else:
                    log.write('其他断点 @%X\n' % addr)
            elif ec == EXCEPTION_SINGLE_STEP:
                pass
            else:
                cont = DBG_EXCEPTION_NOT_HANDLED
        k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, cont)

    log.write('\n总命中 %d\n' % hits)
    log.close()
    k32.TerminateProcess(h, 0)
    print('->', os.path.join(OUT, 'dbg.log'), 'hits=', hits)


main()
