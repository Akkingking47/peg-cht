# -*- coding: utf-8 -*-
"""P0：PeG 运行时几何/输入 trace（**只记录，不改写**）—— 宽屏方案 L3/L4 的取证工具。

做法：`CreateProcessW(DEBUG_ONLY_THIS_PROCESS)` 接管 32 位游戏进程（母本 exe 一个字节不动）：
  * 用与 `peg_launcher.py` 完全相同的「先校验、再写入、回读」流程打上 236 条尺寸站点（可用 --no-patches 关）；
  * 在几何/输入关键函数入口写 `0xCC`（INT3）断点 → 命中时读栈上实参 + 返回地址 + 全局状态快照，写进日志，单步后自动重新下断；
  * 用 Dr0–Dr3 **硬件写监视点**盯住视口/滚动全局，谁写它们就报出 EIP（这是 L4「鼠标→格子换算」取证的关键）。

用法：
  python peg_trace.py --exe "D:\\Program Files\\PeG\\PeG030.exe" --w 1920 --h 1080 --patches
  python peg_trace.py --selftest-debug          # 用 32 位测试进程自测调试循环（不碰游戏）

注意：本工具在运行期间**必须保持窗口不关**（调试器退出＝被调试进程被杀）。
"""
import argparse
import ctypes
import hashlib
import os
import struct
import sys
import time
from ctypes import wintypes

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
sys.path.insert(0, HERE)

import peg_launcher as PL          # noqa: E402  复用补丁计划/PE 工具/Tee

k32 = ctypes.WinDLL("kernel32", use_last_error=True)

# ---------------------------------------------------------------- Win32 常量
DEBUG_ONLY_THIS_PROCESS = 0x00000002
CREATE_NO_WINDOW = 0x08000000
EXCEPTION_DEBUG_EVENT = 1
CREATE_THREAD_DEBUG_EVENT = 2
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_THREAD_DEBUG_EVENT = 4
EXIT_PROCESS_DEBUG_EVENT = 5
LOAD_DLL_DEBUG_EVENT = 6
UNLOAD_DLL_DEBUG_EVENT = 7
OUTPUT_DEBUG_STRING_EVENT = 8
EXCEPTION_BREAKPOINT = 0x80000003
EXCEPTION_SINGLE_STEP = 0x80000004
# 64 位调试器观察 32 位(WOW64)被调试进程时，软件/硬件断点用的是这两个码：
STATUS_WX86_BREAKPOINT = 0x4000001F
STATUS_WX86_SINGLE_STEP = 0x4000001E
BP_CODES = (EXCEPTION_BREAKPOINT, STATUS_WX86_BREAKPOINT)
SS_CODES = (EXCEPTION_SINGLE_STEP, STATUS_WX86_SINGLE_STEP)
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
CONTEXT_FULL = 0x00010007          # i386 | CONTROL | INTEGER | SEGMENTS
PAGE_EXECUTE_READWRITE = 0x40

# WOW64_CONTEXT（x86 CONTEXT）字段偏移
C_DR0, C_DR1, C_DR2, C_DR3, C_DR6, C_DR7 = 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18
C_EAX, C_EBP, C_EIP, C_EFLAGS, C_ESP = 0xB0, 0xB4, 0xB8, 0xC0, 0xC4
CTX_SIZE = 0x400

# 原生 64 位 CONTEXT 里的 DR 偏移（winnt.h：ContextFlags@0x30, Dr0@0x48, Dr6@0x68, Dr7@0x70）
CONTEXT_AMD64 = 0x00100007
C64_FLAGS, C64_DR0, C64_DR6, C64_DR7 = 0x30, 0x48, 0x68, 0x70

# DEBUG_EVENT 的内嵌结构宽度取决于**调试器**位数（不是被调试进程）：
#   64 位调试器 → HANDLE/LPVOID 都是 8 字节
# 偏移由 work\peg\_dump_debugevent.py 实测（64 位 Python 调试 32 位 cmd.exe）：
#   事件头 12 字节 + 4 字节对齐填充 → 联合体从 +0x10 开始（64 位调试器）
#   CREATE_PROCESS: hProcess@0x18 hThread@0x20 lpBaseOfImage@0x28 lpStartAddress@0x40
#   LOAD_DLL:       hFile@0x10  lpBaseOfDll@0x18
#   EXCEPTION:      ExceptionCode@0x10 ExceptionAddress@0x20
PTR = ctypes.sizeof(ctypes.c_void_p)
if PTR == 8:
    OFF_HFILE, OFF_HPROC, OFF_HTHREAD, OFF_BASE = 16, 24, 32, 40
    OFF_EXCODE, OFF_EXADDR = 16, 32
else:
    OFF_HFILE, OFF_HPROC, OFF_HTHREAD, OFF_BASE = 12, 16, 20, 24
    OFF_EXCODE, OFF_EXADDR = 12, 24


def _ptr(buf, off):
    """按调试器位宽读一个句柄/指针。"""
    return int.from_bytes(buf[off:off + PTR], "little")

# ---------------------------------------------------------------- 断点表
# (VA, 名称, 参数个数)  —— 参数按 stdcall 从 [esp+4] 起
POINT_CAP = 24          # 单个断点最多记录多少次命中（到顶即撤掉断点，防热点拖慢游戏）
POINTS = [
    (0x41EB70, "位块助手 helper", 6),      # x, y, srcSurface, RECT*, color, flags
    (0x424C73, "视口设置器", 5),            # left, top, right, bottom, flag
    (0x43CDCE, "屏幕→地图坐标(战斗图)", 2),  # screenX, screenY  （返回值 al=是否在图内）
    (0x44B1D7, "战略图坐标映射", 4),
    (0x41C342, "视口右边界计算", 2),
    (0x41FF8A, "视口窗口→后备", 6),
    (0x4700C6, "文本排版(唯一文本路径)", 4),  # text, x, y, flags…
    (0x448E94, "选格判定", 2),
]

# 全局状态快照（名字, VA, 字节数）
STATE_GLOBALS = [
    ("mouseX", 0x4AF2E8, 2), ("mouseY", 0x4AF2EC, 2),
    ("scrollX", 0x4AF2F8, 4), ("scrollY", 0x4AF2FC, 4),
    ("vpLeft", 0x4AF300, 4),
    ("vpTop", 0x498D3C, 4), ("vpRight", 0x498D40, 4), ("vpBottom", 0x498D44, 4),
    ("tipL", 0x6769A0, 4), ("tipT", 0x6769A4, 4),
]

# 默认硬件写监视点（最多 4 个）。实测本机（WOW64 + 64 位调试器）Dr 不可用，
# 故默认留空；保留机制与 --watch 参数备用。
WATCH_DEFAULT = []


def _u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


# ---------------------------------------------------------------- 调试器
class Tracer(object):
    def __init__(self, exe, cwd, w, h, patches, no_patches, points, watch,
                 logpath, cap):
        self.exe, self.cwd, self.w, self.h = exe, cwd, w, h
        self.patches, self.no_patches = patches, no_patches
        self.points = list(points)
        self.watch = list(watch)[:4]
        self.cap = cap
        self.logpath = logpath
        self.hp = None
        self.main_tid = None
        self.main_thread = None
        self.base = None
        self.bp = {}            # va -> {"orig": bytearray|None, "label": str}
        self.stepping = set()   # tid 正在单步
        self.agg = {}           # key -> [count, sample]
        self.n_events = 0
        self.t0 = time.time()
        self.last_flush = 0.0
        self.entries = None
        self.hits = {}          # va -> 命中次数

    # ---------------- 日志
    def log(self, line):
        try:
            with open(self.logpath, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            print(line)

    def agg_add(self, key, sample):
        rec = self.agg.get(key)
        if rec is None:
            if len(self.agg) < self.cap:
                self.agg[key] = [1, sample]
            else:
                self.agg[key] = [1, sample]
        else:
            rec[0] += 1

    def flush(self, force=False):
        now = time.time()
        if not force and now - self.last_flush < 3.0:
            return
        self.last_flush = now
        if not self.agg:
            return
        items = sorted(self.agg.items(), key=lambda kv: -kv[1][0])
        with open(self.logpath, "a", encoding="utf-8") as f:
            f.write("\n---- 汇总（%s，事件 %d）----\n" % (
                time.strftime("%H:%M:%S"), self.n_events))
            for key, (cnt, sample) in items:
                f.write("  x%-6d %s\n" % (cnt, sample))
        self.agg = {}

    # ---------------- 目标进程内存
    def rpm(self, addr, size):
        buf = ctypes.create_string_buffer(size)
        n = ctypes.c_size_t()
        if not k32.ReadProcessMemory(self.hp, ctypes.c_void_p(addr), buf, size,
                                     ctypes.byref(n)) or n.value != size:
            return None
        return buf.raw[:size]

    def wpm(self, addr, data):
        old = wintypes.DWORD()
        k32.VirtualProtectEx(self.hp, ctypes.c_void_p(addr), len(data),
                             PAGE_EXECUTE_READWRITE, ctypes.byref(old))
        n = ctypes.c_size_t()
        ok = k32.WriteProcessMemory(self.hp, ctypes.c_void_p(addr), data,
                                    len(data), ctypes.byref(n)) and n.value == len(data)
        k32.VirtualProtectEx(self.hp, ctypes.c_void_p(addr), len(data),
                             old.value, ctypes.byref(wintypes.DWORD()))
        return ok

    def u32(self, addr):
        b = self.rpm(addr, 4)
        return _u32(b, 0) if b else None

    def state(self):
        out = []
        for name, va, size in STATE_GLOBALS:
            b = self.rpm(va, size)
            if b is None:
                out.append("%s=?" % name)
            else:
                v = int.from_bytes(b, "little")
                out.append("%s=%d" % (name, v))
        return " ".join(out)

    # ---------------- 线程上下文
    def get_ctx(self, hthread):
        ctx = ctypes.create_string_buffer(CTX_SIZE)
        struct.pack_into("<I", ctx, 0, CONTEXT_FULL)
        if not k32.Wow64GetThreadContext(hthread, ctx):
            return None
        return ctx

    def set_ctx(self, hthread, ctx):
        struct.pack_into("<I", ctx, 0, CONTEXT_FULL)
        return bool(k32.Wow64SetThreadContext(hthread, ctx))

    def reg(self, ctx, off):
        return struct.unpack_from("<I", ctx, off)[0]

    def set_reg(self, ctx, off, val):
        struct.pack_into("<I", ctx, off, val)

    # ---------------- 断点
    def plant(self, va, label):
        addr = va + (self.base - PL.IMAGE_BASE)
        orig = self.rpm(addr, 1)
        if orig is None:
            self.log("  ! 下断失败（读不到）%#x" % va)
            return False
        if orig == b"\xcc":
            self.log("  ! %#x 已是 0xCC" % va)
        if not self.wpm(addr, b"\xcc"):
            self.log("  ! 下断失败（写入）%#x" % va)
            return False
        self.bp[va] = {"orig": orig, "label": label}
        return True

    def unplant(self, va):
        rec = self.bp.get(va)
        if rec and rec["orig"]:
            self.wpm(va + (self.base - PL.IMAGE_BASE), rec["orig"])

    # ---------------- 硬件断点/监视点
    # 关键：64 位调试器 + WOW64 线程时，硬件断点寄存器写 **原生 64 位上下文**
    # 才真正生效（写 Wow64 上下文在多数系统上不会影响 CPU 的 DRx）。
    def write_drs(self, hthread, specs):
        """specs = [(槽位 0..3, 地址, 字节数或 0=执行)]；返回 True/False。"""
        try:
            if PTR == 8:
                ctx = ctypes.create_string_buffer(0x4D0)
                struct.pack_into("<I", ctx, C64_FLAGS, CONTEXT_AMD64)
                if not k32.GetThreadContext(hthread, ctx):
                    self.log("  ! GetThreadContext(64) 失败：%s" % ctypes.WinError(ctypes.get_last_error()))
                    return False
                for i, addr, size in specs:
                    struct.pack_into("<Q", ctx, C64_DR0 + 8 * i, addr)
                struct.pack_into("<Q", ctx, C64_DR7, self.dr7_value(specs))
                struct.pack_into("<Q", ctx, C64_DR6, 0)
                struct.pack_into("<I", ctx, C64_FLAGS, CONTEXT_AMD64)
                ok = bool(k32.SetThreadContext(hthread, ctx))
                if not ok:
                    self.log("  ! SetThreadContext(64) 失败：%s" % ctypes.WinError(ctypes.get_last_error()))
                return ok
            ctx = self.get_ctx(hthread)
            if ctx is None:
                return False
            for i, addr, size in specs:
                self.set_reg(ctx, C_DR0 + 4 * i, addr)
            self.set_reg(ctx, C_DR7, self.dr7_value(specs))
            self.set_reg(ctx, C_DR6, 0)
            return self.set_ctx(hthread, ctx)
        except Exception as exc:                            # noqa: BLE001
            self.log("  ! write_drs 异常：%r" % (exc,))
            return False

    @staticmethod
    def dr7_value(specs):
        dr7 = 0
        for i, addr, size in specs:
            dr7 |= (1 << (2 * i))                          # Ln 本线程启用
            if size:                                       # 数据断点：写 + 长度
                dr7 |= (0b01 << (16 + 4 * i))
                dr7 |= ({1: 0b00, 2: 0b01, 4: 0b11}.get(size, 0b11) << (18 + 4 * i))
        return dr7

    def read_drs(self, hthread):
        """返回 (Dr6, Dr7)；64 位调试器读原生上下文。"""
        try:
            if PTR == 8:
                ctx = ctypes.create_string_buffer(0x4D0)
                struct.pack_into("<I", ctx, C64_FLAGS, CONTEXT_AMD64)
                if not k32.GetThreadContext(hthread, ctx):
                    return 0, 0
                return (struct.unpack_from("<Q", ctx, C64_DR6)[0],
                        struct.unpack_from("<Q", ctx, C64_DR7)[0])
            ctx = self.get_ctx(hthread)
            if ctx is None:
                return 0, 0
            return self.reg(ctx, C_DR6), self.reg(ctx, C_DR7)
        except Exception:                                   # noqa: BLE001
            return 0, 0

    def arm_watch(self, hthread):
        if not self.watch:
            return
        # 实测（_dr_test.py + trace-selftest.txt，2026-10-14）：64 位调试器无法给
        # WOW64 线程设硬件断点——Wow64SetThreadContext 与原生 SetThreadContext 都
        # 返回成功，Dr 却不触发，且会破坏被调试线程（0xC0000005）。
        # 因此默认不用 Dr；靠 INT3 断点 + 周期性状态快照取证。
        self.log("  （硬件监视点跳过：WOW64 + 64 位调试器下 Dr 不可用）")
        return

    # ---------------- 补丁
    def apply_patches(self):
        if self.no_patches:
            self.log("  （--no-patches：不打任何尺寸补丁）")
            return True
        entries, notes = PL.build_plan(self.w, self.h,
                                       tooltip=False, extra=True, panel=True, dxdy=False)
        self.entries = entries
        self.log("  补丁站点：%d 条" % len(entries))
        for n in notes:
            self.log(n)
        delta = self.base - PL.IMAGE_BASE
        bad = []
        for e in entries:
            addr = e["va"] + delta
            cur = self.rpm(addr, e["size"])
            if cur is None:
                bad.append((e, "读失败"))
            elif cur not in (e["old"], e["new"]):
                bad.append((e, "内容=%s 期望 %s" % (cur.hex(), e["old"].hex())))
        if bad:
            self.log("  ❌ 校验不通过 %d 条（未做任何写入）" % len(bad))
            for e, why in bad[:20]:
                self.log("     %#010x %s : %s" % (e["va"], e["label"], why))
            return False
        for e in entries:
            if not self.wpm(e["va"] + delta, e["new"]):
                self.log("  ❌ 写入失败 %#x" % e["va"])
                return False
        self.log("  ✅ 补丁已写入（%d 条，exe 文件未改动）" % len(entries))
        return True

    # ---------------- 事件处理
    def on_create_process(self, de):
        self.hp = ctypes.c_void_p(_ptr(de, OFF_HPROC))
        self.main_thread = ctypes.c_void_p(_ptr(de, OFF_HTHREAD))
        self.main_tid = _u32(de, 8)
        base = _ptr(de, OFF_BASE) & 0xFFFFFFFF
        if not (0x10000 <= base < 0x80000000):
            # 事件字段读不出合理基址时，直接读 32 位 PEB（更可靠）
            base = PL.wow64_peb_image_base(self.hp.value) or 0
        self.base = base
        self.log("== CREATE_PROCESS pid=%d tid=%d 模块基址=%#x ==" % (
            _u32(de, 4), self.main_tid, self.base))
        if not self.apply_patches():
            self.log("  ❌ 补丁失败，终止")
            k32.TerminateProcess(self.hp, 3)
            return
        for va, label, nargs in self.points:
            if self.plant(va, label):
                self.log("  断点 %#x  %s（%d 参）" % (va, label, nargs))
        self.arm_watch(self.main_thread)

    def handle_bp(self, de, tid):
        ex_addr = _ptr(de, OFF_EXADDR) & 0xFFFFFFFF
        va = ex_addr - (self.base - PL.IMAGE_BASE)
        rec = self.bp.get(va)
        if rec is None:
            # 不是我们的断点（可能是游戏自己的 INT3/异常）
            self.log("  ? 未知断点于 %#x（原样放行）" % ex_addr)
            return DBG_EXCEPTION_NOT_HANDLED
        handle, ctx = self.thread_ctx(tid)
        if ctx is None:
            self.close_thread(handle)
            return DBG_CONTINUE
        esp = self.reg(ctx, C_ESP)
        eip = self.reg(ctx, C_EIP)
        ret = self.u32(esp) or 0
        args = []
        for i in range(6):
            args.append(self.u32(esp + 4 + 4 * i) or 0)
        label = rec["label"]
        detail = ""
        if va == 0x41EB70:
            rc = args[3]
            r = self.rpm(rc, 16) if rc else None
            if r:
                x1, y1, x2, y2 = struct.unpack("<iiii", r)
                detail = "rc=(%d,%d,%d,%d) w=%d h=%d" % (x1, y1, x2, y2, x2 - x1, y2 - y1)
            detail += " src=%#x color=%#x flags=%#x" % (args[2], args[4], args[5])
        elif va == 0x424C73:
            detail = "viewport=(%d,%d,%d,%d) flag=%d" % tuple(args[:5])
            if 0 <= args[2] < 4000 and 0 <= args[3] < 4000:
                pass
        elif va == 0x43CDCE:
            detail = "screen=(%d,%d)" % (args[0], args[1])
        elif va == 0x4700C6:
            detail = "text@%#x x=%d y=%d flags=%#x" % (args[0], args[1], args[2], args[3])
        else:
            detail = "args=" + ",".join("%#x" % a for a in args)
        self.hits[va] = self.hits.get(va, 0) + 1
        key = (va, detail)
        sample = "%-22s ret=%#x %s | %s" % (label, ret, detail, self.state())
        self.agg_add(key, sample)
        # 控制台实时反馈（用户能看到「它在工作」）
        try:
            print("  · %-22s %s" % (label, detail), flush=True)
        except Exception:                                   # noqa: BLE001
            pass

        # 断点保持常驻（不再 TF/Dr 单步：WOW64 下会破坏被调试线程）；
        # 命中到上限后撤掉，避免热点断点拖慢游戏。
        if self.hits[va] >= POINT_CAP:
            self.unplant(va)
            self.log("  · %s 命中 %d 次，已撤销该断点" % (label, self.hits[va]))
        self.close_thread(handle)
        return DBG_CONTINUE

    def thread_ctx(self, tid):
        """打开线程并取 WOW64 上下文，返回 (句柄, 上下文)；用完必须 close_thread。"""
        h = k32.OpenThread(0x001F03FF, False, tid)
        if not h:
            return None, None
        handle = ctypes.c_void_p(h)
        ctx = self.get_ctx(handle)
        return handle, ctx

    def close_thread(self, handle):
        if handle:
            k32.CloseHandle(handle)

    def handle_single_step(self, de, tid):
        ex_addr = _ptr(de, OFF_EXADDR) & 0xFFFFFFFF
        handle, ctx = self.thread_ctx(tid)
        if ctx is None:
            self.close_thread(handle)
            return DBG_CONTINUE
        dr6, _dr7 = self.read_drs(handle)
        try:
            if tid in self.stepping:
                # INT3 后的单步：重新下断，清 TF
                va = ex_addr - (self.base - PL.IMAGE_BASE)
                if va in self.bp:
                    self.plant(va, self.bp[va]["label"])
                self.stepping.discard(tid)
                self.set_reg(ctx, C_EFLAGS, self.reg(ctx, C_EFLAGS) & ~0x100)
                self.set_ctx(handle, ctx)
                return DBG_CONTINUE
            # 硬件写监视点：Dr6 低 4 位指出是哪一个
            which = [i for i in range(4) if dr6 & (1 << i)]
            names = ", ".join(self.watch[i][0] if i < len(self.watch) else "?"
                              for i in which)
            eip = self.reg(ctx, C_EIP)
            va = eip - (self.base - PL.IMAGE_BASE)
            key = ("WATCH", "写 %s @eip=%#x" % (names, va))
            self.agg_add(key, "WATCH 写 %-8s eip=%#x (+基址前 %#x) | %s" % (
                names, va, eip, self.state()))
            self.set_reg(ctx, C_DR6, 0)
            self.set_ctx(handle, ctx)
            return DBG_CONTINUE
        finally:
            self.close_thread(handle)

    # ---------------- 主循环
    def run(self):
        si = PL.STARTUPINFOW()
        si.cb = ctypes.sizeof(si)
        pi = PL.PROCESS_INFORMATION()
        flags = DEBUG_ONLY_THIS_PROCESS | CREATE_NO_WINDOW
        cwd = self.cwd or os.path.dirname(self.exe)
        self.log("\n===== trace %s  exe=%s  %dx%d =====" % (
            time.strftime("%Y-%m-%d %H:%M:%S"), self.exe, self.w, self.h))
        with open(self.exe, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        self.log("  母本 md5：%s (%s)" % (md5, "一致" if md5 == PL.MOTHER_MD5 else "！非母本"))
        ok = k32.CreateProcessW(ctypes.c_wchar_p(self.exe), None, None, None, False,
                                flags, None, ctypes.c_wchar_p(cwd),
                                ctypes.byref(si), ctypes.byref(pi))
        if not ok:
            self.log("❌ CreateProcess(DEBUG) 失败：%s" % ctypes.WinError(ctypes.get_last_error()))
            return 3
        self.log("  已创建（调试模式，进程暂停）：pid=%d" % pi.dwProcessId)

        de = ctypes.create_string_buffer(256)
        while True:
            if not k32.WaitForDebugEvent(de, 1000):
                self.flush()
                continue
            code = _u32(de, 0)
            pid, tid = _u32(de, 4), _u32(de, 8)
            self.n_events += 1
            cont = DBG_CONTINUE
            try:
                if code == CREATE_PROCESS_DEBUG_EVENT:
                    self.on_create_process(de)
                elif code == EXCEPTION_DEBUG_EVENT:
                    ex_code = _u32(de, OFF_EXCODE)
                    if ex_code in BP_CODES:
                        cont = self.handle_bp(de, tid)
                    elif ex_code in SS_CODES:
                        cont = self.handle_single_step(de, tid)
                    else:
                        cont = DBG_EXCEPTION_NOT_HANDLED
                elif code == EXIT_PROCESS_DEBUG_EVENT:
                    self.log("== EXIT_PROCESS code=%d ==" % _u32(de, 12))
                    k32.ContinueDebugEvent(pid, tid, DBG_CONTINUE)
                    break
                elif code == LOAD_DLL_DEBUG_EVENT:
                    h = _ptr(de, OFF_HFILE)
                    if h:
                        k32.CloseHandle(ctypes.c_void_p(h))
                k32.ContinueDebugEvent(pid, tid, cont)
            except Exception as exc:                     # noqa: BLE001
                self.log("  !! 事件处理异常：%r" % (exc,))
                k32.ContinueDebugEvent(pid, tid, DBG_CONTINUE)
            self.flush()
        self.flush(force=True)
        self.log("---- 断点命中统计：%s ----" % ", ".join(
            "%#x×%d" % (v, self.hits[v]) for v in sorted(self.hits)))
        self.log("  日志结束（事件 %d，用时 %.0fs）" % (self.n_events, time.time() - self.t0))
        return 0


    def plant_abs(self, addr, label):
        """按**绝对地址**下断（自测用；游戏用 plant() 走文件 VA + 基址差）。"""
        orig = self.rpm(addr, 1)
        if orig is None or not self.wpm(addr, b"\xcc"):
            self.log("  ! plant_abs 写入失败 @%#x" % addr)
            return False
        back = self.rpm(addr, 1)
        if back != b"\xcc":
            self.log("  ! plant_abs 回读不是 0xCC（读到 %s）@%#x" % (
                back.hex() if back else "None", addr))
            return False
        self.bp_abs = getattr(self, "bp_abs", {})
        self.bp_abs[addr] = {"orig": orig, "label": label}
        return True

    def write_drs_both(self, hthread, specs):
        """把同一份 DR 值写进原生(64 位)与 WOW64(32 位)两个上下文并返回 (ok64, ok32)。
        WOW64 线程在两个上下文间切换，只写一侧可能在模式切换后失效。"""
        ok1 = self.write_drs(hthread, specs)
        ok2 = False
        try:
            ctx = self.get_ctx(hthread)
            if ctx is not None:
                for i, addr, size in specs:
                    self.set_reg(ctx, C_DR0 + 4 * i, addr)
                self.set_reg(ctx, C_DR7, self.dr7_value(specs))
                self.set_reg(ctx, C_DR6, 0)
                ok2 = self.set_ctx(hthread, ctx)
        except Exception:                                   # noqa: BLE001
            pass
        return ok1, ok2


# ---------------------------------------------------------------- 自测（INT3 + Dr）
def selftest_debug():
    """自测调试循环（32 位测试进程，不碰游戏）：
    ① 在入口下 INT3 → 验证断点命中与上下文读取；
    ② 命中后清断点，把 Dr0 指向「下一条指令」并同时写两个上下文 → 验证 Dr 是否触发。"""
    import glob
    cands = [p for p in glob.glob(r"C:\Windows\SysWOW64\*.exe")
             if os.path.basename(p).lower() in ("ping.exe", "hostname.exe", "whoami.exe")]
    if not cands:
        print("❌ 找不到 32 位测试进程（SysWOW64）")
        return 3
    exe = cands[0]
    # 默认用「跑得久、一定执行到入口」的进程（ping 30 次）；可用 PEG_SELFTEST_CMD 覆盖
    cmdline = os.environ.get("PEG_SELFTEST_CMD") or ('"%s" -n 30 127.0.0.1' % exe)
    pe = open(exe, "rb").read()
    e_lfanew = struct.unpack_from("<I", pe, 0x3C)[0]
    entry_rva = struct.unpack_from("<I", pe, e_lfanew + 0x28)[0]
    print("测试进程：%s  entryRVA=%#x" % (exe, entry_rva))

    logp = os.path.join(OUT, "trace-selftest.txt")
    open(logp, "w", encoding="utf-8").close()
    tr = Tracer(exe, os.path.dirname(exe), 800, 600, patches=False,
                no_patches=True, points=[], watch=[], logpath=logp, cap=50)

    si = PL.STARTUPINFOW()
    si.cb = ctypes.sizeof(si)
    pi = PL.PROCESS_INFORMATION()
    cl = ctypes.create_unicode_buffer(cmdline)
    ok = k32.CreateProcessW(ctypes.c_wchar_p(exe), cl, None, None, False,
                            DEBUG_ONLY_THIS_PROCESS | CREATE_NO_WINDOW, None,
                            ctypes.c_wchar_p(os.path.dirname(exe)),
                            ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        print("❌ CreateProcess 失败：%s" % ctypes.WinError(ctypes.get_last_error()))
        return 3
    tr.log("selftest：pid=%d exe=%s" % (pi.dwProcessId, exe))

    de = ctypes.create_string_buffer(256)
    stage = 1              # 2=等 INT3 命中；3=等 Dr 单步；4=完
    hit_bp = hit_dr = False
    entry_abs = None
    t_end = time.time() + 30
    while time.time() < t_end and stage < 4:
        if not k32.WaitForDebugEvent(de, 500):
            continue
        code, pid, tid = _u32(de, 0), _u32(de, 4), _u32(de, 8)
        tr.log("  · 事件 code=%d pid=%d tid=%d" % (code, pid, tid))
        try:
            if code == CREATE_PROCESS_DEBUG_EVENT:
                tr.hp = ctypes.c_void_p(_ptr(de, OFF_HPROC))
                tr.base = _ptr(de, OFF_BASE) & 0xFFFFFFFF
                if not (0x10000 <= tr.base < 0x80000000):
                    tr.base = PL.wow64_peb_image_base(tr.hp.value) or 0
                tr.main_tid = tid
                entry_abs = tr.base + entry_rva
                tr.log("CREATE_PROCESS base=%#x pid=%d 入口=%#x" % (tr.base, pid, entry_abs))
                if tr.plant_abs(entry_abs, "selftest 入口"):
                    tr.log("已下 INT3 @%#x" % entry_abs)
                    stage = 2
                else:
                    tr.log("! 无法下断")
                    stage = 4
            elif code == EXCEPTION_DEBUG_EVENT:
                ex = _u32(de, OFF_EXCODE)
                ex_addr = _ptr(de, OFF_EXADDR) & 0xFFFFFFFF
                seen = getattr(tr, "ex_seen", None)
                if seen is None:
                    seen = tr.ex_seen = {}
                k = (ex, ex_addr)
                seen[k] = seen.get(k, 0) + 1
                if seen[k] <= 3:
                    tr.log("  异常 ex=%#x addr=%#x（第 %d 次）" % (ex, ex_addr, seen[k]))
                if ex in BP_CODES and stage == 2:
                    rec = getattr(tr, "bp_abs", {}).get(ex_addr)
                    if rec is None:
                        tr.log("  其它断点 @%#x（放行）" % ex_addr)
                    else:
                        handle, ctx = tr.thread_ctx(tid)
                        try:
                            if ctx is None:
                                continue
                            hit_bp = True
                            tr.log("✅ ① INT3 命中 @%#x  EAX=%#x ESP=%#x" % (
                                ex_addr, tr.reg(ctx, C_EAX), tr.reg(ctx, C_ESP)))
                            # 常驻断点：不再 TF/Dr 单步（WOW64 下会破坏被调试线程）
                            tr.stage_after_tf = False
                            stage = 4
                        finally:
                            tr.close_thread(handle)
                        k32.ContinueDebugEvent(pid, tid, DBG_CONTINUE)
                        continue
                elif ex in SS_CODES:
                    handle, ctx = tr.thread_ctx(tid)
                    try:
                        eip = tr.reg(ctx, C_EIP)
                        if getattr(tr, "stage_after_tf", False):
                            tr.stage_after_tf = False
                            tr.log("  （跳过 Dr 单步：WOW64 下不可用）")
                    finally:
                        tr.close_thread(handle)
            k32.ContinueDebugEvent(pid, tid, DBG_CONTINUE)
        except Exception as exc:                            # noqa: BLE001
            tr.log("selftest 异常：%r" % (exc,))
            k32.ContinueDebugEvent(pid, tid, DBG_CONTINUE)
    if tr.hp:
        k32.TerminateProcess(tr.hp, 0)
    tr.flush(force=True)
    print("① INT3 断点        ：%s" % ("✅" if hit_bp else "❌"))
    print("② Dr 硬件执行断点  ：跳过（WOW64 + 64 位调试器下不可用，见日志）")
    print("日志：%s" % logp)
    return 0 if hit_bp else 4


# ---------------------------------------------------------------- 入口
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default=PL.MOTHER)
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--w", type=int, default=1920)
    ap.add_argument("--h", type=int, default=1080)
    ap.add_argument("--patches", action="store_true", help="先打 236 条尺寸补丁（默认就打）")
    ap.add_argument("--no-patches", action="store_true", help="不打尺寸补丁（纯观察原始行为）")
    ap.add_argument("--point", action="append", default=None,
                    help="额外断点 VA（可多次），格式 0x41EB70[:名称]")
    ap.add_argument("--no-default-points", action="store_true", help="只用 --point 指定的断点")
    ap.add_argument("--watch", action="append", default=None,
                    help="硬件写监视点 VA[:字节数]（最多 4 个）")
    ap.add_argument("--no-watch", action="store_true")
    ap.add_argument("--cap", type=int, default=400, help="每类事件最多记录多少条不同样本")
    ap.add_argument("--log", default=os.path.join(OUT, "trace-log.txt"))
    ap.add_argument("--selftest-debug", action="store_true")
    a = ap.parse_args()

    if a.selftest_debug:
        return selftest_debug()

    points = [] if a.no_default_points else list(POINTS)
    for spec in (a.point or []):
        va = int(spec.split(":")[0], 16)
        label = spec.split(":", 1)[1] if ":" in spec else "自定义 %#x" % va
        points.append((va, label, 6))
    watch = [] if a.no_watch else list(WATCH_DEFAULT)
    for spec in (a.watch or []):
        parts = spec.split(":")
        watch.append(("watch%#x" % int(parts[0], 16), int(parts[0], 16),
                      int(parts[1]) if len(parts) > 1 else 4))

    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    open(a.log, "w", encoding="utf-8").close()
    print("trace 日志：%s" % a.log)
    tr = Tracer(a.exe, a.cwd, a.w, a.h, patches=True,
                no_patches=a.no_patches, points=points, watch=watch,
                logpath=a.log, cap=a.cap)
    return tr.run()


if __name__ == "__main__":
    sys.exit(main())
