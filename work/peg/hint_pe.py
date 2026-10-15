# -*- coding: utf-8 -*-
"""hint_pe.py — 提示框逆向分析用的 PE 公共库（只读）。

SECS 与母本节表一致；提供 va/fo 互转、字节/字/dword 读取、capstone 反汇编、
全镜像指针扫描（找引用某 VA 的 dword）。
"""
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

SRC = r"D:\Program Files\PeG\PeG030.exe"
PORT = r"D:\DSH\军事游戏汉化\archive\exe\PeG030-16x9-v10b.exe"
IMAGE_BASE = 0x400000

# 真实节表（prob0_sechdr.py 实测）：
#   name      VA        vsize      raw      rawsize
#   .text   0x401000   0x8A136   0x400    0x8A200
#   .rdata  0x48C000   0x1017    0x8A600  0x1200
#   .data   0x48E000   0x21BF3C  0x8B800  0x21400   <-- vsize >> rawsize：含 ~129KB 零填充 BSS
#   .idata  0x6AA000   0x1434    0xACC00  0x1600
#   .rsrc   0x6AC000   0x52DC    0xAE200  0x5400
# vsize 用于 VA->节 归属；rawsize 用于 FO->节 归属。BSS 区读出来一律是 0（母本与 v10b 都是）。
SECS = [
    (".text",  0x401000, 0x400,   0x8A136),
    (".rdata", 0x48C000, 0x8A600, 0x1017),
    (".data",  0x48E000, 0x8B800, 0x21BF3C),
    (".idata", 0x6AA000, 0xACC00, 0x1434),
    (".rsrc",  0x6AC000, 0xAE200, 0x52DC),
]

_TEXT = next(s for s in SECS if s[0] == ".text")
TEXT_VA, TEXT_FO, TEXT_SIZE = _TEXT[1], _TEXT[2], _TEXT[3]

# 每节的 SizeOfRawData（磁盘上有多少字节；缺的部分读出来是 0）
RAWSIZE = {
    ".text": 0x8A200, ".rdata": 0x1200, ".data": 0x21400,
    ".idata": 0x1600, ".rsrc": 0x5400,
}


def is_bss(va):
    """该 VA 是否落在 .data 节内但超出 rawsize（= 磁盘上全零的 BSS）。"""
    return 0x48E000 + RAWSIZE[".data"] <= va < 0x48E000 + 0x21BF3C


def in_file(va):
    """该 VA 在磁盘上是否真有字节（False = BSS 零填充）。"""
    n = sec_of(va)
    if n is None:
        return False
    sva, raw = next((s[1], s[2]) for s in SECS if s[0] == n)
    return (va - sva) < RAWSIZE[n]



_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = False


def va_to_fo(va):
    for _n, sva, raw, size in SECS:
        if sva <= va < sva + size:
            return raw + (va - sva)
    raise ValueError("VA %#x 不在任何已知节内" % va)


def fo_to_va(fo):
    for _n, sva, raw, size in SECS:
        if raw <= fo < raw + size:
            return sva + (fo - raw)
    raise ValueError("FO %#x 不在任何已知节内" % fo)


def sec_of(va):
    for n, sva, raw, size in SECS:
        if sva <= va < sva + size:
            return n
    return None


def load(path=SRC):
    return open(path, "rb").read()


def u8(d, va):
    return d[va_to_fo(va)]


def u16(d, va):
    return struct.unpack_from("<H", d, va_to_fo(va))[0]


def u32(d, va):
    return struct.unpack_from("<I", d, va_to_fo(va))[0]


def i32(d, va):
    return struct.unpack_from("<i", d, va_to_fo(va))[0]


def blob(d, va, n):
    return d[va_to_fo(va):va_to_fo(va) + n]


def dis(va, n=1, d=None, off=0):
    """反汇编 VA 处 n 条指令；off 允许从 VA 前若干字节开始。"""
    if d is None:
        d = load()
    start = va - off
    fo = va_to_fo(start)
    return list(_md.disasm(d[fo:fo + 15 * max(n, 1) + 32], start))[:n]


def dis_all(lo, hi, d=None):
    """反汇编 [lo,hi)。capstone 5 遇到非法字节就整体返回空，所以逐条解码并在
    失败时前进 1 字节重新同步（与 imm_range.py 同一策略，标记 *resync）。"""
    if d is None:
        d = load()
    fo_lo = va_to_fo(lo)
    buf = d[fo_lo:fo_lo + (hi - lo)]
    out = []
    o = 0
    skipped = 0
    while o < len(buf):
        one = list(_md.disasm(buf[o:o + 16], lo + o, count=1))
        if not one:
            o += 1
            skipped += 1
            continue
        ins = one[0]
        ins.resync = skipped
        out.append(ins)
        skipped = 0
        o += ins.size
    return out


def fmt(ins, n=1):
    return " | ".join("%s %s" % (i.mnemonic, i.op_str) for i in ins[:n])


def find_bytes(d, pat, lo=IMAGE_BASE, hi=None):
    """在文件里找字节串，返回 [(fo, va)]。lo/hi 是 VA 范围限定（默认全文件）。"""
    out = []
    i = d.find(pat)
    while i >= 0:
        try:
            va = fo_to_va(i)
            if va >= lo and (hi is None or va < hi):
                out.append((i, va))
        except ValueError:
            pass
        i = d.find(pat, i + 1)
    return out


def find_dword_refs(d, target):
    """全镜像里值为 target 的 dword 位置（即指针表条目 / 指令立即数）。"""
    pat = struct.pack("<I", target)
    return find_bytes(d, pat)


def find_refs_code_only(d, target):
    """只在 .text 里查该 dword（= push/mov/cmp 的立即数）。"""
    return find_dword_refs(d, target)


def hexdump(d, va, n=32):
    fo = va_to_fo(va)
    out = []
    for r in range(0, n, 16):
        chunk = d[fo + r:fo + r + 16]
        out.append("0x%08X  %-47s  %s" % (va + r, chunk.hex(" "),
                                          "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)))
    return "\n".join(out)


def cstr(d, va, maxlen=512):
    fo = va_to_fo(va)
    end = d.find(b"\x00", fo)
    if end < 0 or end - fo > maxlen:
        end = fo + maxlen
    return d[fo:end]


def cp936(s):
    return s.encode("cp936")
