# -*- coding: utf-8 -*-
"""分析 exe 提示串块：每条串的出现次数 / push 引用数 / 是否可安全改（唯一引用）"""
import struct, re, io, sys

EXE = r"D:/OpenPG2/OpenGen.exe"
d = open(EXE, "rb").read()
pe = struct.unpack_from("<I", d, 0x3C)[0]
nsec = struct.unpack_from("<H", d, pe + 6)[0]
szopt = struct.unpack_from("<H", d, pe + 20)[0]
opt = pe + 24
IB = struct.unpack_from("<I", d, opt + 28)[0]
sh = opt + szopt
secs = []
for i in range(nsec):
    o = sh + i * 40
    nm = d[o:o + 8].rstrip(b"\x00").decode()
    vsz, rva, rsz, fo = struct.unpack_from("<IIII", d, o + 8)
    secs.append((nm, rva, vsz, fo, rsz))

def fo2va(fo):
    for n, sva, vsz, f0, rsz in secs:
        if f0 <= fo < f0 + rsz:
            return sva + (fo - f0) + IB
    return None
def va2fo(va):
    rva = va - IB
    for n, sva, vsz, f0, rsz in secs:
        if sva <= rva < sva + max(vsz, rsz):
            return f0 + (rva - sva)
    return None

# push 索引
TEXT_FO0, TEXT_FO1 = secs[0][3], secs[0][3] + secs[0][4]
push = {}
for i in range(TEXT_FO0, TEXT_FO1 - 5):
    if d[i] == 0x68:
        v = struct.unpack_from("<I", d, i + 1)[0]
        if IB <= v < 0x10000000:
            push.setdefault(v, []).append(i)

# dump 串块
VA0, VA1 = 0x911E80, 0x912340
b = d[va2fo(VA0):va2fo(VA1)]
cur = b""; addr = VA0; items = []
for i, ch in enumerate(b):
    if ch == 0:
        if cur:
            items.append((addr, cur))
        cur = b""; addr = VA0 + i + 1
    else:
        cur += bytes([ch])

FMT = re.compile(r"%[-+ 0-9.#]*[dsfxc]")
print("共 %d 条\n" % len(items))
print("%-9s %-4s %-4s %-4s %-4s  %s" % ("VA", "len", "出现", "push", "空洞", "串"))
rows = []
for va, raw in items:
    s = raw.decode("latin-1")
    fo = va2fo(va)
    occ = d.count(raw + b"\x00")
    nref = len(push.get(va, []))
    # 原地改是否可能：译文 <= 原长
    rows.append((va, fo, len(raw), occ, nref, s))
    print("%08X %4d %4d %4d %4s  %s" % (va, len(raw), occ, nref, "", repr(s)))
print()
print("=== 唯一 push 引用（可安全改）===")
safe = [r for r in rows if r[4] == 1]
print("  %d / %d" % (len(safe), len(rows)))
print("=== 无 push 引用 ===")
noref = [r for r in rows if r[4] == 0]
for r in noref:
    print("   %08X  %r" % (r[0], r[5]))
print("=== 多引用 ===")
multi = [r for r in rows if r[4] > 1]
for r in multi:
    print("   %08X  x%d  %r" % (r[0], r[4], r[5]))
