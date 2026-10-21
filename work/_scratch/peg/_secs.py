# -*- coding: utf-8 -*-
"""_secs.py — 只读：从 PE 头解析真实的节表（名称/VA/VSize/FO/RAWSize）。"""
import struct
import sys

SRC = r"D:\Program Files\PeG\PeG030.exe"


def main():
    d = open(SRC, "rb").read()
    print("文件大小 = %d (0x%X)" % (len(d), len(d)))
    e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
    sig = d[e_lfanew:e_lfanew + 4]
    print("e_lfanew = 0x%X  sig=%r" % (e_lfanew, sig))
    coff = e_lfanew + 4
    nsec, = struct.unpack_from("<H", d, coff + 2)
    optsz, = struct.unpack_from("<H", d, coff + 16)
    print("NumberOfSections = %d  SizeOfOptionalHeader = 0x%X" % (nsec, optsz))
    opt = coff + 20
    magic, = struct.unpack_from("<H", d, opt)
    print("OptionalHeader.Magic = 0x%X" % magic)
    if magic == 0x10B:
        imgbase, = struct.unpack_from("<I", d, opt + 28)
        print("ImageBase = 0x%X" % imgbase)
    so = opt + optsz
    print("%-10s %-10s %-10s %-10s %-10s %-10s" % ("name", "VA", "VSize", "FO", "RAWSize", "flags"))
    for i in range(nsec):
        o = so + i * 40
        nm = d[o:o + 8].rstrip(b"\x00").decode("ascii", "replace")
        vsz, va, rsz, fo = struct.unpack_from("<IIII", d, o + 8)
        fl, = struct.unpack_from("<I", d, o + 36)
        print("%-10s 0x%08X 0x%08X 0x%08X 0x%08X 0x%08X" % (nm, va, vsz, fo, rsz, fl))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
