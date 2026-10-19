# -*- coding: utf-8 -*-
"""诊断运行（非调试器方案）：一边监听游戏的 OutputDebugString 日志，
一边按启动器方式带补丁启动游戏；游戏退出后把这段时间里游戏**自己**输出的日志落盘。

- 不动任何文件：母本 exe 只读，补丁只写进程内存（沿用 peg_launcher 的 build_plan）。
- 不需要调试器：用 DBWIN 共享内存 + 事件对监听 OutputDebugString（DebugView 同款机制），
  32/64 位进程都能收到。
- `--selftest`：不启动游戏，用 python 子进程发一条 OutputDebugString 验证监听链路。
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import peg_launcher as PL                                    # noqa: E402

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.CreateEventW.restype = ctypes.c_void_p
k32.CreateEventW.argtypes = [ctypes.c_void_p, wt.BOOL, wt.BOOL, ctypes.c_wchar_p]
k32.SetEvent.argtypes = [ctypes.c_void_p]
k32.SetEvent.restype = wt.BOOL
k32.WaitForSingleObject.argtypes = [ctypes.c_void_p, wt.DWORD]
k32.WaitForSingleObject.restype = wt.DWORD
k32.CloseHandle.argtypes = [ctypes.c_void_p]
k32.CloseHandle.restype = wt.BOOL
k32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
k32.UnmapViewOfFile.restype = wt.BOOL
k32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(wt.DWORD)]
k32.GetExitCodeProcess.restype = wt.BOOL

PAGE_READWRITE = 0x04
FILE_MAP_READ = 0x0004
FILE_MAP_WRITE = 0x0002
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
DBWIN_SIZE = 4096
CREATE_SUSPENDED = 0x00000004
PAGE_EXECUTE_READWRITE = 0x40
OUT = os.path.join(HERE, "out")
DEFAULT_LOG = os.path.join(OUT, "game-debugview.txt")


class Listener:
    """DBWIN 监听：先创建共享内存与两个事件，再起线程收消息。"""

    def __init__(self, logpath, only_pid=None, echo=True):
        self.logpath = logpath
        self.only_pid = only_pid
        self.echo = echo
        self.count = 0
        self.stop = threading.Event()
        self.buf = None
        self.hmap = None
        self.h_ready = None
        self.h_data = None
        self.thread = None
        self.err = None

    def start(self):
        k32.CreateFileMappingW.restype = ctypes.c_void_p
        k32.CreateFileMappingW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wt.DWORD,
                                           wt.DWORD, wt.DWORD, ctypes.c_wchar_p]
        k32.MapViewOfFile.restype = ctypes.c_void_p
        k32.MapViewOfFile.argtypes = [ctypes.c_void_p, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]
        self.hmap = k32.CreateFileMappingW(ctypes.c_void_p(INVALID_HANDLE_VALUE), None,
                                           PAGE_READWRITE, 0, DBWIN_SIZE, "DBWIN_BUFFER")
        if not self.hmap:
            self.err = "CreateFileMapping(DBWIN_BUFFER) 失败：%s" % ctypes.WinError(ctypes.get_last_error())
            return False
        self.buf = k32.MapViewOfFile(ctypes.c_void_p(self.hmap), FILE_MAP_READ | FILE_MAP_WRITE,
                                     0, 0, DBWIN_SIZE)
        if not self.buf:
            self.err = "MapViewOfFile 失败：%s" % ctypes.WinError(ctypes.get_last_error())
            return False
        # 自动重置事件；已存在时 CreateEvent 返回其句柄
        self.h_ready = k32.CreateEventW(None, False, False, "DBWIN_BUFFER_READY")
        self.h_data = k32.CreateEventW(None, False, False, "DBWIN_DATA_READY")
        if not self.h_ready or not self.h_data:
            self.err = "CreateEvent 失败：%s" % ctypes.WinError(ctypes.get_last_error())
            return False
        with open(self.logpath, "w", encoding="utf-8") as f:
            f.write("# 游戏自身 OutputDebugString 日志（%s 开始监听）\n"
                    % time.strftime("%Y-%m-%d %H:%M:%S"))
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return True

    def _loop(self):
        k32.SetEvent(self.h_ready)
        while not self.stop.is_set():
            if k32.WaitForSingleObject(self.h_data, 200) != 0:
                continue
            try:
                pid = ctypes.c_uint32.from_address(self.buf).value
                raw = ctypes.string_at(self.buf + 4, DBWIN_SIZE - 4)
                msg = raw.split(b"\x00")[0].decode("gbk", "replace").rstrip("\r\n")
            except Exception as exc:                        # noqa: BLE001
                msg, pid = "<读取失败 %r>" % (exc,), 0
            if msg and (self.only_pid is None or pid == self.only_pid):
                line = "[%s] pid=%d  %s" % (time.strftime("%H:%M:%S"), pid, msg)
                self.count += 1
                with open(self.logpath, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
                if self.echo:
                    print(line, flush=True)
            k32.SetEvent(self.h_ready)

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=1.0)
        for h in (self.h_ready, self.h_data):
            if h:
                k32.CloseHandle(h)
        if self.buf:
            k32.UnmapViewOfFile(self.buf)
        if self.hmap:
            k32.CloseHandle(self.hmap)


def launch_patched(exe, w, h, dry=False, stop_after=False, repaint=False):
    """挂起启动 → 校验 → 写补丁 → 回读 → 放行；返回 (pid, hProcess) 或 (None, None)。

    repaint=False 表示**不**打 B 组（0x4489D8 每帧强制整屏刷新）。
    2026-xx 起因：0x498D74 这个「需要刷新」标志是共享的，母本里有很多处理器
    各自「读到标志 → 重绘自己那部分 → 清零」；我们的 B 组每帧抢先把标志清掉，
    导致地图/覆盖层（选中单位的移动范围阴影）拿不到刷新信号 —— 表现为
    「选中单位后鼠标不动就不显示范围阴影」。所以试玩默认关掉 B 组。
    """
    entries, notes = PL.build_plan(w, h, tooltip=False, extra=True, panel=True, dxdy=False,
                                   repaint=repaint)
    print("补丁站点：%d 条" % len(entries))
    for n in notes:
        print("  · %s" % n)
    if dry:
        return None, None
    base_pref, aslr = PL.pe_image_base_of(exe)
    cwd = os.path.dirname(exe)
    si = PL.STARTUPINFOW()
    si.cb = ctypes.sizeof(si)
    pi = PL.PROCESS_INFORMATION()
    ok = False
    for attempt in range(1, 4):
        ok = k32.CreateProcessW(ctypes.c_wchar_p(exe), None, None, None, False,
                                CREATE_SUSPENDED, None, ctypes.c_wchar_p(cwd),
                                ctypes.byref(si), ctypes.byref(pi))
        if ok:
            break
        print("CreateProcess 第 %d 次失败：%s" % (attempt, ctypes.WinError(ctypes.get_last_error())))
        time.sleep(0.7)
    if not ok:
        print("❌ CreateProcess 失败（已重试 3 次）")
        return None, None
    print("已挂起启动：pid=%d" % pi.dwProcessId)
    img = PL.wow64_peb_image_base(pi.hProcess) or base_pref
    delta = img - PL.IMAGE_BASE
    print("  实际模块基址：%#x" % img)
    bad = []
    for e in entries:
        addr = e["va"] + delta
        buf = ctypes.create_string_buffer(e["size"])
        n = ctypes.c_size_t()
        if not k32.ReadProcessMemory(ctypes.c_void_p(pi.hProcess), ctypes.c_void_p(addr),
                                     buf, e["size"], ctypes.byref(n)) or n.value != e["size"]:
            bad.append((e, "读失败"))
            continue
        cur = buf.raw[:e["size"]]
        if cur not in (e["old"], e["new"]):
            bad.append((e, "内容=%s 期望 %s" % (cur.hex(), e["old"].hex())))
    if bad:
        print("❌ 校验不通过 %d 条（未做任何写入）：" % len(bad))
        for e, why in bad[:10]:
            print("   %#010x %s : %s" % (e["va"], e["label"], why))
        k32.TerminateProcess(ctypes.c_void_p(pi.hProcess), 0)
        return None, None
    written = 0
    for e in entries:
        addr = e["va"] + delta
        old_prot = wt.DWORD()
        k32.VirtualProtectEx(ctypes.c_void_p(pi.hProcess), ctypes.c_void_p(addr),
                             e["size"], PAGE_EXECUTE_READWRITE, ctypes.byref(old_prot))
        n = ctypes.c_size_t()
        if not k32.WriteProcessMemory(ctypes.c_void_p(pi.hProcess), ctypes.c_void_p(addr),
                                      e["new"], e["size"], ctypes.byref(n)) or n.value != e["size"]:
            print("❌ WriteProcessMemory 失败于 %#x" % e["va"])
            k32.TerminateProcess(ctypes.c_void_p(pi.hProcess), 0)
            return None, None
        written += 1
        k32.VirtualProtectEx(ctypes.c_void_p(pi.hProcess), ctypes.c_void_p(addr),
                             e["size"], old_prot, ctypes.byref(wt.DWORD()))
    print("✅ 内存补丁完成：%d 条已写入（exe 文件未改动）" % written)
    if stop_after:
        k32.TerminateProcess(ctypes.c_void_p(pi.hProcess), 0)
        k32.CloseHandle(ctypes.c_void_p(pi.hThread))
        k32.CloseHandle(ctypes.c_void_p(pi.hProcess))
        print("selftest：已终止进程（游戏未执行任何指令，也没有窗口）")
        return None, None
    k32.ResumeThread(ctypes.c_void_p(pi.hThread))
    k32.CloseHandle(ctypes.c_void_p(pi.hThread))
    print("▶ 已放行，游戏开始运行（本窗口会实时显示游戏自己的日志）")
    return pi.dwProcessId, pi.hProcess


def selftest():
    logp = os.path.join(OUT, "debugview-selftest.txt")
    lis = Listener(logp, echo=True)
    if not lis.start():
        print("❌ 监听启动失败：%s" % lis.err)
        return 3
    time.sleep(0.5)
    print("用子进程发一条 OutputDebugStringA …")
    subprocess.Popen([sys.executable, "-c",
                      "import ctypes;ctypes.WinDLL('kernel32').OutputDebugStringA(b'diag-selftest-hello')"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 5
    while time.time() < deadline and lis.count == 0:
        time.sleep(0.2)
    lis.close()
    ok = lis.count > 0
    print("监听结果：%s（收到 %d 条）" % ("✅" if ok else "❌", lis.count))
    print("日志：%s" % logp)
    return 0 if ok else 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default=PL.MOTHER)
    ap.add_argument("--w", type=int, default=1920)
    ap.add_argument("--h", type=int, default=1080)
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--all", action="store_true", help="不按 pid 过滤（默认只看游戏进程）")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--selftest-patch", action="store_true",
                    help="只验证「挂起启动 + 236 条补丁 + 回读」这条路，然后立刻终止进程（不跑游戏）")
    a = ap.parse_args()
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    if a.selftest:
        return selftest()
    if a.selftest_patch:
        print("===== 补丁路径自测 %s =====" % time.strftime("%Y-%m-%d %H:%M:%S"))
        pid, _ = launch_patched(a.exe, a.w, a.h, stop_after=True)
        return 0 if pid is None else 3

    print("===== PeG 诊断运行 %s =====" % time.strftime("%Y-%m-%d %H:%M:%S"))
    print("exe=%s  %dx%d" % (a.exe, a.w, a.h))
    lis = Listener(a.log, only_pid=None if a.all else -1, echo=True)
    if not lis.start():
        print("❌ 监听启动失败：%s" % lis.err)
        return 3
    pid, hp = launch_patched(a.exe, a.w, a.h, dry=a.dry_run)
    if pid is None:
        lis.close()
        return 3
    lis.only_pid = None if a.all else pid
    try:
        k32.WaitForSingleObject(ctypes.c_void_p(hp), 0xFFFFFFFF)   # 等游戏退出
        code = wt.DWORD()
        k32.GetExitCodeProcess(ctypes.c_void_p(hp), ctypes.byref(code))
        print("\n游戏已退出（pid=%d，退出码=%d）。" % (pid, code.value))
    except KeyboardInterrupt:
        print("\n（被 Ctrl+C 中断；游戏可能仍在运行）")
    finally:
        time.sleep(0.5)
        lis.close()
        if hp:
            k32.CloseHandle(ctypes.c_void_p(hp))
    print("共记录 %d 条游戏日志 → %s" % (lis.count, a.log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
