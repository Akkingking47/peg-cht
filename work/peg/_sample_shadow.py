# -*- coding: utf-8 -*-
"""只读采样器 v2：在游戏里盯“选中单位 → 范围阴影”这一族状态，绝不写目标进程。

用法：
    python work\\peg\\_sample_shadow.py [--wait 240] [--secs 150]
先最多等 --wait 秒让 PeG030.exe 出现，然后每 0.4 秒采一次，共 --secs 秒。
只在“有变化”时打印（另每 25 次打一行心跳），同时全量追加写入
work\\peg\\out\\shadow-samples.txt。

每行含义：
    SELECT/DESELECT  选中单位 id 变化（word[0x686fd4]；0 = 没选中）
    SCROLL           滚动位置变化（word[0x4af2f8]/word[0x4af2fc]）
    range            范围表 0x622d4a 中等于选中 id 的格子数（= 应显示的阴影格数）
    maskA/maskB      两层 1bpp 遮挡层 0x4CCE40 / 0x53D640 的置位比特数及相对上一行的增量
    f78/f324/dirty   0x498d78 / 0x4af324 / word[0x498d74] 三个门标志
"""
import ctypes as C
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


k32 = C.WinDLL("kernel32", use_last_error=True)
k32.CreateToolhelp32Snapshot.restype = C.c_void_p
k32.CreateToolhelp32Snapshot.argtypes = [C.c_uint32, C.c_uint32]
k32.OpenProcess.restype = C.c_void_p
k32.OpenProcess.argtypes = [C.c_uint32, C.c_int, C.c_uint32]
k32.ReadProcessMemory.restype = C.c_int
k32.ReadProcessMemory.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p, C.c_size_t,
                                  C.POINTER(C.c_size_t)]
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
TH32CS_SNAPPROCESS = 0x00000002

LAYER_A, LAYER_B = 0x4CCE40, 0x53D640
LAYER_LEN = 0x70800
TABLE = 0x622D4A
ROW_STRIDE = 0x13B
COL_STRIDE = 7
DEFAULT_LOG = os.path.join(WS, "work", "peg", "out", "shadow-samples.txt")


class PROCESSENTRY32(C.Structure):
    _fields_ = [("dwSize", C.c_uint32), ("cntUsage", C.c_uint32),
                ("th32ProcessID", C.c_uint32), ("th32DefaultHeapID", C.c_void_p),
                ("th32ModuleID", C.c_uint32), ("cntThreads", C.c_uint32),
                ("th32ParentProcessID", C.c_uint32), ("pcPriClassBase", C.c_int32),
                ("dwFlags", C.c_uint32), ("szExeFile", C.c_char * 260)]


k32.Process32First.argtypes = [C.c_void_p, C.POINTER(PROCESSENTRY32)]
k32.Process32Next.argtypes = [C.c_void_p, C.POINTER(PROCESSENTRY32)]


def find_pids(name=b"PeG030.exe"):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    pe = PROCESSENTRY32()
    pe.dwSize = C.sizeof(PROCESSENTRY32)
    pids = []
    if k32.Process32First(snap, C.byref(pe)):
        while True:
            if pe.szExeFile.lower() == name.lower():
                pids.append(pe.th32ProcessID)
            if not k32.Process32Next(snap, C.byref(pe)):
                break
    k32.CloseHandle(snap)
    return sorted(pids, reverse=True)


def rd(proc, addr, n):
    buf = C.create_string_buffer(n)
    got = C.c_size_t(0)
    if not k32.ReadProcessMemory(proc, C.c_void_p(addr), buf, n, C.byref(got)):
        return None
    return buf.raw[:got.value]


def val(proc, addr, fmt="h"):
    b = rd(proc, addr, 2 if fmt in "hH" else 1)
    if not b or len(b) < (2 if fmt in "hH" else 1):
        return None
    return struct.unpack("<" + fmt, b)[0]


def popcount(proc, addr, n):
    b = rd(proc, addr, n)
    return -1 if not b else int.from_bytes(b, "little").bit_count()


def snapshot(proc):
    s = {}
    s["dirty"] = val(proc, 0x498d74)
    s["f78"] = val(proc, 0x498d78, "B")
    s["f324"] = val(proc, 0x4af324, "B")
    s["scr"] = (val(proc, 0x4af2f8), val(proc, 0x4af2fc))
    s["cache"] = (val(proc, 0x498d34), val(proc, 0x498d38))
    s["sel"] = val(proc, 0x686fd4)
    s["ext"] = (val(proc, 0x622d42), val(proc, 0x622d44))
    if None in s["ext"]:
        s["range"] = -1
    else:
        ex, ey = s["ext"]
        n = 0
        for j in range(ey):
            row = rd(proc, TABLE + j * ROW_STRIDE, ex * COL_STRIDE)
            if not row:
                continue
            for i in range(ex):
                if struct.unpack_from("<H", row, i * COL_STRIDE)[0] == s["sel"]:
                    n += 1
        s["range"] = n
    s["maskA"] = popcount(proc, LAYER_A, LAYER_LEN)
    s["maskB"] = popcount(proc, LAYER_B, LAYER_LEN)
    return s


def fmt(s, prev, t):
    ev = []
    if prev:
        if prev["sel"] != s["sel"]:
            ev.append("DESELECT" if not s["sel"] else "SELECT")
        if prev["scr"] != s["scr"]:
            ev.append("SCROLL")
        if prev["maskA"] != s["maskA"] or prev["maskB"] != s["maskB"]:
            ev.append("MASK+")
        if prev["f78"] != s["f78"]:
            ev.append("f78:%s->%s" % (prev["f78"], s["f78"]))
        if prev["f324"] != s["f324"]:
            ev.append("f324:%s->%s" % (prev["f324"], s["f324"]))
    dA = "" if not prev else "(%+d)" % (s["maskA"] - prev["maskA"])
    dB = "" if not prev else "(%+d)" % (s["maskB"] - prev["maskB"])
    return ("[%6.1fs] %-22s sel=%-5s range=%-4s maskA=%-7s%s maskB=%-7s%s "
            "scr=%s cache=%s f78=%s f324=%s dirty=%s"
            % (t, ",".join(ev) or "-", s["sel"], s["range"], s["maskA"], dA,
               s["maskB"], dB, s["scr"], s["cache"], s["f78"], s["f324"], s["dirty"]))


def main():
    args = sys.argv[1:]
    wait = 240.0
    secs = 150.0
    for i, a in enumerate(args):
        if a == "--wait":
            wait = float(args[i + 1])
        elif a == "--secs":
            secs = float(args[i + 1])
    os.makedirs(os.path.dirname(DEFAULT_LOG), exist_ok=True)
    log = open(DEFAULT_LOG, "a", encoding="utf-8")
    t0 = time.time()
    last_msg = t0
    proc = None
    while time.time() - t0 < wait and proc is None:
        pids = find_pids()
        if pids:
            proc = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pids[0])
            pid = pids[0]
        else:
            if time.time() - last_msg > 60:
                print("等待 PeG030.exe 出现…已等 %d 秒" % int(time.time() - t0))
                sys.stdout.flush()
                last_msg = time.time()
            time.sleep(0.5)
    if not proc:
        print("等了 %d 秒也没等到 PeG030.exe" % wait)
        return 1
    print("已连上 pid=%d，开始采样 %.0f 秒（只读）" % (pid, secs))
    print("日志：%s" % DEFAULT_LOG)
    log.write("\n===== 采样开始 pid=%d %s =====\n" % (pid, time.strftime("%H:%M:%S")))
    prev = None
    n = 0
    t1 = time.time()
    while time.time() - t1 < secs:
        n += 1
        s = snapshot(proc)
        if s["sel"] is None:
            print("  (读不到了，游戏可能已退出，等 20 秒看是否重开)")
            k32.CloseHandle(proc)
            proc = None
            t2 = time.time()
            while time.time() - t2 < 20 and proc is None:
                pids = find_pids()
                if pids:
                    proc = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
                                           False, pids[0])
                    prev = None
                else:
                    time.sleep(0.5)
            if not proc:
                print("游戏已退出，采样结束")
                break
            continue
        changed = (prev is None or prev["sel"] != s["sel"] or prev["scr"] != s["scr"]
                   or prev["maskA"] != s["maskA"] or prev["maskB"] != s["maskB"]
                   or prev["f78"] != s["f78"] or prev["f324"] != s["f324"]
                   or prev["dirty"] != s["dirty"])
        line = fmt(s, prev, time.time() - t1)
        if changed or n % 25 == 0:
            print(line)
            sys.stdout.flush()
        log.write(line + "\n")
        log.flush()
        prev = s
        time.sleep(0.4)
    log.write("===== 采样结束 %s =====\n" % time.strftime("%H:%M:%S"))
    log.close()
    k32.CloseHandle(proc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
