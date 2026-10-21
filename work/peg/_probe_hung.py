# -*- coding: utf-8 -*-
"""只读探针：看某个 PeG030 进程卡在哪（不改目标进程任何字节）。
用法：python work\\peg\\_probe_hung.py <pid>
原理：CreateToolhelp32Snapshot 列线程 → Wow64GetThreadContext 取 EIP/ESP/EBP
（64 位 python 看 32 位目标必须用 Wow64 版）→ 反汇编 EIP 处代码 → 扫栈上的返回地址。
"""
import ctypes as C
import struct
import sys

k32 = C.WinDLL("kernel32", use_last_error=True)
# 句柄是 64 位指针：不声明 restype 会被截成 32 位（经典坑）
k32.OpenProcess.restype = C.c_void_p
k32.OpenProcess.argtypes = [C.c_uint32, C.c_int, C.c_uint32]
k32.CreateToolhelp32Snapshot.restype = C.c_void_p
k32.CreateToolhelp32Snapshot.argtypes = [C.c_uint32, C.c_uint32]
k32.OpenThread.restype = C.c_void_p
k32.OpenThread.argtypes = [C.c_uint32, C.c_int, C.c_uint32]
k32.ReadProcessMemory.restype = C.c_int
k32.ReadProcessMemory.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p, C.c_size_t,
                                  C.POINTER(C.c_size_t)]
TH32CS_SNAPTHREAD = 0x00000004
THREAD_SUSPEND_RESUME = 0x0002
THREAD_GET_CONTEXT = 0x0008
THREAD_QUERY_INFORMATION = 0x0040
THREAD_QUERY_LIMITED_INFORMATION = 0x0800
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01
WOW64_CONTEXT_FULL = 0x00010007
MODBASE = 0x400000
TEXTHI = 0x8B136


class THREADENTRY32(C.Structure):
    _fields_ = [("dwSize", C.c_uint32), ("cntUsage", C.c_uint32),
                ("th32ThreadID", C.c_uint32), ("th32OwnerProcessID", C.c_uint32),
                ("tpBasePri", C.c_int32), ("tpDeltaPri", C.c_int32),
                ("dwFlags", C.c_uint32)]


k32.Thread32First.argtypes = [C.c_void_p, C.POINTER(THREADENTRY32)]
k32.Thread32Next.argtypes = [C.c_void_p, C.POINTER(THREADENTRY32)]


class FLOATSAVE(C.Structure):
    _fields_ = [("ControlWord", C.c_uint32), ("StatusWord", C.c_uint32),
                ("TagWord", C.c_uint32), ("ErrorOffset", C.c_uint32),
                ("ErrorSelector", C.c_uint32), ("DataOffset", C.c_uint32),
                ("DataSelector", C.c_uint32), ("RegisterArea", C.c_ubyte * 80),
                ("Cr0NpxState", C.c_uint32)]


class WOW64CONTEXT(C.Structure):
    _fields_ = [("ContextFlags", C.c_uint32), ("Dr0", C.c_uint32), ("Dr1", C.c_uint32),
                ("Dr2", C.c_uint32), ("Dr3", C.c_uint32), ("Dr6", C.c_uint32),
                ("Dr7", C.c_uint32), ("FloatSave", FLOATSAVE),
                ("SegGs", C.c_uint32), ("SegFs", C.c_uint32), ("SegEs", C.c_uint32),
                ("SegDs", C.c_uint32), ("Edi", C.c_uint32), ("Esi", C.c_uint32),
                ("Ebx", C.c_uint32), ("Edx", C.c_uint32), ("Ecx", C.c_uint32),
                ("Eax", C.c_uint32), ("Ebp", C.c_uint32), ("Eip", C.c_uint32),
                ("SegCs", C.c_uint32), ("EFlags", C.c_uint32), ("Esp", C.c_uint32),
                ("SegSs", C.c_uint32), ("ExtendedRegisters", C.c_ubyte * 512)]


try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)
except Exception:
    md = None


def read(proc, addr, n):
    buf = C.create_string_buffer(n)
    got = C.c_size_t(0)
    if k32.ReadProcessMemory(proc, C.c_void_p(addr), buf, n, C.byref(got)):
        return buf.raw[:got.value]
    return None


def main(pid):
    proc = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not proc:
        print("OpenProcess 失败 err=%d" % C.get_last_error())
        return 1
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    te = THREADENTRY32()
    te.dwSize = C.sizeof(THREADENTRY32)
    tids = []
    if k32.Thread32First(snap, C.byref(te)):
        while True:
            if te.th32OwnerProcessID == pid:
                tids.append(te.th32ThreadID)
            if not k32.Thread32Next(snap, C.byref(te)):
                break
    k32.CloseHandle(snap)
    print("pid=%d 线程数=%d %s" % (pid, len(tids), tids))
    for tid in tids:
        h = k32.OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT
                           | THREAD_QUERY_INFORMATION | THREAD_QUERY_LIMITED_INFORMATION,
                           False, tid)
        if not h:
            print("  tid=%d OpenThread 失败 err=%d" % (tid, C.get_last_error()))
            continue
        k32.SuspendThread(h)
        ctx = WOW64CONTEXT()
        ctx.ContextFlags = WOW64_CONTEXT_FULL
        ok = k32.Wow64GetThreadContext(h, C.byref(ctx))
        if not ok:
            print("  tid=%d Wow64GetThreadContext 失败 err=%d" % (tid, C.get_last_error()))
            k32.ResumeThread(h)
            k32.CloseHandle(h)
            continue
        eip, esp, ebp = ctx.Eip, ctx.Esp, ctx.Ebp
        inside = "在PeG030.text" if MODBASE <= eip < MODBASE + TEXTHI else "不在游戏代码里"
        print("  tid=%d EIP=%08X (+%X %s) ESP=%08X EBP=%08X EAX=%08X EBX=%08X"
              % (tid, eip, eip - MODBASE, inside, esp, ebp, ctx.Eax, ctx.Ebx))
        code = read(proc, eip, 32)
        if code and md:
            print("    当前指令：")
            for ins in md.disasm(code, eip):
                print("      %08X  %-22s %s %s" % (ins.address, ins.bytes.hex(),
                                                   ins.mnemonic, ins.op_str))
                if ins.address - eip > 16:
                    break
        st = read(proc, esp, 4 * 24)
        if st:
            print("    栈顶 24 个字（★=落在 PeG030 .text）：")
            for i in range(0, len(st) - 3, 4):
                v = struct.unpack_from("<I", st, i)[0]
                mark = "★" if MODBASE <= v < MODBASE + TEXTHI else " "
                if i % 16 == 0:
                    print("      ", end="")
                print("%08X%s" % (v, mark), end=" ")
                if i % 16 == 12:
                    print()
            print()
        k32.ResumeThread(h)
        k32.CloseHandle(h)
    # 线程都不在自己代码里时：扫主线程栈上的返回地址
    k32.CloseHandle(proc)
    return 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1])))
