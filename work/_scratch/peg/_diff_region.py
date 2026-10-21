r"""_diff_region.py -- read-only watcher.

Snapshots a large window of the game's memory at a fixed interval and prints
which addresses changed (4-byte words), together with the cursor position, so
we can correlate "clicked a unit / scrolled the map" with state changes.

Usage:
  python work\_scratch\peg\_diff_region.py --wait --secs 240
  python work\_scratch\peg\_diff_region.py --pid 1234 --lo 0x4AF000 --hi 0x6C0000 --interval 0.35

Never writes to the target process. Log: work\peg\out\diff-region.txt
"""
import ctypes
import ctypes.wintypes as wt
import os
import sys
import time

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
TH32CS_SNAPPROCESS = 0x00000002
INVALID_HANDLE = ctypes.c_void_p(-1).value


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD),
        ("cntUsage", wt.DWORD),
        ("th32ProcessID", wt.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wt.DWORD),
        ("cntThreads", wt.DWORD),
        ("th32ParentProcessID", wt.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wt.DWORD),
        ("szExeFile", ctypes.c_char * 260),
    ]


k32.OpenProcess.restype = ctypes.c_void_p
k32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
k32.ReadProcessMemory.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
]
k32.ReadProcessMemory.restype = wt.BOOL


def find_pid(name):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snap or snap == INVALID_HANDLE:
        return None
    e = PROCESSENTRY32()
    e.dwSize = ctypes.sizeof(e)
    ok = k32.Process32First(snap, ctypes.byref(e))
    found = None
    while ok:
        nm = e.szExeFile.decode("mbcs", "ignore")
        if nm.lower() == name.lower():
            found = e.th32ProcessID
            break
        ok = k32.Process32Next(snap, ctypes.byref(e))
    k32.CloseHandle(ctypes.c_void_p(snap))
    return found


def cursor():
    pt = wt.POINT()
    if u32.GetCursorPos(ctypes.byref(pt)):
        return pt.x, pt.y
    return -1, -1


def main():
    args = sys.argv[1:]
    name = "PeG030.exe"
    lo, hi = 0x4AF000, 0x6C0000
    interval, secs, wait = 0.35, 240.0, False
    pid = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--wait":
            wait = True
        elif a == "--pid":
            i += 1
            pid = int(args[i])
        elif a == "--lo":
            i += 1
            lo = int(args[i], 0)
        elif a == "--hi":
            i += 1
            hi = int(args[i], 0)
        elif a == "--interval":
            i += 1
            interval = float(args[i])
        elif a == "--secs":
            i += 1
            secs = float(args[i])
        else:
            raise SystemExit("unknown arg %r" % a)
        i += 1

    if pid is None:
        while True:
            pid = find_pid(name)
            if pid:
                break
            if not wait:
                raise SystemExit("process %s not found (use --wait)" % name)
            time.sleep(1.0)

    h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not h:
        raise SystemExit("OpenProcess failed err=%d" % ctypes.get_last_error())

    size = hi - lo
    CH = 0x10000
    outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
    try:
        os.makedirs(outdir)
    except OSError:
        pass
    logpath = os.path.join(outdir, "diff-region.txt")
    log = open(logpath, "w", encoding="utf-8", buffering=1)

    def snap():
        buf = bytearray(size)
        mv = memoryview(buf)
        got = 0
        off = 0
        while off < size:
            n = min(CH, size - off)
            read = ctypes.c_size_t(0)
            ok = k32.ReadProcessMemory(ctypes.c_void_p(h), ctypes.c_void_p(lo + off),
                                       ctypes.c_void_p(ctypes.addressof(mv[off])),
                                       ctypes.c_size_t(n), ctypes.byref(read))
            if not ok or read.value == 0:
                break
            got += read.value
            off += read.value
        return buf, got

    prev, got = snap()
    t0 = time.time()
    print("attached pid=%d region=%#x..%#x size=%d read=%d" % (pid, lo, hi, size, got))
    log.write("attached pid=%d region=%#x..%#x read=%d at %s\n" % (
        pid, lo, hi, got, time.strftime("%H:%M:%S")))
    print("log: %s" % logpath)

    last_cursor = cursor()
    while time.time() - t0 < secs:
        time.sleep(interval)
        cur, got = snap()
        t = time.time() - t0
        cx, cy = cursor()
        moved = (cx, cy) != last_cursor
        last_cursor = (cx, cy)
        # fast chunk compare first
        changed = []
        for base in range(0, size, CH):
            end = min(base + CH, size)
            if cur[base:end] == prev[base:end]:
                continue
            for o in range(base, end - 3, 4):
                if cur[o:o + 4] != prev[o:o + 4]:
                    changed.append(o)
                    if len(changed) >= 400:
                        break
            if len(changed) >= 400:
                break
        n_changed = len(changed)
        if n_changed:
            head = " ".join(
                "%#x:%s>%s" % (lo + o,
                               prev[o:o + 4][::-1].hex(),
                               cur[o:o + 4][::-1].hex())
                for o in changed[:20])
            line = "[%7.2fs] cursor=(%d,%d)%s changed=%d %s" % (
                t, cx, cy, " MOUSE" if moved else "", n_changed, head)
            print(line)
            log.write(line + "\n")
        else:
            if moved:
                line = "[%7.2fs] cursor=(%d,%d) MOUSE changed=0" % (t, cx, cy)
                print(line)
                log.write(line + "\n")
        prev = cur
    print("done, log: %s" % logpath)
    log.close()
    k32.CloseHandle(ctypes.c_void_p(h))


if __name__ == "__main__":
    main()
