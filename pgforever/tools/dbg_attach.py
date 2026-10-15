# -*- coding: utf-8 -*-
r"""
附加式调试器：游戏正常启动（可正常渲染列表），随后 DebugActiveProcess 附加，
在 0x401680 下断点，读取 esi[4]（HTML 数据指针）与 [dataptr-0xC]（长度字段）。

关键：附加式调试不会阻止游戏正常跑完启动流程。
"""
import ctypes
import os
import struct
import subprocess
import time
from ctypes import wintypes

k32 = ctypes.windll.kernel32
user = ctypes.windll.user32
GAME = r'D:\PGForever1.021\PGForever.exe'
OUT = r'D:\DSH\军事游戏汉化\pgforever\poc\dbg'

DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_BREAKPOINT = 0x80000003
PROCESS_ALL = 0x1F0FFF
THREAD_ALL = 0x1F03FF
BREAK_VA = 0x401680
IMGBASE = 0x400000


class DEBUG_EVENT_HDR(ctypes.Structure):
    _fields_ = [('dwDebugEventCode', wintypes.DWORD), ('dwProcessId', wintypes.DWORD),
                ('dwThreadId', wintypes.DWORD)]


class EXCEPTION_RECORD(ctypes.Structure):
    pass


EXCEPTION_RECORD._fields_ = [
    ('ExceptionCode', wintypes.DWORD), ('ExceptionFlags', wintypes.DWORD),
    ('ExceptionRecord', ctypes.POINTER(EXCEPTION_RECORD)),
    ('ExceptionAddress', ctypes.c_void_p), ('NumberParameters', wintypes.DWORD),
    ('ExceptionInformation', ctypes.c_void_p * 15)]


class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [('dwDebugEventCode', wintypes.DWORD), ('dwProcessId', wintypes.DWORD),
                ('dwThreadId', wintypes.DWORD),
                ('pad', ctypes.c_byte * 160)]


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


def find_pid():
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq PGForever.exe', '/FO', 'CSV'],
                         capture_output=True, text=True)
    for line in out.stdout.splitlines():
        if 'PGForever' in line:
            return int(line.split('","')[1])
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    subprocess.run(['taskkill', '/F', '/IM', 'PGForever.exe'], capture_output=True)
    time.sleep(1.0)
    p = subprocess.Popen([GAME, '/game', 'pg'], cwd=os.path.dirname(GAME))
    # 让它正常启动渲染
    time.sleep(7.0)
    pid = p.pid
    print('pid=%d' % pid)

    if not k32.DebugActiveProcess(pid):
        print('DebugActiveProcess 失败', k32.GetLastError())
        return
    h = k32.OpenProcess(PROCESS_ALL, False, pid)
    print('attached, h=%s' % h)

    off = BREAK_VA - IMGBASE
    orig = rd(h, IMGBASE + off, 1)
    print('orig byte @%X = %s' % (IMGBASE + off, orig.hex() if orig else None))
    wr(h, IMGBASE + off, b'\xcc')
    print('bp set')

    log = open(os.path.join(OUT, 'attach.log'), 'w', encoding='utf-8')
    hits = 0
    t0 = time.time()
    de = DEBUG_EVENT()
    while time.time() - t0 < 60 and hits < 30:
        if not k32.WaitForDebugEvent(ctypes.byref(de), 1000):
            continue
        code = de.dwDebugEventCode
        cont = DBG_CONTINUE
        if code == 1:  # EXCEPTION_DEBUG_EVENT
            # 需要重新解析 union
            addr = de.pad
            er = ctypes.cast(ctypes.byref(de.pad), ctypes.POINTER(EXCEPTION_RECORD)).contents
            ec = er.ExceptionCode
            if ec == EXCEPTION_BREAKPOINT:
                ea = er.ExceptionAddress or 0
                if abs(ea - (IMGBASE + off)) < 8:
                    th = k32.OpenThread(THREAD_ALL, False, de.dwThreadId)
                    ctx = CONTEXT()
                    ctx.ContextFlags = CONTEXT_FULL
                    k32.GetThreadContext(th, ctypes.byref(ctx))
                    # 0x401680 尚未执行，此时 esi 尚未赋值；读 [esp+4] 的返回值
                    # 我们改在 0x4016A0（mov edx,[esi+4]）下断更准 —— 但现在先记录
                    log.write('HIT#%d @%X esi=%08X esp=%08X\n'
                              % (hits, ea, ctx.Esi, ctx.Esp))
                    # 读 0x401680 的调用者，反推参数
                    args = rd(h, ctx.Esp, 0x20)
                    log.write('  stack@esp = %s\n' % (args.hex() if args else '?'))
                    k32.CloseHandle(th)
                    hits += 1
                else:
                    log.write('bp @%X\n' % ea)
            else:
                cont = DBG_EXCEPTION_NOT_HANDLED
                log.write('exc %08X @%X\n' % (ec, er.ExceptionAddress or 0))
        k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, cont)

    log.write('\nhits=%d\n' % hits)
    log.close()
    print('->', os.path.join(OUT, 'attach.log'), 'hits=', hits)
    k32.DebugActiveProcessStop(pid)


main()
