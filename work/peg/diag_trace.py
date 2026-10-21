# -*- coding: utf-8 -*-
"""diag_trace.py — 运行时追踪器（最小写入）

在 32 位目标进程（默认等 PeG030.exe）的指定地址放 INT3 断点，命中的瞬间记录：
返回地址（栈顶）、EIP/ESP/EBP 与通用寄存器，然后恢复原字节继续跑。

- 只改每个断点处的 1 个字节（0xCC <-> 原字节），退出时恢复原状
- 64 位 Python 追踪 32 位进程，用 Wow64GetThreadContext / Wow64SetThreadContext
- 日志：work/peg/out/trace.log

用法：
  python work/peg/diag_trace.py --wait PeG030.exe --bp 410E66 --bp 43D680 --bp 455CA8
  python work/peg/diag_trace.py --pid 1234 --bp 410E66 --max 40
  python work/peg/diag_trace.py --selftest
"""
import ctypes
import ctypes.wintypes as wt
import os
import struct
import subprocess
import sys
import time

NL = chr(10)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "trace.log")

k32 = ctypes.WinDLL("kernel32", use_last_error=True)

PROCESS_ALL_ACCESS = 0x1F0FFF
THREAD_ALL_ACCESS = 0x1F03FF
TH32CS_SNAPPROCESS = 0x2

DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001

EXCEPTION_DEBUG_EVENT = 1
CREATE_THREAD_DEBUG_EVENT = 2
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_THREAD_DEBUG_EVENT = 4
EXIT_PROCESS_DEBUG_EVENT = 5
LOAD_DLL_DEBUG_EVENT = 6

EXCEPTION_BREAKPOINT = 0x80000003
EXCEPTION_SINGLE_STEP = 0x80000004

CONTEXT_FULL = 0x00010007
CONTEXT_ALL = 0x0001003F

# DEBUG_EVENT 内固定偏移。注意：本工具是 64 位 Python，DEBUG_EVENT 里的
# EXCEPTION_RECORD 按 64 位布局（指针 8 字节），所以 ExceptionAddress 在 28、
# dwFirstChance 在 164；早先误用 32 位偏移（24/92），会把 first-chance 读成 0。
OFF_EVENT_CODE = 0
OFF_PID = 4
OFF_TID = 8
OFF_EXC_CODE = 12
OFF_EXC_ADDR = 28
OFF_EXC_FIRST = 164


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.c_void_p), ("th32ModuleID", wt.DWORD),
                ("cntThreads", wt.DWORD), ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", ctypes.c_char * 260)]


class FLOATING_SAVE_AREA(ctypes.Structure):
    _fields_ = [("ControlWord", wt.DWORD), ("StatusWord", wt.DWORD), ("TagWord", wt.DWORD),
                ("ErrorOffset", wt.DWORD), ("ErrorSelector", wt.DWORD), ("DataOffset", wt.DWORD),
                ("DataSelector", wt.DWORD), ("RegisterArea", ctypes.c_ubyte * 80),
                ("Cr0NpxState", wt.DWORD)]


class CONTEXT(ctypes.Structure):
    _fields_ = [("ContextFlags", wt.DWORD),
                ("Dr0", wt.DWORD), ("Dr1", wt.DWORD), ("Dr2", wt.DWORD), ("Dr3", wt.DWORD),
                ("Dr6", wt.DWORD), ("Dr7", wt.DWORD),
                ("FloatSave", FLOATING_SAVE_AREA),
                ("SegGs", wt.DWORD), ("SegFs", wt.DWORD), ("SegEs", wt.DWORD), ("SegDs", wt.DWORD),
                ("Edi", wt.DWORD), ("Esi", wt.DWORD), ("Ebx", wt.DWORD), ("Edx", wt.DWORD),
                ("Ecx", wt.DWORD), ("Eax", wt.DWORD),
                ("Ebp", wt.DWORD), ("Eip", wt.DWORD), ("SegCs", wt.DWORD), ("EFlags", wt.DWORD),
                ("Esp", wt.DWORD), ("SegSs", wt.DWORD),
                ("ExtendedRegisters", ctypes.c_ubyte * 512)]


def u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


def log(msg, echo=True):
    line = msg
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(line + NL)
    if echo:
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode("gbk", "replace").decode("gbk"))


def find_pid(name):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap in (0, -1):
        return None
    e = PROCESSENTRY32()
    e.dwSize = ctypes.sizeof(PROCESSENTRY32)
    ok = k32.Process32First(snap, ctypes.byref(e))
    found = None
    while ok:
        exe = e.szExeFile.decode("latin1", "replace")
        if exe.lower() == name.lower():
            found = e.th32ProcessID
            break
        ok = k32.Process32Next(snap, ctypes.byref(e))
    k32.CloseHandle(snap)
    return found


class Tracer(object):
    def __init__(self, pid, bps, maxhits):
        self.pid = pid
        self.bps = {}
        self.orig = {}
        self.maxhits = maxhits
        self.hits = {}
        self.pending = {}
        self.threads = {}
        self.probed = False
        self.h = k32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed: %d" % ctypes.get_last_error())
        for a in bps:
            self.bps[a] = 0

    def rpm(self, addr, n):
        buf = ctypes.create_string_buffer(n)
        read = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(self.h, ctypes.c_void_p(addr), buf, n, ctypes.byref(read)):
            return None
        return buf.raw[:read.value]

    def wpm(self, addr, data):
        n = len(data)
        written = ctypes.c_size_t(0)
        return bool(k32.WriteProcessMemory(self.h, ctypes.c_void_p(addr), data, n, ctypes.byref(written)))

    def arm(self, addr):
        cur = self.rpm(addr, 1)
        if not cur:
            log("! 无法读取 0x%08X" % addr)
            return False
        self.orig[addr] = cur
        if not self.wpm(addr, bytes([0xCC])):
            log("! 无法写断点 0x%08X" % addr)
            return False
        return True

    def disarm(self, addr):
        if addr in self.orig:
            self.wpm(addr, self.orig[addr])

    def arm_all(self):
        for addr in list(self.bps):
            if self.arm(addr):
                log("· 断点已置 0x%08X（原字节 %s）" % (addr, self.orig[addr].hex(" ")))

    def restore_all(self):
        for addr in list(self.orig):
            self.disarm(addr)
        log("· 已恢复全部原字节")

    def thread_handle(self, tid):
        if tid not in self.threads:
            h = k32.OpenThread(THREAD_ALL_ACCESS, False, tid)
            self.threads[tid] = h
        return self.threads[tid]

    def get_ctx(self, tid):
        h = self.thread_handle(tid)
        if not h:
            return None
        c = CONTEXT()
        c.ContextFlags = CONTEXT_ALL
        fn = k32.Wow64GetThreadContext
        if not fn(h, ctypes.byref(c)):
            return None
        return c

    def set_ctx(self, tid, c):
        h = self.thread_handle(tid)
        if not h:
            return False
        c.ContextFlags = CONTEXT_ALL
        return bool(k32.Wow64SetThreadContext(h, ctypes.byref(c)))

    def handle_exception(self, buf, tid):
        code = u32(buf, OFF_EXC_CODE)
        addr = u32(buf, OFF_EXC_ADDR)
        first = u32(buf, OFF_EXC_FIRST)

        if code == EXCEPTION_SINGLE_STEP and tid in self.pending:
            addr0 = self.pending.pop(tid)
            self.wpm(addr0, bytes([0xCC]))
            c = self.get_ctx(tid)
            if c is not None:
                c.EFlags &= 0xFFFFFEFF
                self.set_ctx(tid, c)
            return DBG_CONTINUE

        if code == EXCEPTION_BREAKPOINT:
            if addr in self.bps:
                c = self.get_ctx(tid)
                esp = c.Esp if c else 0
                retv = self.rpm(esp, 4) if esp else None
                ret = struct.unpack("<I", retv)[0] if retv else 0
                self.hits[addr] = self.hits.get(addr, 0) + 1
                n = self.hits[addr]
                if n <= self.maxhits or n in (100, 500, 1000):
                    log("HIT 0x%08X #%d tid=%d ret=0x%08X eax=0x%08X ecx=0x%08X edx=0x%08X "
                        "ebx=0x%08X esi=0x%08X edi=0x%08X ebp=0x%08X esp=0x%08X" %
                        (addr, n, tid, ret, c.Eax, c.Ecx, c.Edx, c.Ebx, c.Esi, c.Edi, c.Ebp, esp))
                if self.orig.get(addr):
                    self.wpm(addr, self.orig[addr])
                c2 = self.get_ctx(tid)
                if c2 is not None:
                    c2.Eip = addr
                    c2.EFlags |= 0x00000100
                    self.set_ctx(tid, c2)
                    self.pending[tid] = addr
                if n >= self.maxhits * 8:
                    self.disarm(addr)
                    self.bps.pop(addr, None)
            return DBG_CONTINUE

        if first:
            return DBG_CONTINUE
        log("EXC code=0x%08X addr=0x%08X tid=%d（second chance，交回进程）" % (code, addr, tid))
        return DBG_EXCEPTION_NOT_HANDLED

    def loop(self, seconds=0):
        buf = ctypes.create_string_buffer(256)
        t0 = time.time()
        while True:
            if seconds and time.time() - t0 > seconds:
                log("· 到时间上限，退出追踪")
                break
            ok = k32.WaitForDebugEvent(ctypes.byref(buf), 200)
            if not ok:
                if self.pid and not k32.GetExitCodeProcess(self.h, ctypes.byref(wt.DWORD())):
                    pass
                continue
            code = u32(buf.raw, OFF_EVENT_CODE)
            tid = u32(buf.raw, OFF_TID)
            pid = u32(buf.raw, OFF_PID)
            if not self.probed and tid:
                self.probed = True
                c = self.get_ctx(tid)
                if c is None:
                    log("! Wow64GetThreadContext 失败 tid=%d err=%d" % (tid, ctypes.get_last_error()))
                else:
                    log("· 目标线程上下文可用 tid=%d eip=0x%08X esp=0x%08X" % (tid, c.Eip, c.Esp))
            self.dbg = False
            if code == EXCEPTION_DEBUG_EVENT:
                cont = self.handle_exception(buf.raw, tid)
            elif code == EXIT_PROCESS_DEBUG_EVENT:
                log("· 目标进程已退出（pid=%d）" % pid)
                k32.ContinueDebugEvent(pid, tid, DBG_CONTINUE)
                break
            elif code in (CREATE_PROCESS_DEBUG_EVENT, LOAD_DLL_DEBUG_EVENT):
                cont = DBG_CONTINUE
            else:
                cont = DBG_CONTINUE
            k32.ContinueDebugEvent(pid, tid, cont)

    def run(self, seconds=0):
        if not k32.DebugActiveProcess(self.pid):
            raise OSError("DebugActiveProcess failed: %d" % ctypes.get_last_error())
        log("=== 已附加到 pid=%d ===" % self.pid)
        log("（若无 HIT 行，说明该地址没被执行；若进程立即退出，可能是反调试或崩溃）")
        self.arm_all()
        try:
            self.loop(seconds)
        finally:
            self.restore_all()
            k32.DebugActiveProcessStop(self.pid)
            log("=== 已脱离 pid=%d ===" % self.pid)
        for a, n in sorted(self.hits.items()):
            log("统计 0x%08X 命中 %d 次" % (a, n))


def selftest():
    log("=== selftest：附加到一个无害子进程，验证事件/读写/脱离 ===", echo=True)
    p = subprocess.Popen(["cmd", "/c", "ping -n 6 127.0.0.1 >nul"], shell=False)
    time.sleep(0.6)
    pid = p.pid
    h = k32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    log("子进程 pid=%d handle=%s" % (pid, bool(h)))
    if not k32.DebugActiveProcess(pid):
        log("DebugActiveProcess 失败: %d" % ctypes.get_last_error())
        return False
    k32.DebugActiveProcessStop(pid)
    log("附加/脱离 ✓")
    k32.CloseHandle(h)
    p.wait()
    return True


def main():
    args = sys.argv[1:]
    waitname = None
    pid = None
    bps = []
    maxhits = 30
    seconds = 0
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--wait":
            i += 1
            waitname = args[i]
        elif a == "--pid":
            i += 1
            pid = int(args[i])
        elif a == "--bp":
            i += 1
            bps.append(int(args[i], 16))
        elif a == "--max":
            i += 1
            maxhits = int(args[i])
        elif a == "--seconds":
            i += 1
            seconds = int(args[i])
        elif a == "--selftest":
            return 0 if selftest() else 1
        i += 1

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    log("=== diag_trace 启动 %s ===" % time.strftime("%Y-%m-%d %H:%M:%S"))

    if pid is None:
        if not waitname:
            print("需要 --wait NAME 或 --pid N（或 --selftest）")
            return 2
        log("等待进程 %s ..." % waitname)
        last = 0
        while True:
            pid = find_pid(waitname)
            if pid:
                log("发现 %s pid=%d" % (waitname, pid))
                break
            if time.time() - last > 10:
                last = time.time()
                log("  仍在等待 %s ..." % waitname, echo=False)
            time.sleep(0.4)

    tr = Tracer(pid, bps, maxhits)
    tr.run(seconds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
