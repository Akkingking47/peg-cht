# -*- coding: utf-8 -*-
"""
xref_call.py — 全 .text 调用图（call / jmp / jcc 目标 → 引用点）

用途：反查「谁调用了 0xXXXXXX」。为了速度，第一次运行时把整个 .text 线性反汇编
（逐条 count=1 重切，遇坏字节跳 1 字节，避免 capstone 中途停），结果缓存成 TSV：
    work\\peg\\out\\call_xrefs.tsv    列：target_hex  site_hex  mn  text
之后用 grep 工具直接查这个 TSV 即可，无需重复反汇编。

用法：
    python xref_call.py 0x44c6f0              # 建/读缓存并打印该目标的引用点
    python xref_call.py 0x44c6f0 0x44ac45     # 多个目标
    python xref_call.py --rebuild 0x44c6f0    # 强制重建缓存
"""
import os
import struct
import sys

from capstone import CS_ARCH_X86, CS_MODE_32, Cs

EXE = r"D:\Program Files\PeG\PeG030.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "out", "call_xrefs.tsv")


def image_base_of(data, e_lfanew):
    magic = struct.unpack_from("<H", data, e_lfanew + 24)[0]
    if magic == 0x10B:      # PE32
        return struct.unpack_from("<I", data, e_lfanew + 24 + 28)[0]
    return struct.unpack_from("<Q", data, e_lfanew + 24 + 24)[0]


def load_sections(path):
    with open(path, "rb") as f:
        data = f.read()
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if data[e_lfanew:e_lfanew + 4] != b"PE\0\0":
        raise SystemExit("not a PE file")
    nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    opt_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    sec0 = e_lfanew + 24 + opt_size
    secs = {}
    for i in range(nsec):
        off = sec0 + i * 40
        name = data[off:off + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, off + 8)
        secs[name] = dict(va=va, vsize=vsize, raw=raw, rawsize=rawsize)
    return data, secs


def build_cache():
    """字节扫描法：直接扫 e8/e9 rel32 与 0f 8x rel32。

    不能用 capstone 线性反汇编：它在数据/坏字节处会失步，整段 .text 一路扫下去
    边界会漂移，导致真实调用点被漏掉（第一版就是这么漏掉 0x4489e5 的）。
    字节扫描没有失步问题，代价是可能有极少数假阳性，逐个 disasm 复核即可。
    """
    data, secs = load_sections(EXE)
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    image_base = image_base_of(data, e_lfanew)
    t = secs[".text"]
    code = data[t["raw"]:t["raw"] + t["rawsize"]]
    base = t["va"] + image_base
    lo, hi = base, base + len(code)
    rows = []
    n = len(code)
    for i in range(n - 5):
        b = code[i]
        tgt = None
        mn = None
        if b == 0xE8:
            rel = struct.unpack_from("<i", code, i + 1)[0]
            tgt = base + i + 5 + rel
            mn = "call"
        elif b == 0xE9:
            rel = struct.unpack_from("<i", code, i + 1)[0]
            tgt = base + i + 5 + rel
            mn = "jmp"
        elif b == 0x0F and 0x80 <= code[i + 1] <= 0x8F:
            rel = struct.unpack_from("<i", code, i + 2)[0]
            tgt = base + i + 6 + rel
            mn = "jcc"
        if tgt is not None and lo <= tgt < hi:
            rows.append((tgt, base + i, mn, "%s 0x%08x" % (mn, tgt)))
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    tmp = CACHE + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("target_hex\tsite_hex\tmn\ttext\n")
        for tgt, site, mn, text in rows:
            f.write("%08x\t%08x\t%s\t%s\n" % (tgt, site, mn, text))
    os.replace(tmp, CACHE)
    print("cache built: %d entries -> %s" % (len(rows), CACHE))
    return rows


def load_cache(rebuild=False):
    if rebuild or not os.path.exists(CACHE):
        return build_cache()
    rows = []
    with open(CACHE, "r", encoding="utf-8") as f:
        next(f, None)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 4:
                rows.append((int(p[0], 16), int(p[1], 16), p[2], p[3]))
    return rows


def main(argv):
    rebuild = "--rebuild" in argv
    targets = []
    for a in argv:
        if a.startswith("--"):
            continue
        a = a.lower().replace("0x", "")
        targets.append(int(a, 16))
    rows = load_cache(rebuild)
    if not targets:
        print("total entries: %d" % len(rows))
        return
    for tgt in targets:
        hits = [(s, mn, tx) for (t, s, mn, tx) in rows if t == tgt]
        print("== target 0x%08x : %d 个引用点" % (tgt, len(hits)))
        for site, mn, tx in sorted(hits):
            print("   0x%08x  %s" % (site, tx))


if __name__ == "__main__":
    main(sys.argv[1:])
