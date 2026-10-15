# -*- coding: utf-8 -*-
r"""
栈参数探针：在 0x4016A6（已取到 length，即将 push 参数）下硬件断点，
读出 eax（length）、[esp+4]（utf8bytes）、[esp+0x8c]（hElem），
并 dump [esp+4] 指向的字节，判断它是不是 UTF-8 数据。
"""
import ctypes
import os
import struct
import subprocess
import time
from ctypes import wintypes

k32 = ctypes.windll.kernel32
GAME = r'D:\PGForever1.021\PGForever.exe'
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc\dbg'

DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_BREAKPOINT = 0x80000003
EXCEPTION_SINGLE_STEP = 0x80000004
PROCESS_ALL = 0x1F0FFF
THREAD_ALL = 0x1F03FF
IMGBASE = 0x400000
BREAK_VA = 0x4016A6


class EXCEPTION_RECORD(ctypes.Structure):
    pass


EXCEPTION_RECORD._fields_ = [
    ('ExceptionCode', wintypes.DWORD), ('ExceptionFlags', wintypes.DWORD),
    ('ExceptionRecord', ctypes.POINTER(EXCEPTION_RECORD)),
    ('ExceptionAddress', ctypes.c_void_p), ('NumberParameters', wintypes.DWORD),
    ('ExceptionInformation', ctypes.c_void_p * 15)]


class EXCEPTION_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('ExceptionRecord', EXCEPTION_RECORD), ('dwFirstChance', wintypes.DWORD)]


class DEBUG_EVENT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [('Exception', EXCEPTION_DEBUG_INFO), ('raw', ctypes.c_byte * 160)]
    _fields_ = [('dwDebugEventCode', wintypes.DWORD), ('dwProcessId', wintypes.DWORD),
                ('dwThreadId', wintypes.DWORD), ('u', _U)]


CONTEXT_FULL = 0x00010007
CONTEXT_DEBUG_REGISTERS = 0x00010010


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
    time.sleep(1.0)
    p = subprocess.Popen([GAME, '/game', 'pg'], cwd=os.path.dirname(GAME))
    pid = p.pid
    print('pid=%d' % pid)
    # 尽早附加：立刻附加（不等渲染）
    time.sleep(0.5)
    if not k32.DebugActiveProcess(pid):
        print('附加失败', k32.GetLastError()); return
    h = k32.OpenProcess(PROCESS_ALL, False, pid)
    print('attached h=%s' % h)

    off = BREAK_VA - IMGBASE
    orig = rd(h, IMGBASE + off, 4)
    print('原字节 @%X = %s' % (BREAK_VA, orig.hex() if orig else None))
    wr(h, IMGBASE + off, b'\xcc')

    log = open(os.path.join(OUT, 'stack.log'), 'w', encoding='utf-8')
    hits = 0
    t0 = time.time()
    de = DEBUG_EVENT()
    while time.time() - t0 < 60 and hits < 10:
        if not k32.WaitForDebugEvent(ctypes.byref(de), 1000):
            continue
        code = de.dwDebugEventCode
        cont = DBG_CONTINUE
        if code == 1:
            er = de.u.Exception.ExceptionRecord
            ec = er.ExceptionCode
            ea = er.ExceptionAddress or 0
            if ec == EXCEPTION_BREAKPOINT and abs(ea - (IMGBASE + off)) < 4:
                th = k32.OpenThread(THREAD_ALL, False, de.dwThreadId)
                ctx = CONTEXT()
                ctx.ContextFlags = CONTEXT_FULL
                k32.GetThreadContext(th, ctypes.byref(ctx))
                esp = ctx.Esp
                log.write('\n=== HIT#%d @%X esp=%08X eax(length)=%d(0x%X) esi=%08X ===\n'
                          % (hits, ea, esp, ctx.Eax, ctx.Eax, ctx.Esi))
                # 栈上 4 个参数（call 前已 push 0, eax, ecx, edx）
                st = rd(h, esp, 0x20)
                if st:
                    for k in range(8):
                        v = u32(st, k * 4)
                        log.write('  [esp+%#04x] = %08X (%d)\n' % (k * 4, v, v))
                # [esp+4] 是即将 push 的 utf8bytes（0x4016B4 push ecx 且 ecx=[esp+4]）
                p_utf8 = u32(st, 4)
                p_elem = u32(st, 0x8C)
                log.write('  utf8数据指针 = %08X\n' % (p_utf8 or 0))
                log.write('  hElem       = %08X\n' % (p_elem or 0))
                if p_utf8 and 0x10000 < p_utf8 < 0x7FFFFFFF:
                    d = rd(h, p_utf8, 0x200)
                    if d:
                        z = d.find(b'\x00')
                        s = d[:z] if z >= 0 else d
                        log.write('  该指针处内容(%d 字节到\\0):\n' % len(s))
                        log.write('    %s\n' % s[:300].decode('utf-8', 'replace'))
                k32.CloseHandle(th)
                hits += 1
                if hits >= 10:
                    k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, cont)
                    break
            elif ec == EXCEPTION_SINGLE_STEP:
                pass
            else:
                cont = DBG_EXCEPTION_NOT_HANDLED
        k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, cont)

    log.write('\nhits=%d\n' % hits)
    log.close()
    print('-> stack.log hits=%d' % hits)
    k32.DebugActiveProcessStop(pid)


main()
