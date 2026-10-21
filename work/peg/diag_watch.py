# -*- coding: utf-8 -*-
"""diag_watch.py -- read-only watcher for PeG030 runtime layout variables.

Waits for PeG030.exe (started by the user through any entry), then polls a set
of variables that drive the map composition:

  0x622d42 / 0x622d44   drawn-extent in cells (0x41F2FD.. clamps them at 45/40)
  0x686a90 / 0x64c700   "map width/height in px" (grown +0x28 per call, cap 1920)
  0x4af2f8 / 0x4af2fc   scroll X / Y (clamped to mapW - viewportW - 2  => may go negative)
  0x4af300 / 0x498d3c   viewport origin on screen
  0x498d40 / 0x498d44   viewport far edge on screen
  0x4af330              game mode dword
  0x4af45c              theme/scenario index used by the hex-cell table at 0x4a0200
  0x4af2e4              "in scene" flag used by the map code

Usage: python work\\peg\\diag_watch.py [--pid N] [--interval 0.5] [--seconds 0]

Nothing is written to the game; every value is read with ReadProcessMemory.
"""
import argparse
import ctypes
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import peg_launcher as PL  # noqa: E402

k32 = ctypes.WinDLL("kernel32", use_last_error=True)

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
TH32CS_SNAPPROCESS = 0x00000002
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_ulong),
                ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", ctypes.c_ulong),
                ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.c_ulong),
                ("szExeFile", ctypes.c_wchar * 260)]


def find_pid(exe_name):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == INVALID_HANDLE_VALUE:
        return None
    pe = PROCESSENTRY32W()
    pe.dwSize = ctypes.sizeof(pe)
    ok = k32.Process32FirstW(snap, ctypes.byref(pe))
    pid = None
    while ok:
        if pe.szExeFile.lower() == exe_name.lower():
            pid = pe.th32ProcessID
            break
        ok = k32.Process32NextW(snap, ctypes.byref(pe))
    k32.CloseHandle(snap)
    return pid


def open_proc(pid):
    h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    return h or None


def read_mem(h, addr, size):
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size, ctypes.byref(got))
    if not ok or got.value != size:
        return None
    return buf.raw


U16 = [(0x00622d42, "extent_w_cells"), (0x00622d44, "extent_h_cells"),
       (0x00686a90, "mapW_px"), (0x0064c700, "mapH_px"),
       (0x004af2f8, "scrollX"), (0x004af2fc, "scrollY"),
       (0x004af300, "vpLeft"), (0x00498d3c, "vpTop"),
       (0x00498d40, "vpRight"), (0x00498d44, "vpBottom"),
       (0x004af45c, "theme_idx"), (0x00498d70, "last_arg")]
U8 = [(0x004af2e4, "in_scene_flag")]
U32 = [(0x004af330, "mode")]


def snap(h, base):
    out = {}
    for va, name in U16:
        raw = read_mem(h, base + (va - 0x400000), 2)
        out[name] = None if raw is None else int.from_bytes(raw, "little", signed=True)
    for va, name in U8:
        raw = read_mem(h, base + (va - 0x400000), 1)
        out[name] = None if raw is None else raw[0]
    for va, name in U32:
        raw = read_mem(h, base + (va - 0x400000), 4)
        out[name] = None if raw is None else int.from_bytes(raw, "little")
    return out


def fmt(s):
    vw = None
    vh = None
    if s["vpRight"] is not None and s["vpLeft"] is not None:
        vw = s["vpRight"] - s["vpLeft"] + 1
    if s["vpBottom"] is not None and s["vpTop"] is not None:
        vh = s["vpBottom"] - s["vpTop"] + 1
    maxx = maxy = None
    if s["mapW_px"] is not None and vw is not None:
        maxx = s["mapW_px"] - vw - 2
    if s["mapH_px"] is not None and vh is not None:
        maxy = s["mapH_px"] - vh - 2
    warn = ""
    if maxx is not None and maxx < 0:
        warn += "  <== maxScrollX NEGATIVE"
    if maxy is not None and maxy < 0:
        warn += "  <== maxScrollY NEGATIVE"
    return ("extent=%sx%s cells | mapW/H=%s/%s px | vp=%sx%s @%s,%s | "
            "scroll=%s,%s | maxScroll=%s,%s | mode=%s theme=%s scene=%s%s"
            % (s["extent_w_cells"], s["extent_h_cells"], s["mapW_px"], s["mapH_px"],
               vw, vh, s["vpLeft"], s["vpTop"],
               s["scrollX"], s["scrollY"], maxx, maxy,
               s["mode"], s["theme_idx"], s["in_scene_flag"], warn))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=0)
    ap.add_argument("--interval", type=float, default=0.5)
    ap.add_argument("--seconds", type=float, default=0.0,
                    help="0 = run until the game exits (Ctrl+C also works)")
    a = ap.parse_args()

    pid = a.pid
    n = 0
    while not pid:
        pid = find_pid("PeG030.exe")
        if not pid:
            if n % 15 == 0:
                print("[watch] waiting for PeG030.exe ...")
                sys.stdout.flush()
            n += 1
            time.sleep(1.0)
    print("[watch] found PeG030.exe pid=%d" % pid)

    h = None
    base = 0x400000
    for _ in range(20):
        h = open_proc(pid)
        if h:
            break
        time.sleep(0.5)
    if not h:
        print("[watch] cannot OpenProcess, error=%d" % ctypes.get_last_error())
        return 1
    b = PL.wow64_peb_image_base(h)
    if b:
        base = b
    print("[watch] image base = 0x%08X" % base)

    t0 = time.time()
    last = None
    miss = 0
    tried_fallback = False
    try:
        while True:
            s = snap(h, base)
            line = fmt(s)
            if line != last:
                print("[%7.2fs] %s" % (time.time() - t0, line))
                sys.stdout.flush()
                last = line
            if a.seconds and (time.time() - t0) > a.seconds:
                break
            if s["extent_w_cells"] is None:
                miss += 1
                if miss == 1:
                    print("[watch] ReadProcessMemory failed at base=0x%08X" % base)
                    sys.stdout.flush()
                if miss == 3 and not tried_fallback:
                    tried_fallback = True
                    base = 0x400000
                    print("[watch] retry with base=0x%08X" % base)
                    sys.stdout.flush()
                if find_pid("PeG030.exe") is None or miss > 60:
                    print("[watch] process gone / unreadable -> stop")
                    break
            else:
                miss = 0
            time.sleep(a.interval)
    except KeyboardInterrupt:
        pass
    k32.CloseHandle(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
