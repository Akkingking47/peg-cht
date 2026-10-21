# -*- coding: utf-8 -*-
"""只读静态分析：找出 0x4CCE40 / 0x53D640 两层 1bpp 遮罩缓冲的“使用点”，
并回溯到所在函数与全部 E8 调用点（这层遮罩何时被烘焙进画面）。
用法：python work\\_scratch\\peg\\_find_layer_refs.py
"""
import struct
import sys
import os

EXE = r"D:\Program Files\PeG\PeG030.exe"
IMAGE_BASE = 0x400000
PATTERNS = {0x4CCE40: "遮罩层 A (0x4CCE40)", 0x53D640: "遮罩层 B (0x53D640)",
            0x4CCE2C: "层结构头 (0x4CCE2C)"}

try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)
except Exception:
    md = None


def sections(data):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    secoff = pe + 24 + opt
    out = []
    for i in range(nsec):
        off = secoff + i * 40
        name = data[off:off + 8].rstrip(b"\0").decode("latin1")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, off + 8)
        out.append((name, va, vsize, raw, rawsize))
    return out


def fo2va(secs, fo):
    for name, va, vsize, raw, rawsize in secs:
        if raw <= fo < raw + rawsize:
            return IMAGE_BASE + va + (fo - raw)
    return None


def va2fo(secs, va):
    rva = va - IMAGE_BASE
    for name, sva, vsize, raw, rawsize in secs:
        if sva <= rva < sva + vsize:
            return raw + (rva - sva)
    return None


def func_start(data, secs, va):
    """向前找 55 8B EC 序言"""
    fo = va2fo(secs, va)
    if fo is None:
        return None
    lo = max(0, fo - 0x2000)
    pat = b"\x55\x8b\xec"
    i = fo
    while i > lo:
        j = data.rfind(pat, lo, i)
        if j < 0:
            return None
        return fo2va(secs, j)
    return None


def main():
    data = open(EXE, "rb").read()
    secs = sections(data)
    for name, va, vsize, raw, rawsize in secs:
        print("节 %-8s VA=%08X vsize=%7d raw=%08X" % (name, IMAGE_BASE + va, vsize, raw))
    print()
    for val, label in PATTERNS.items():
        pat = struct.pack("<I", val)
        print("=== %s ===" % label)
        start = 0
        hits = []
        while True:
            i = data.find(pat, start)
            if i < 0:
                break
            start = i + 1
            va = fo2va(secs, i)
            if va is None:
                continue
            hits.append((va, i))
        print("命中 %d 处" % len(hits))
        funcs = {}
        for va, fo in hits:
            fs = func_start(data, secs, va)
            funcs.setdefault(fs, []).append(va)
            print("  VA=%08X  所在函数起始=%s" % (va, ("%08X" % fs) if fs else "?"))
        print("  --- 各函数的 E8 调用点 ---")
        for fs in sorted(funcs, key=lambda x: (x is None, x)):
            if fs is None:
                continue
            tgt_rel = fs
            callers = []
            for fo in range(0, len(data) - 5):
                if data[fo] != 0xE8:
                    continue
                rel = struct.unpack_from("<i", data, fo + 1)[0]
                va = fo2va(secs, fo)
                if va is None:
                    continue
                if (va + 5 + rel) & 0xFFFFFFFF == tgt_rel:
                    callers.append(va)
            print("  函数 %08X 的调用点(%d)：%s" % (fs, len(callers),
                  " ".join("%08X" % c for c in callers[:40]) or "无（可能走跳转表/间接调用）"))
        print()


if __name__ == "__main__":
    main()
