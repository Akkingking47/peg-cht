# -*- coding: utf-8 -*-
"""空洞候选扫描：在 .rdata/.data 的 raw 区里找连续 NUL 段，并排除
  ① 任何 PE 数据目录覆盖的范围（**这是这次踩的坑**）
  ② 被当作 4 字节指针/立即数引用过的位置
输出按长度降序的候选清单。
"""
import struct
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else r"D:\DSH\军事游戏汉化\backup\OpenGen.exe.original"
MINSIZE = 32
d = open(EXE, "rb").read()

pe = struct.unpack_from("<I", d, 0x3C)[0]
nsec, = struct.unpack_from("<H", d, pe + 6)
opt = pe + 24
sec_off = opt + struct.unpack_from("<H", d, pe + 20)[0]
sects = []
for i in range(nsec):
    o = sec_off + 40 * i
    name = d[o:o + 8].rstrip(b"\0").decode("latin-1")
    vsize, va = struct.unpack_from("<II", d, o + 8)
    rsize, rptr = struct.unpack_from("<II", d, o + 16)
    sects.append((name, va, vsize, rptr, rsize))


def rva2fo(rva):
    for n, va, vs, rp, rs in sects:
        if va <= rva < va + max(vs, rs):
            return rp + (rva - va), n
    return None, "?"


DIRNAMES = ["Export", "Import", "Resource", "Exception", "Security", "BaseReloc",
            "Debug", "Arch", "GlobalPtr", "TLS", "LoadConfig", "BoundImport",
            "IAT", "DelayImport", "CLR", "Reserved"]
ndir, = struct.unpack_from("<I", d, opt + 92)
forbidden = []
print("== 数据目录（禁区） ==")
for i in range(ndir):
    rva, size = struct.unpack_from("<II", d, opt + 96 + 8 * i)
    if not rva or not size:
        continue
    fo, sec = rva2fo(rva)
    if fo is None:
        continue
    # 目录条目本身在文件中的位置也可能被读：扩 32 字节余量
    forbidden.append((fo - 32, fo + size + 32, DIRNAMES[i]))
    print("  %-12s FO 0x%X..0x%X  VA 0x%X..0x%X" %
          (DIRNAMES[i], fo, fo + size, rva + 0x400000, rva + size + 0x400000))


# 预建「全 exe 中出现的、形如镜像内 VA 的 4 字节值」集合，用于 O(1) 引用检查
IMG_LO, IMG_HI = 0x400000, 0x1900000
VAS = set()
_mv = int.from_bytes
for _o in range(0, len(d) - 3):
    _v = _mv(d[_o:_o + 4], "little")
    if IMG_LO <= _v < IMG_HI:
        VAS.add(_v)
print("镜像内 VA 形态的 4 字节值: %d 个" % len(VAS))


def blocked(fo):
    for a, b, n in forbidden:
        if a <= fo < b:
            return n
    return None


print("\n== 连续 NUL 候选 (>=%d B) ==" % MINSIZE)
cands = []
for name, va, vs, rp, rs in sects:
    if name not in (".rdata", ".data"):
        continue
    base = rp
    end = rp + rs
    i = base
    while i < end:
        if d[i] == 0:
            j = i
            while j < end and d[j] == 0:
                j += 1
            if j - i >= MINSIZE:
                cands.append((j - i, i, va + (i - rp), name))
            i = j
        else:
            i += 1

cands.sort(reverse=True)
for ln, fo, tva, sec in cands:
    blk = blocked(fo)
    blk_end = blocked(fo + ln - 1)
    if blk or blk_end:
        tag = "!! 命中目录 %s" % (blk or blk_end)
    else:
        tag = "OK"
    # 引用检查：段内每个 4 字节对齐位置的 VA 值，全 exe 出现次数
    refs = sum(1 for off in range(0, ln - 3, 4) if (tva + off) in VAS)
    if refs:
        tag += "  | 被引用 %d 次(段内 4B 对齐点)" % refs
    print("  %5d B  FO 0x%06X  VA 0x%08X  %s  %s" % (ln, fo, tva, sec, tag))
