# -*- coding: utf-8 -*-
"""_hexread.py — 只读：以 i16/u16/u8/u32/i32 多视角 dump 一段 .data/.text 数据。

用法：
    python _hexread.py 0x490486 0x4905A6 --i16 8      # 每行 8 个 i16
    python _hexread.py 0x4A0200 0x4A0260 --mix
"""
import struct
import sys

SRC = r"D:\Program Files\PeG\PeG030.exe"
SECS = [(".text", 0x401000, 0x400, 0x8A136),
        (".rdata", 0x48C000, 0x8A600, 0x1017),
        (".data", 0x48E000, 0x8B800, 0x21BF3C),
        (".idata", 0x6AA000, 0xACC00, 0x1434),
        (".rsrc", 0x6AC000, 0xAE200, 0x52DC)]


def va_to_fo(va):
    for _n, sva, raw, size in SECS:
        if sva <= va < sva + size:
            return raw + (va - sva)
    return None


def main():
    lo = int(sys.argv[1], 16)
    hi = int(sys.argv[2], 16)
    per = 8
    if "--i16" in sys.argv:
        per = int(sys.argv[sys.argv.index("--i16") + 1])
    d = open(SRC, "rb").read()
    fo = va_to_fo(lo)
    print("VA 0x%06X..0x%06X  (%d 字节)" % (lo, hi, hi - lo))
    n = hi - lo
    step = per * 2
    for r in range(0, n, step):
        va = lo + r
        f = va_to_fo(va)
        if f is None:
            break
        chunk = d[f:f + min(step, n - r)]
        i16 = struct.unpack_from("<%dh" % (len(chunk) // 2), chunk, 0) if len(chunk) >= 2 else ()
        u8 = list(chunk)
        print("0x%06X | i16: %s | u8: %s" % (
            va, " ".join("%6d" % v for v in i16),
            " ".join("%02X" % b for b in u8)))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
