# -*- coding: utf-8 -*-
"""diag_watch2.py — 只读轮询：单位记录 + 地图刷新标志（不写一个字节）

用法：python work/peg/diag_watch2.py --wait PeG030.exe
日志：work/peg/out/watch2.log
"""
import ctypes
import ctypes.wintypes as wt
import os
import struct
import sys
import time

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


NL = chr(10)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "watch2.log")
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
TH32CS_SNAPPROCESS = 0x2

UNIT_BASE = 0x65AA00
UNIT_STRIDE = 0x58
UNIT_COUNT = 96
DWRITE = 0x66
EXT_X = 0x622D42
EXT_Y = 0x622D44
SCROLL_X = 0x4AF2F8
SCROLL_Y = 0x4AF2FC


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.c_void_p), ("th32ModuleID", wt.DWORD),
                ("cntThreads", wt.DWORD), ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", ctypes.c_char * 260)]


def find_pid(name):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap in (0, -1):
        return None
    e = PROCESSENTRY32()
    e.dwSize = ctypes.sizeof(PROCESSENTRY32)
    ok = k32.Process32First(snap, ctypes.byref(e))
    pid = None
    while ok:
        if e.szExeFile.decode("latin1", "replace").lower() == name.lower():
            pid = e.th32ProcessID
            break
        ok = k32.Process32Next(snap, ctypes.byref(e))
    k32.CloseHandle(snap)
    return pid


def log(msg):
    line = "%s %.3f %s" % (time.strftime("%H:%M:%S"), time.time() % 1000, msg)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(line + NL)
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("gbk", "replace").decode("gbk"))


def main():
    args = sys.argv[1:]
    name = "PeG030.exe"
    if "--wait" in args:
        name = args[args.index("--wait") + 1]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    log("=== diag_watch2 启动，等待 %s ===" % name)
    pid = None
    while not pid:
        pid = find_pid(name)
        time.sleep(0.4)
    h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    log("发现 %s pid=%d handle=%s" % (name, pid, bool(h)))
    if not h:
        return 1

    def rd(addr, n):
        buf = ctypes.create_string_buffer(n)
        read = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, n, ctypes.byref(read)):
            return None
        return buf.raw[:read.value]

    def u32(addr, off=0):
        d = rd(addr, off + 4)
        return None if not d or len(d) < off + 4 else struct.unpack_from("<I", d, off)[0]

    def u16(addr, off):
        d = rd(addr, off + 2)
        return None if not d or len(d) < off + 2 else struct.unpack_from("<H", d, off)[0]

    def u8(addr, off):
        d = rd(addr, off + 1)
        return None if not d or len(d) < off + 1 else d[off]

    prev = {}
    t0 = time.time()
    while time.time() - t0 < 3600:
        dirty = u8(DWRITE, 0)
        ex = u16(EXT_X, 0)
        ey = u16(EXT_Y, 0)
        sx = u32(SCROLL_X)
        sy = u32(SCROLL_Y)
        changed = []
        act = 0
        for i in range(UNIT_COUNT):
            a = UNIT_BASE + i * UNIT_STRIDE
            blk = rd(a, UNIT_STRIDE)
            if not blk or len(blk) < UNIT_STRIDE:
                continue
            fl = struct.unpack_from("<I", blk, 4)[0]
            if not (fl & 0x20):
                continue
            act += 1
            old = prev.get(i)
            if old != blk:
                if old is None:
                    changed.append("u[%d] first fl=0x%X c=(%d,%d)" % (i, fl, struct.unpack_from("<H", blk, 8)[0], struct.unpack_from("<H", blk, 10)[0]))
                else:
                    d = ["%02X:%02X>%02X" % (o, old[o], blk[o]) for o in range(UNIT_STRIDE) if old[o] != blk[o]]
                    changed.append("u[%d] fl=0x%X %s" % (i, fl, " ".join(d[:14])))
                prev[i] = blk
        n = prev.get("n", 0) + 1
        prev["n"] = n
        if n % 16 == 1 and n > 1:
            buf = bytearray()
            for b2 in range(0x600000, 0x700000, 0x10000):
                c2 = rd(b2, 0x10000)
                buf += c2 if c2 is not None else bytes(0x10000)
            fn = os.path.join(WS, "work", "peg", "out", "snap_%04d.bin") % n
            with open(fn, "wb") as fh:
                fh.write(bytes(buf))
            log("snap n=%d file=snap_%04d.bin" % (n, n))
        nok = 0
        for base in range(0x600000, 0x700000, 0x10000):
            chunk = rd(base, 0x10000)
            if chunk is None:
                continue
            nok += 1
            key = "c%X" % base
            cold = prev.get(key)
            if cold is not None and len(cold) == len(chunk):
                df = [o for o in range(len(chunk)) if cold[o] != chunk[o]]
                if df:
                    parts = ["%06X:%02X>%02X" % (base + o, cold[o], chunk[o]) for o in df[:16]]
                    log("diff n=%d %s" % (len(df), " ".join(parts)))
            prev[key] = chunk
        if n % 20 == 1:
            log("beat n=%d chunks_ok=%d" % (n, nok))
        tbl = rd(0x6268A0, 400 * 65)
        hist = {}
        if tbl and len(tbl) >= 400 * 65:
            for g in range(400):
                b = tbl[g * 65 + 1]
                hist[b] = hist.get(b, 0) + 1
            hkey = tuple(sorted(hist.items()))
            if prev.get("hist") != hkey:
                log("cells %s" % (hkey,))
                prev["hist"] = hkey
        dirty = u8(0x498D74, 0)
        if changed or prev.get("head") != (dirty, ex, ey, sx, sy):
            head = "dirty=%s ext=%sx%s scroll=%s,%s act=%d | " % (dirty, ex, ey, sx, sy, act)
            log(head + " ; ".join(changed) if changed else head)
            prev["head"] = (dirty, ex, ey, sx, sy)
        time.sleep(0.25)
    return 0


if __name__ == "__main__":
    sys.exit(main())
