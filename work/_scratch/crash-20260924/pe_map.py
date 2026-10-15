# -*- coding: utf-8 -*-
"""解析 PE 数据目录 / 段表，定位 VA 0x91D940 究竟落在哪个结构里。"""
import struct
import sys

DIRNAMES = ["Export", "Import", "Resource", "Exception", "Security", "BaseReloc",
            "Debug", "Arch", "GlobalPtr", "TLS", "LoadConfig", "BoundImport",
            "IAT", "DelayImport", "CLR", "Reserved"]

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\DSH\军事游戏汉化\backup\OpenGen.exe.original"
d = open(path, "rb").read()
pe = struct.unpack_from("<I", d, 0x3C)[0]
assert d[pe:pe + 4] == b"PE\0\0", "非 PE"
print("PE 头 FO 0x%X" % pe)
nsec, = struct.unpack_from("<H", d, pe + 6)
ts, = struct.unpack_from("<I", d, pe + 8)
opt = pe + 24
magic, = struct.unpack_from("<H", d, opt)
print("magic=%04X  TimeDateStamp=0x%08X (%d 段)" % (magic, ts, nsec))
sects = []
sec_off = opt + struct.unpack_from("<H", d, pe + 20)[0]
for i in range(nsec):
    o = sec_off + 40 * i
    name = d[o:o + 8].rstrip(b"\0").decode("latin-1")
    vsize, va = struct.unpack_from("<II", d, o + 8)
    rsize, rptr = struct.unpack_from("<II", d, o + 16)
    chars, = struct.unpack_from("<I", d, o + 36)
    sects.append((name, va, vsize, rptr, rsize, chars))
    print("  %-8s VA %08X virt %08X   RO  %08X raw %08X  chars %08X"
          % (name, va, vsize, rptr, rsize, chars))


def rva2fo(rva):
    for n, va, vs, rp, rs, ch in sects:
        if va <= rva < va + max(vs, rs):
            return rp + (rva - va), n
    return None, "?"


ndir, = struct.unpack_from("<I", d, opt + 92)
print("\n数据目录 %d 项:" % ndir)
dirs = []
for i in range(ndir):
    rva, size = struct.unpack_from("<II", d, opt + 96 + 8 * i)
    if not rva:
        continue
    fo, sec = rva2fo(rva)
    dirs.append((i, rva, size, fo, sec))
    print("  [%2d] %-12s RVA %08X..%08X  size %7d  FO %s .. %s  (%s)"
          % (i, DIRNAMES[i], rva, rva + size, size,
             "0x%X" % fo if fo else "?", "0x%X" % (fo + size) if fo else "?", sec))

TARGETS = [0x91D940, 0x91D931, 0x9148D8, 0x8ED939, 0x8B2A86]
print("\n目标 VA 归属:")
for t in TARGETS:
    hit = [x for x in dirs if x[1] <= t < x[1] + max(x[2], 0)]
    fo, sec = rva2fo(t)
    print("  0x%08X  %s  FO %s  -> %s" % (t, sec, "0x%X" % fo if fo else "?",
          ", ".join("%s(偏移+0x%X/0x%X)" % (DIRNAMES[x[0]], t - x[1], x[2])
                    for x in hit) or "不在任何目录范围"))

# 导入描述符数组（20 字节一项，全 0 结尾）
imp = [x for x in dirs if x[0] == 1]
if imp:
    _, rva, size, fo, _ = imp[0]
    print("\n导入描述符数组 (%d 项, RVA %08X FO 0x%X):" % (size // 20, rva, fo))
    for k in range(size // 20):
        e = fo + 20 * k
        oft, tds, fwd, name, ft = struct.unpack_from("<IIIII", d, e)
        s = ""
        if name:
            nfo, _ = rva2fo(name)
            if nfo:
                s = d[nfo:d.find(b"\0", nfo)].decode("latin-1", "replace")
        print("   [%d] VA %08X  OFT %08X TDS %08X FwdChain %08X Name 0x%08X FT %08X %s"
              % (k, rva + 20 * k, oft, tds, fwd, name, ft, s))

dbg = [x for x in dirs if x[0] == 6]
if dbg:
    _, rva, size, fo, _ = dbg[0]
    print("\n调试目录 (%d 项 x32B, RVA %08X FO 0x%X):" % (size // 28, rva, fo))
    for k in range(size // 28):
        e = fo + 28 * k
        ch, t, mv, mnv, ty, sd, addr, ptr = struct.unpack_from("<IIHHIIII", d, e)
        nfo, _ = rva2fo(addr)
        tag = d[nfo:nfo + 4] if nfo else b""
        print("   [%d] VA %08X Type %d Size %d AddrOfRaw 0x%08X PtrRaw 0x%X tag=%r"
              % (k, rva + 28 * k, ty, sd, addr, ptr, tag))
