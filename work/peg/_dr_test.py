# -*- coding: utf-8 -*-
"""临时诊断：验证 WOW64 线程上 Dr 硬件执行断点是否真的会触发。
做法：在被调试进程第一次断点异常处，把 Dr0 指向「下一条将要执行的指令」，继续，
      如果 Dr 生效就会立刻收到 EXCEPTION_SINGLE_STEP。两种写入方式各测一次。"""
import ctypes
import struct
import sys

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
import os
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


sys.path.insert(0, os.path.join(WS, "work", "peg"))
import peg_launcher as PL  # noqa: E402

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
DEBUG_ONLY_THIS_PROCESS = 0x00000002
CREATE_NO_WINDOW = 0x08000000
CONTEXT_FULL32 = 0x00010007
CONTEXT_AMD64 = 0x00100007
EXE = r"C:\Windows\SysWOW64\hostname.exe"

OFF_HPROC, OFF_HTHREAD, OFF_BASE = 24, 32, 40
OFF_EXCODE, OFF_EXADDR = 16, 32
C32_EIP, C64_RIP, C64_FLAGS, C64_DR0, C64_DR7 = 0xB8, 0xF8, 0x30, 0x48, 0x70


def ptr(buf, off):
    return int.from_bytes(buf[off:off + 8], "little")


def mix_marked(tag):
    print("  [%s]" % tag)


si = PL.STARTUPINFOW()
si.cb = ctypes.sizeof(si)
pi = PL.PROCESS_INFORMATION()
ok = k32.CreateProcessW(ctypes.c_wchar_p(EXE), None, None, None, False,
                        DEBUG_ONLY_THIS_PROCESS | CREATE_NO_WINDOW, None,
                        ctypes.c_wchar_p(r"C:\Windows\SysWOW64"),
                        ctypes.byref(si), ctypes.byref(pi))
print("CreateProcess:", bool(ok), "pid=", pi.dwProcessId)

de = ctypes.create_string_buffer(256)
mode = sys.argv[1] if len(sys.argv) > 1 else "wow64"
hp = hthread = None
for _ in range(200):
    if not k32.WaitForDebugEvent(de, 5000):
        print("超时")
        break
    code = struct.unpack_from("<I", de, 0)[0]
    pid, tid = struct.unpack_from("<I", de, 4)[0], struct.unpack_from("<I", de, 8)[0]
    if code == 3:                       # CREATE_PROCESS
        hp = ctypes.c_void_p(ptr(de, OFF_HPROC))
        hthread = ctypes.c_void_p(ptr(de, OFF_HTHREAD))
        base = ptr(de, OFF_BASE) & 0xFFFFFFFF
        print("CREATE_PROCESS base=%#x hproc=%s hthread=%s" % (base, hp.value, hthread.value))
        k32.ContinueDebugEvent(pid, tid, 0x00010002)
        continue
    if code == 1:                       # EXCEPTION
        ex = struct.unpack_from("<I", de, OFF_EXCODE)[0]
        if ex == 0x80000003:            # 第一次断点：把 Dr0 指向下一条指令
            ctx = ctypes.create_string_buffer(0x400)
            struct.pack_into("<I", ctx, 0, CONTEXT_FULL32)
            k32.Wow64GetThreadContext(hthread, ctx)
            eip = struct.unpack_from("<I", ctx, C32_EIP)[0]
            target = eip + 1
            print("断点异常 EIP=%#x → 把 Dr0 指向 %#x（方式：%s）" % (eip, target, mode))
            done = False
            if mode == "native":
                c64 = ctypes.create_string_buffer(0x4D0)
                struct.pack_into("<I", c64, C64_FLAGS, CONTEXT_AMD64)
                if k32.GetThreadContext(hthread, c64):
                    struct.pack_into("<Q", c64, C64_DR0, target)
                    struct.pack_into("<Q", c64, C64_DR7, 1)
                    struct.pack_into("<I", c64, C64_FLAGS, CONTEXT_AMD64)
                    done = bool(k32.SetThreadContext(hthread, c64))
                    print("  SetThreadContext(64):", done,
                          ctypes.WinError(ctypes.get_last_error()) if not done else "")
                else:
                    print("  GetThreadContext(64) 失败")
            else:
                struct.pack_into("<I", ctx, 0x04, target)      # Dr0
                struct.pack_into("<I", ctx, 0x18, 1)           # Dr7
                struct.pack_into("<I", ctx, 0x14, 0)           # Dr6
                done = bool(k32.Wow64SetThreadContext(hthread, ctx))
                print("  Wow64SetThreadContext:", done,
                      ctypes.WinError(ctypes.get_last_error()) if not done else "")
            k32.ContinueDebugEvent(pid, tid, 0x00010002)
            # 等 3 秒看有没有单步事件
            if k32.WaitForDebugEvent(de, 3000):
                code2 = struct.unpack_from("<I", de, 0)[0]
                ex2 = struct.unpack_from("<I", de, OFF_EXCODE)[0] if code2 == 1 else 0
                print("  → 下个事件 code=%d ex=%#x %s" % (
                    code2, ex2, "★ Dr 生效（单步命中）" if ex2 == 0x80000004 else "（不是单步）"))
                k32.ContinueDebugEvent(struct.unpack_from("<I", de, 4)[0],
                                       struct.unpack_from("<I", de, 8)[0], 0x00010002)
            else:
                print("  → 3 秒内没有任何调试事件（Dr 未生效）")
            break
    k32.ContinueDebugEvent(pid, tid, 0x00010002)
k32.TerminateProcess(ctypes.c_void_p(pi.hProcess), 0)
