# -*- coding: utf-8 -*-
"""_w.py — 只读：按 VA 读原始数据（i16/u16/u32/i32/bytes）。

用法：
    python _w.py 0x622D40 --i16 8
    python _w.py 0x4AF45C --u32 4
    python _w.py 0x490470 --bytes 32
"""
import struct
import sys

SRC = r"D:\Program Files\PeG\PeG030.exe"
SECS = [(".text", 0x401000, 0x400, 0x8A200),
        (".rdata", 0x48C000, 0x8A600, 0x1200),
        (".data", 0x48E000, 0x8B800, 0x21400),
        (".idata", 0x6AA000, 0xACC00, 0x1600),
        (".rsrc", 0x6AC000, 0xAE200, 0x5400)]


def va_to_fo(va):
    for _n, sva, raw, size in SECS:
        if sva <= va < sva + size:
            return raw + (va - sva)
    return None


def main():
    va = int(sys.argv[1], 16)
    kind, n = "i16", 8
    for i, a in enumerate(sys.argv):
        if a in ("--i16", "--u16", "--u32", "--i32", "--bytes", "--f32"):
            kind = a[2:]
            n = int(sys.argv[i + 1])
    fo = va_to_fo(va)
    if fo is None:
        print("VA 0x%06X 不在任何节内（可能是 BSS，磁盘上不存在）" % va)
        return
    fmt = {"i16": "h", "u16": "H", "u32": "I", "i32": "i", "f32": "f"}.get(kind)
    if kind == "bytes":
        chunk = open(SRC, "rb").read()[fo:fo + n]
        print("VA 0x%06X bytes: %s" % (va, " ".join("%02X" % b for b in chunk)))
        return
    vals = struct.unpack_from("<%d%s" % (n, fmt), open(SRC, "rb").read(), fo)
    print("VA 0x%06X %s[%d]: %s" % (va, kind, n, " ".join(str(v) for v in vals)))
    if kind in ("i16", "u16"):
        print("            hex:  %s" % " ".join("%04X" % (v & 0xFFFF) for v in vals))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
