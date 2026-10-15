# -*- coding: utf-8 -*-
"""枚举：所有以 LangDir(0x11951B0) 为目录去拼文件名的地方。

做法：在 .text 扫 `push 0x11951B0`（68 b0 51 19 01），向后反汇编最多 0x40 字节，
取第一个能解析成可读 ASCII 串的 push imm32 —— 那就是被读取的文件名。
"""
import pathlib
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

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


def read_cstr(va, maxlen=64):
    fo = va2fo(va)
    if fo is None:
        return None
    e = b.find(b"\0", fo)
    if e < 0:
        return None
    raw = b[fo:e]
    if not raw or len(raw) > maxlen:
        return None
    if any(x < 9 or (13 < x < 32) or x > 126 for x in raw):
        return None
    return raw.decode("latin1")


tn, tva, tvsz, tfo, trsz = next(s for s in secs if s[0] == ".text")
text = b[tfo:tfo + trsz]
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

GLOBALS = {
    0x11951B0: "LangDir(TEXT-ZH)",
    0x11951AC: "EfileRoot",
    0x11951A8: "names 首选",
}

pat = b"\x68" + struct.pack("<I", 0x11951B0)
hits = []
i = 0
while True:
    i = text.find(pat, i)
    if i < 0:
        break
    hits.append(tva + i)
    i += 1

print("push LangDir 命中 %d 处\n" % len(hits))
found = {}
for h in hits:
    va = imgbase + h
    fo = va2fo(va)
    code = b[fo:fo + 0x50]
    picked = None
    for ins in md.disasm(code, va):
        if ins.mnemonic == "push" and ins.op_str.startswith("0x"):
            try:
                imm = int(ins.op_str, 16)
            except ValueError:
                continue
            s = read_cstr(imm)
            if s:
                picked = (s, imm, ins.address)
                break
        if ins.address - va > 0x40:
            break
    key = picked[0] if picked else "(未识别)"
    found.setdefault(key, []).append((va, picked))
    print("  0x%08X  ->  %s" % (va, ("push \"%s\" @0x%08X" % (picked[0], picked[2])) if picked else "（后方 0x40 内无字符串）"))

print("\n=== 汇总：从 LangDir 读取的文件名 ===")
for k in sorted(found, key=lambda x: -len(found[x])):
    print("  %-24s x%d   refs=%s" % (k, len(found[k]), ["0x%08X" % v for v, _ in found[k]]))
