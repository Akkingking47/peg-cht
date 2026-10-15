# -*- coding: utf-8 -*-
r"""
附加式调试器 v2：正确解析 DEBUG_EVENT，在 0x4016A0（HTMLayoutSetElementHtml 调用前
读取长度字段）以及 0x401680 入口下断，读出：
  - this 指针 (ecx/esi)
  - [this+4] = HTML 数据指针
  - [dataptr-0xC] = std::string::length  ← 关键
  - [dataptr-4]  = capacity
  - 数据前若干字节（UTF-8 解码）
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
IMGBASE = 0x400000

# 0x4016A0: mov edx, [esi+4]   ← esi 已 = this
BREAK_VA = 0x4016A0


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
        _fields_ = [('Exception', EXCEPTION_DEBUG_INFO),
                    ('raw', ctypes.c_byte * 160)]
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
    if addr <= 0 or addr > 0x7FFFFFFF:
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
    print('started pid=%d, 等待渲染...' % pid)
    time.sleep(8.0)

    if not k32.DebugActiveProcess(pid):
        print('DebugActiveProcess 失败', k32.GetLastError())
        return
    h = k32.OpenProcess(PROCESS_ALL, False, pid)
    print('attached h=%s' % h)

    off = BREAK_VA - IMGBASE
    orig = rd(h, IMGBASE + off, 8)
    print('原字节 @%X = %s' % (IMGBASE + off, orig.hex() if orig else None))
    if orig and orig[0] != 0xCC:
        wr(h, IMGBASE + off, b'\xcc')
    print('bp @%X' % (IMGBASE + off))

    log = open(os.path.join(OUT, 'attach2.log'), 'w', encoding='utf-8')
    log.write('BREAK_VA=%X orig=%s\n' % (BREAK_VA, orig.hex() if orig else '?'))
    hits = 0
    t0 = time.time()
    de = DEBUG_EVENT()
    while time.time() - t0 < 70:
        if not k32.WaitForDebugEvent(ctypes.byref(de), 1000):
            continue
        code = de.dwDebugEventCode
        cont = DBG_CONTINUE
        if code == 1:
            er = de.u.Exception.ExceptionRecord
            ec = er.ExceptionCode
            ea = er.ExceptionAddress or 0
            if ec == EXCEPTION_BREAKPOINT:
                if abs(ea - (IMGBASE + off)) < 4:
                    th = k32.OpenThread(THREAD_ALL, False, de.dwThreadId)
                    ctx = CONTEXT()
                    ctx.ContextFlags = CONTEXT_FULL
                    k32.GetThreadContext(th, ctypes.byref(ctx))
                    log.write('\n=== HIT#%d @%X ecx=%08X esi=%08X eax=%08X ebx=%08X edx=%08X ===\n'
                              % (hits, ea, ctx.Ecx, ctx.Esi, ctx.Eax, ctx.Ebx, ctx.Edx))
                    # 0x401680 的 this 在 ecx（0x401687 mov esi,ecx）
                    this = ctx.Ecx if ctx.Esi == 0 else ctx.Esi
                    # 0x4016A0 处 esi 已 = this
                    this = ctx.Esi
                    p4 = rd(h, this + 4, 4)
                    dataptr = u32(p4)
                    log.write('this=%08X  [this+4](dataptr)=%08X\n' % (this, dataptr or 0))
                    if dataptr:
                        L = u32(rd(h, dataptr - 0xC, 4))
                        C = u32(rd(h, dataptr - 8, 4))
                        log.write('  [dataptr-0xC] = %s   <- std::wstring?/string? length\n' % L)
                        log.write('  [dataptr-0x8] = %s   <- capacity\n' % C)
                        hdr = rd(h, dataptr - 0x10, 0x10)
                        log.write('  hdr(-0x10..0) = %s\n' % (hdr.hex() if hdr else '?'))
                        d = rd(h, dataptr, 0x300)
                        if d:
                            z = d.find(b'\x00')
                            s = d[:z] if z >= 0 else d
                            log.write('  字节数(到\\0)=%d\n' % len(s))
                            try:
                                log.write('  UTF-8字符数=%d\n' % len(s.decode('utf-8')))
                            except Exception as e:
                                log.write('  UTF-8解码失败 %s\n' % e)
                            log.write('  内容[0:400]: %s\n' % s[:400].decode('utf-8', 'replace'))
                    k32.CloseHandle(th)
                    hits += 1
                    if hits >= 20:
                        k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, cont)
                        break
                else:
                    log.write('bp @%X (非目标)\n' % ea)
            else:
                cont = DBG_EXCEPTION_NOT_HANDLED
        k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, cont)
    log.write('\nhits=%d\n' % hits)
    log.close()
    print('-> attach2.log hits=%d' % hits)
    k32.DebugActiveProcessStop(pid)


main()
