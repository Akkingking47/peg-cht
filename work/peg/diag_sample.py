import ctypes, ctypes.wintypes as wt, os, time

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
k32.OpenThread.restype = wt.HANDLE
k32.OpenProcess.restype = wt.HANDLE


class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ThreadID", wt.DWORD),
                ("th32OwnerProcessID", wt.DWORD), ("tpBasePri", ctypes.c_long),
                ("tpDeltaPri", ctypes.c_long), ("dwFlags", wt.DWORD)]


class CONTEXT(ctypes.Structure):
    _fields_ = [("ContextFlags", wt.DWORD),
                ("Dr0", wt.DWORD), ("Dr1", wt.DWORD), ("Dr2", wt.DWORD), ("Dr3", wt.DWORD),
                ("Dr6", wt.DWORD), ("Dr7", wt.DWORD), ("FloatSave", ctypes.c_byte * 112),
                ("SegGs", wt.DWORD), ("SegFs", wt.DWORD), ("SegEs", wt.DWORD), ("SegDs", wt.DWORD),
                ("Edi", wt.DWORD), ("Esi", wt.DWORD), ("Ebx", wt.DWORD), ("Edx", wt.DWORD),
                ("Ecx", wt.DWORD), ("Eax", wt.DWORD), ("Ebp", wt.DWORD), ("Eip", wt.DWORD),
                ("SegCs", wt.DWORD), ("EFlags", wt.DWORD), ("Esp", wt.DWORD), ("SegSs", wt.DWORD),
                ("ExtendedRegisters", ctypes.c_byte * 512)]


OUT = os.path.join(WS, "work", "peg", "out")
LOG = os.path.join(OUT, "samples.log")
UNIT, STRIDE, N = 0x65AA00, 0x58, 96
TEXT = (0x401000, 0x48B000)


def log(s):
    line = "%s %s" % (time.strftime("%H:%M:%S"), s)
    print(line, flush=True)
    try:
        open(LOG, "a", encoding="gbk", errors="replace").write(line + "\n")
    except Exception:
        pass


def find_pid():
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)
    if not snap or snap == wt.HANDLE(-1).value:
        return None
    ME = ctypes.Structure
    class PE(ME):
        _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ProcessID", wt.DWORD),
                    ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)), ("th32ModuleID", wt.DWORD),
                    ("cntThreads", wt.DWORD), ("th32ParentProcessID", wt.DWORD),
                    ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD), ("szExeFile", ctypes.c_char * 260)]
    pe = PE()
    pe.dwSize = ctypes.sizeof(pe)
    pid = None
    if k32.Process32First(snap, ctypes.byref(pe)):
        while True:
            if pe.szExeFile.decode("gbk", "replace").lower() == "peg030.exe":
                pid = pe.th32ProcessID
                break
            if not k32.Process32Next(snap, ctypes.byref(pe)):
                break
    k32.CloseHandle(snap)
    return pid


def threads(pid):
    out = []
    snap = k32.CreateToolhelp32Snapshot(0x4, pid)
    if not snap or snap == wt.HANDLE(-1).value:
        return out
    te = THREADENTRY32()
    te.dwSize = ctypes.sizeof(te)
    if k32.Thread32First(snap, ctypes.byref(te)):
        while True:
            if te.th32OwnerProcessID == pid:
                out.append(te.th32ThreadID)
            if not k32.Thread32Next(snap, ctypes.byref(te)):
                break
    k32.CloseHandle(snap)
    return out


def sample(h, span=0.4, dt=0.001):
    hist = {}
    t0 = time.time()
    while time.time() - t0 < span:
        if k32.SuspendThread(h) == 0xFFFFFFFF:
            break
        c = CONTEXT()
        c.ContextFlags = 0x10001
        if k32.Wow64GetThreadContext(h, ctypes.byref(c)):
            hist[c.Eip] = hist.get(c.Eip, 0) + 1
        k32.ResumeThread(h)
        time.sleep(dt)
    return hist


def main():
    log("=== 采样器启动：等 PeG030.exe ===")
    pid = None
    while pid is None:
        pid = find_pid()
        if pid is None:
            time.sleep(1)
    log("found pid=%d" % pid)
    hp = k32.OpenProcess(0x1F0FFF, False, pid)
    tids = threads(pid)
    log("threads=%s" % tids)
    handles = []
    for tid in tids:
        h = k32.OpenThread(0x1F03FF, False, tid)
        if h:
            handles.append(h)
    prevfl = {}
    trig = 0
    last = time.time()
    while True:
        if k32.WaitForSingleObject(hp, 200) != 0x102:
            if find_pid() is None:
                log("进程已退出")
                break
        for i in range(N):
            b = ctypes.c_ubyte()
            got = k32.ReadProcessMemory(hp, ctypes.c_void_p(UNIT + i * STRIDE + 4), ctypes.byref(b), 1, None)
            if not got:
                continue
            v = b.value
            if prevfl.get(i) is not None and prevfl[i] != v and (v & 0x40):
                trig += 1
                log("trigger#%d unit=%d flags %02X -> %02X" % (trig, i, prevfl[i], v))
                agg = {}
                for h in handles:
                    for a, n in sample(h).items():
                        agg[a] = agg.get(a, 0) + n
                top = sorted(agg.items(), key=lambda kv: -kv[1])[:40]
                log("top(%d): %s" % (len(agg), " ".join("%X:%d" % (a, n) for a, n in top)))
            prevfl[i] = v
        if time.time() - last > 10:
            last = time.time()
            agg = {}
            for h in handles:
                for a, n in sample(h).items():
                    agg[a] = agg.get(a, 0) + n
            top = sorted(agg.items(), key=lambda kv: -kv[1])[:20]
            log("control top(%d): %s" % (len(agg), " ".join("%X:%d" % (a, n) for a, n in top)))
    log("=== 采样结束 ===")


main()
