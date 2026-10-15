# -*- coding: utf-8 -*-
"""Attach to a running process and search its address space for probes.

Pure ASCII source; probes come from a UTF-8 TSV (zh <TAB> en <TAB> source).

Usage:
  python memscan.py --pid 1234 --probes probes.tsv
"""
import argparse
import ctypes
import io
import sys
from ctypes import wintypes

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
PAGE_GUARD = 0x100
READABLE = (0x02, 0x04, 0x08, 0x20, 0x40, 0x80)


class MBI(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("_pad1", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("_pad2", wintypes.DWORD),
    ]


k32.OpenProcess.restype = wintypes.HANDLE
k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k32.VirtualQueryEx.restype = ctypes.c_size_t
k32.VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MBI), ctypes.c_size_t]
k32.ReadProcessMemory.restype = wintypes.BOOL
k32.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.CloseHandle.argtypes = [wintypes.HANDLE]


def load_probes(path):
    out = []
    with io.open(path, "r", encoding="utf-8-sig") as f:
        for ln in f:
            ln = ln.rstrip("\r\n")
            if not ln or ln.startswith("#"):
                continue
            c = ln.split("\t")
            if len(c) >= 2:
                out.append((c[0].strip(), (c[1].strip() if len(c) > 1 else ""),
                            (c[2].strip() if len(c) > 2 else "")))
    return out


def regions(h, hi=0x7FFF0000):
    addr = 0x10000
    mbi = MBI()
    size = ctypes.sizeof(mbi)
    while addr < hi:
        q = k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), size)
        if not q:
            break
        base = mbi.BaseAddress or 0
        rsize = mbi.RegionSize or 0
        if rsize == 0:
            break
        if (mbi.State & MEM_COMMIT) and not (mbi.Protect & PAGE_GUARD) \
           and (mbi.Protect & 0xFF) in READABLE and rsize <= 64 * 1024 * 1024:
            yield base, rsize
        nxt = base + rsize
        addr = nxt if nxt > addr else addr + 0x1000


def peek(pid, addr, length):
    """Dump process memory at a fixed VA (ASCII / GBK preview)."""
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        print("OpenProcess failed err=%d" % ctypes.get_last_error())
        return 2
    buf = ctypes.create_string_buffer(length)
    read = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, length, ctypes.byref(read))
    k32.CloseHandle(h)
    print("ReadProcessMemory(0x%08X, %d) = %s, read=%d" % (addr, length, ok, read.value))
    data = buf.raw[:read.value]
    print("  hex: %s" % data[:64].hex(" "))
    # split on NUL and print candidates
    for i, part in enumerate(data.split(b"\x00")):
        if not part:
            continue
        for enc in ("ascii", "gbk"):
            try:
                s = part.decode(enc)
                if all(c.isprintable() or c == "\t" for c in s):
                    print("  [%2d] (%s) %r" % (i, enc, s))
                    break
            except Exception:
                pass
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, required=True)
    ap.add_argument("--probes")
    ap.add_argument("--all-hits", action="store_true")
    ap.add_argument("--peek")
    ap.add_argument("--len", type=int, default=512)
    a = ap.parse_args()

    if a.peek:
        return peek(a.pid, int(a.peek, 16), a.len)

    probes = load_probes(a.probes)
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, a.pid)
    if not h:
        print("OpenProcess failed err=%d" % ctypes.get_last_error())
        return 2

    needles = []
    for zh, en, src in probes:
        for enc, tag in (("gbk", "GBK"), ("utf-16-le", "U16")):
            try:
                needles.append(([zh, src, tag], zh.encode(enc)))
            except Exception:
                pass
        if en:
            try:
                needles.append(([en, src, "ASCII"], en.encode("ascii")))
            except Exception:
                pass

    hits = {}
    total = 0
    nreg = 0
    for base, rsize in regions(h):
        nreg += 1
        b = ctypes.create_string_buffer(rsize)
        read = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(h, ctypes.c_void_p(base), b, rsize, ctypes.byref(read)):
            continue
        data = b.raw[:read.value]
        total += read.value
        for key, nd in needles:
            kk = tuple(key)
            lst = hits.setdefault(kk, [])
            if lst and not a.all_hits:
                continue
            pos = data.find(nd)
            while pos >= 0:
                lst.append(base + pos)
                if not a.all_hits:
                    break
                pos = data.find(nd, pos + 1)
    k32.CloseHandle(h)

    print("pid=%d  regions=%d  scanned=%.1f MB" % (a.pid, nreg, total / 1048576.0))
    print()
    zh_ok = 0
    for zh, en, src in probes:
        g = len(hits.get((zh, src, "GBK"), []))
        u = len(hits.get((zh, src, "U16"), []))
        e = len(hits.get((en, src, "ASCII"), [])) if en else -1
        flag = "OK " if g else "MISS"
        if g:
            zh_ok += 1
        print("%s %-30s src=%-22s GBK=%d U16=%d EN(%s)=%d  %s"
              % (flag, zh[:30], src, g, u, (en[:18] if en else "-"), e,
                 ("0x%08X" % hits[(zh, src, "GBK")][0]) if g else ""))
    print()
    print("== %d / %d Chinese probes present in memory ==" % (zh_ok, len(probes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
