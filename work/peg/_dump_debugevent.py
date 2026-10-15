# -*- coding: utf-8 -*-
"""临时诊断：dump CREATE_PROCESS / EXCEPTION 调试事件的原始字节，确定字段偏移。
（64 位调试器 + 32 位被调试进程）"""
import ctypes
import struct
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import peg_launcher as PL  # noqa: E402

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
DEBUG_ONLY_THIS_PROCESS = 0x00000002
CREATE_NO_WINDOW = 0x08000000
EXE = r"C:\Windows\SysWOW64\cmd.exe"

pe = open(EXE, "rb").read()
e_lfanew = struct.unpack_from("<I", pe, 0x3C)[0]
entry_rva = struct.unpack_from("<I", pe, e_lfanew + 0x28)[0]

si = PL.STARTUPINFOW()
si.cb = ctypes.sizeof(si)
pi = PL.PROCESS_INFORMATION()
ok = k32.CreateProcessW(ctypes.c_wchar_p(EXE), None, None, None, False,
                        DEBUG_ONLY_THIS_PROCESS | CREATE_NO_WINDOW, None,
                        ctypes.c_wchar_p(r"C:\Windows\SysWOW64"),
                        ctypes.byref(si), ctypes.byref(pi))
print("CreateProcess:", ok, "pid=", pi.dwProcessId, "ptr=", ctypes.sizeof(ctypes.c_void_p))
print("entryRVA=%#x" % entry_rva)


def dump(de, tag):
    raw = de.raw[:96]
    print("\n%s：code=%d pid=%d tid=%d" % (
        tag, struct.unpack_from("<I", raw, 0)[0], struct.unpack_from("<I", raw, 4)[0],
        struct.unpack_from("<I", raw, 8)[0]))
    for i in range(0, 96, 16):
        dwords = " ".join("%08x" % struct.unpack_from("<I", raw, i + j)[0]
                          for j in range(0, 16, 4))
        print("  +%02x  %s   %s" % (i, raw[i:i + 16].hex(" "), dwords))


def ctx_of(tid):
    h = k32.OpenThread(0x001F03FF, False, tid)
    ctx = ctypes.create_string_buffer(0x400)
    struct.pack_into("<I", ctx, 0, 0x00010007)
    if not k32.Wow64GetThreadContext(ctypes.c_void_p(h), ctx):
        print("  ! Wow64GetThreadContext 失败：%s" % ctypes.WinError(ctypes.get_last_error()))
        return None, None, ctx
    return h, ctypes.c_void_p(h), ctx


de = ctypes.create_string_buffer(256)
stage = 1
entry = None
for _ in range(20):
    if not k32.WaitForDebugEvent(de, 4000):
        print("timeout")
        break
    code = struct.unpack_from("<I", de, 0)[0]
    pid = struct.unpack_from("<I", de, 4)[0]
    tid = struct.unpack_from("<I", de, 8)[0]
    dump(de, "事件")
    if code == 3:
        base = PL.wow64_peb_image_base(pi.hProcess)
        print("  PEB 取到基址 = %#x" % (base or 0))
        entry = (base or 0) + entry_rva
        h, hp, ctx = ctx_of(tid)
        if ctx and hp:
            struct.pack_into("<I", ctx, 0x04, entry)      # Dr0
            struct.pack_into("<I", ctx, 0x18, 1)          # Dr7 = L0, RW=00 执行
            struct.pack_into("<I", ctx, 0x14, 0)          # Dr6
            ok2 = k32.Wow64SetThreadContext(hp, ctx)
            print("  装执行监视点 @%#x -> %s" % (entry, ok2))
        stage = 2
    k32.ContinueDebugEvent(pid, tid, 0x00010002)
    if stage == 2 and code == 1:
        ex = struct.unpack_from("<I", de, 0x0C)[0]
        if ex == 0x80000004:
            h, hp, ctx = ctx_of(tid)
            if ctx and hp:
                dr6 = struct.unpack_from("<I", ctx, 0x14)[0]
                eip = struct.unpack_from("<I", ctx, 0xB8)[0]
                print("  Dr6=%#x EIP=%#x（期望 %#x）" % (dr6, eip, entry))
            break
k32.TerminateProcess(ctypes.c_void_p(pi.hProcess), 0)
