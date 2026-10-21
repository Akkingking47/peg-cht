# -*- coding: utf-8 -*-
"""通用只读 xref：扫 .text 里对某个绝对地址的 disp32 引用，打印上下文指令与所在函数。
用法：python work\\_scratch\\peg\\_xref_addr.py 0x686FD4 [0x622D4A ...]
"""
import struct
import sys

EXE = r"D:\Program Files\PeG\PeG030.exe"
IMAGE_BASE = 0x400000

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


def text_range(secs):
    for name, va, vsize, raw, rawsize in secs:
        if name == ".text":
            return IMAGE_BASE + va, IMAGE_BASE + va + vsize
    return 0, 0


def func_start(data, secs, va):
    fo = va2fo(secs, va)
    lo = max(0, fo - 0x3000)
    j = data.rfind(b"\x55\x8b\xec", lo, fo)
    return fo2va(secs, j) if j >= 0 else None


def callers_of(data, secs, target):
    lo, hi = text_range(secs)
    out = []
    for fo in range(0, len(data) - 5):
        if data[fo] != 0xE8:
            continue
        va = fo2va(secs, fo)
        if va is None or not (lo <= va < hi):
            continue
        rel = struct.unpack_from("<i", data, fo + 1)[0]
        if (va + 5 + rel) & 0xFFFFFFFF == target:
            out.append(va)
    return out


def main():
    data = open(EXE, "rb").read()
    secs = sections(data)
    for arg in sys.argv[1:]:
        addr = int(arg, 16)
        pat = struct.pack("<I", addr)
        print("=== 引用 %08X 的 .text 位置 ===" % addr)
        hits = []
        start = 0
        while True:
            i = data.find(pat, start)
            if i < 0:
                break
            start = i + 1
            va = fo2va(secs, i)
            if va is None or va < 0x401000 or va > 0x48B136:
                continue
            hits.append(va)
        print("命中 %d 处" % len(hits))
        groups = {}
        for va in hits:
            fs = func_start(data, secs, va)
            groups.setdefault(fs, []).append(va)
            fo = va2fo(secs, va) - 20
            code = data[fo:fo + 32]
            va_start = fo2va(secs, fo)
            print("  --- 命中 %08X（函数 %s）上下文 ---" % (va, ("%08X" % fs) if fs else "?"))
            if md:
                for ins in md.disasm(code, va_start):
                    mark = "  <== 引用" if ins.address <= va < ins.address + ins.size else ""
                    print("      %08X  %-20s %s %s%s" % (ins.address, ins.bytes.hex(),
                                                         ins.mnemonic, ins.op_str, mark))
        print("  --- 各函数的 E8 调用点 ---")
        for fs in sorted([g for g in groups if g]):
            cs = callers_of(data, secs, fs)
            print("    %08X ← %s" % (fs, " ".join("%08X" % c for c in cs[:30]) or "无"))
        print()


if __name__ == "__main__":
    main()
