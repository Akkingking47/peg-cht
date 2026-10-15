# -*- coding: utf-8 -*-
"""定位资源文件名（TerrainEx.txt / Weather.txt / ...）的引用点，并识别所用目录全局。

思路：
 1) 在文件里找 ASCII 串，算出 VA；
 2) 在 .text 里扫 `push imm32`（0x68 + 4 字节小端）命中该 VA；
 3) 从引用点向前反汇编 0x40 字节，抓取引用的数据全局（mov reg,[abs] / mov ecx,[abs]）。
"""
import pathlib
import struct

EXE = pathlib.Path(r"D:\OpenPG2\OpenGen.exe")
b = EXE.read_bytes()
pe = struct.unpack_from("<I", b, 0x3C)[0]
sizeopt = struct.unpack_from("<H", b, pe + 20)[0]
nsec = struct.unpack_from("<H", b, pe + 6)[0]
opt = pe + 24
imgbase = struct.unpack_from("<I", b, opt + 28)[0]
secs = []
for i in range(nsec):
    off = opt + sizeopt + i * 40
    nm = b[off:off + 8].rstrip(b"\0").decode("latin1")
    vsz, va, rsz, fo = struct.unpack_from("<IIII", b, off + 8)
    secs.append((nm, va, vsz, fo, rsz))


def va2fo(va):
    r = va - imgbase
    for nm, sva, vsz, f, rsz in secs:
        if sva <= r < sva + vsz:
            return f + (r - sva)
    return None


def fo2va(fo):
    for nm, sva, vsz, f, rsz in secs:
        if f <= fo < f + rsz:
            return imgbase + sva + (fo - f)
    return None


def find_strings(needle):
    """返回该 ASCII 串（以 NUL 结尾，前面是 NUL）的全部 VA。"""
    out = []
    pat = needle.encode("ascii")
    i = 0
    while True:
        i = b.find(pat, i)
        if i < 0:
            break
        if b[i - 1] == 0 and b[i + len(pat)] == 0:
            va = fo2va(i)
            if va:
                out.append(va)
        i += 1
    return out


TEXT = next(s for s in secs if s[0] == ".text")
tn, tva, tvsz, tfo, trsz = TEXT
text = b[tfo:tfo + trsz]


def find_pushes(va):
    """在 .text 里找 push imm32 命中 va 的位置（返回 VA 列表）。"""
    pat = b"\x68" + struct.pack("<I", va)
    out = []
    i = 0
    while True:
        i = text.find(pat, i)
        if i < 0:
            break
        out.append(imgbase + tva + i)
        i += 1
    return out


def window_refs(va_ref, back=0x50):
    """反汇编 ref 之前 back 字节，收集绝对地址引用。"""
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    fo = va2fo(va_ref - back)
    code = b[fo:fo + back + 6]
    lines = []
    for ins in md.disasm(code, va_ref - back):
        ann = ""
        for op in ins.operands:
            # x86 mem operand: type 3
            if op.type == 3 and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp:
                ann = "  ; [0x%08X]" % (op.mem.disp & 0xFFFFFFFF)
        lines.append("      0x%08X  %-24s %s %s%s" % (
            ins.address, ins.bytes.hex(" "), ins.mnemonic, ins.op_str, ann))
    return lines


KNOWN = {
    0x11951AC: "EfileRoot",
    0x11951B0: "LangDir(TEXT-ZH)",
    0x11951A8: "names 首选目录",
}

TARGETS = ["TerrainEx.txt", "Weather.txt", "Terrain.txt", "equip.txt",
           "tips1.txt", "tips.txt", "names.txt", "Nations.txt", "strings_efile.txt"]

for t in TARGETS:
    vas = find_strings(t)
    print("=" * 90)
    print("### %s   字符串 VA: %s" % (t, ["0x%08X" % v for v in vas] or "（未找到）"))
    for v in vas:
        for p in find_pushes(v):
            print("  push @ 0x%08X" % p)
            for ln in window_refs(p):
                print(ln)
            print("  " + "-" * 60)
