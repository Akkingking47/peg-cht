# -*- coding: utf-8 -*-
"""Runtime verification for OpenGen efile localization.

Pure ASCII source (Chinese probes are read from a UTF-8 data file).

Steps
  1. back up Settings.cfg (once) and switch EFolder / LastOpen to the target efile
  2. launch the game
  3. wait, then scan the process address space for each probe in
     GBK / UTF-16LE / UTF-8 encodings
  4. report hit counts, then terminate the game and restore Settings.cfg

Usage:
  python runtime-verify.py --game D:\\OpenPG2 --probes probes.tsv ^
      --efolder EFILE_NASHORNPBEM\\ --lastopen EFILE_NASHORNPBEM\\SCENARIO\\utopianparadox.xscn
"""
import argparse
import ctypes
import io
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes

k32 = ctypes.WinDLL("kernel32", use_last_error=True)

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01
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
            if len(c) < 3:
                continue
            out.append((c[0].strip(), c[1].strip(), c[2].strip()))
    return out


def patch_settings(path, efolder, lastopen):
    with io.open(path, "r", encoding="gbk", errors="replace", newline="") as f:
        txt = f.read()
    lines = txt.split("\n")
    seen = {"EFolder": False, "LastOpen": False}
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.lower().startswith("efolder="):
            lines[i] = "EFolder=" + efolder
            seen["EFolder"] = True
        elif s.lower().startswith("lastopen="):
            lines[i] = "LastOpen=" + lastopen
            seen["LastOpen"] = True
    with io.open(path, "w", encoding="gbk", newline="") as f:
        f.write("\n".join(lines))
    return seen


def regions(h):
    addr = 0x10000
    hi = 0x7FFF0000
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


def scan(pid, probes):
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        raise OSError("OpenProcess failed, err=%d" % ctypes.get_last_error())
    # needles: (label, bytes)
    needles = []
    for zh, en, src in probes:
        for enc, tag in (("gbk", "GBK"), ("utf-16-le", "U16")):
            try:
                needles.append(((zh, src, tag), zh.encode(enc)))
            except Exception:
                pass
        if en:
            try:
                needles.append(((en, src, "ASCII"), en.encode("ascii")))
            except Exception:
                pass

    hits = {k[0:3]: [] for k in needles}
    total = 0
    nregions = 0
    buf = ctypes.create_string_buffer(1)
    for base, rsize in regions(h):
        nregions += 1
        b = ctypes.create_string_buffer(rsize)
        read = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(h, ctypes.c_void_p(base), b, rsize, ctypes.byref(read)):
            continue
        data = b.raw[:read.value]
        total += read.value
        for key, nd in needles:
            if hits[key]:
                continue
            pos = data.find(nd)
            if pos >= 0:
                hits[key].append(base + pos)
    k32.CloseHandle(h)
    return hits, total, nregions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True)
    ap.add_argument("--exe", default="OpenGen.exe")
    ap.add_argument("--probes", required=True)
    ap.add_argument("--efolder", required=True)
    ap.add_argument("--lastopen", required=True)
    ap.add_argument("--wait", type=int, default=30)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    exe = os.path.join(a.game, a.exe)
    settings = os.path.join(a.game, "Settings.cfg")
    bak = settings + ".poc-backup"

    if not os.path.exists(bak):
        shutil.copy2(settings, bak)
        print("[1] Settings.cfg backed up -> %s" % bak)
    else:
        print("[1] Settings.cfg backup already exists")

    seen = patch_settings(settings, a.efolder, a.lastopen)
    print("[2] Settings patched: %s" % seen)

    probes = load_probes(a.probes)
    print("[3] probes loaded: %d" % len(probes))

    proc = subprocess.Popen([exe], cwd=a.game)
    print("[4] launched pid=%d, waiting %ds ..." % (proc.pid, a.wait))
    try:
        time.sleep(a.wait)
        if proc.poll() is not None:
            print("    !! process exited early, rc=%s" % proc.returncode)
        hits, total, nregions = scan(proc.pid, probes)
        print("[5] scanned %d regions / %.1f MB" % (nregions, total / 1048576.0))
        print()
        print("%-26s %-34s %-6s %s" % ("PROBE(zh)", "EN ORIGINAL", "ENC", "HITS"))
        print("-" * 100)
        ng = 0
        for zh, en, src in probes:
            for tag in ("GBK", "U16"):
                k = (zh, src, tag)
                n = len(hits.get(k, []))
                print("%-26s %-34s %-6s %d" % (zh[:26], en[:34], tag, n))
                if tag == "GBK" and n:
                    ng += 1
            k = (en, src, "ASCII")
            if k in hits:
                print("%-26s %-34s %-6s %d" % ("", en[:34], "ASCII", len(hits[k])))
        print()
        print("== SUMMARY: %d / %d Chinese probes found in memory (GBK) ==" % (ng, len(probes)))
    finally:
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=8)
                except Exception:
                    proc.kill()
            print("[6] process stopped")
        except Exception as e:
            print("[6] stop failed: %s" % e)
        shutil.copy2(bak, settings)
        print("[7] Settings.cfg restored")


if __name__ == "__main__":
    main()
