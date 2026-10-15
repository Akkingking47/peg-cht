# -*- coding: utf-8 -*-
"""搜索 push imm32 对关键字符串的引用点，并 dump 附近代码的字节。"""
import pathlib, struct

EXE = pathlib.Path(r"D:\OpenPG2\OpenGen.exe")
b = EXE.read_bytes()
pe = struct.unpack_from("<I", b, 0x3C)[0]
sizeopt = struct.unpack_from("<H", b, pe + 20)[0]
nsec = struct.unpack_from("<H", b, pe + 6)[0]
opt = pe + 24
imgbase = struct.unpack_from("<I", b, opt + 28)[0]
so = opt + sizeopt
secs = []
for i in range(nsec):
    off = so + i * 40
    nm = b[off:off+8].rstrip(b"\0").decode("latin1")
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

TARGETS = {
    "TEXT-":        0x90C6BC,
    "STRINGS-":     0x90C6C4,
    "%s%s\\":       0x90C6D0,
    "%sequip.txt":  0x909FD8,
    "%sSCENARIO\\%s": 0x90E1F8,
    "STRINGS_EFILE.txt": 0x90E208,
    "Nations.txt":  0x90C740,
    "%stips%d.txt": 0x90C774,
}

for name, va in TARGETS.items():
    pat = b"\x68" + struct.pack("<I", va)
    hits = []
    start = 0
    while True:
        i = b.find(pat, start)
        if i < 0: break
        hits.append(i); start = i + 1
    print(f"{name!r:22s} VA=0x{va:X}  push 引用 {len(hits)} 处: " +
          ", ".join(f"0x{fo2va(h):X}" if fo2va(h) else f"fo0x{h:X}" for h in hits))
print()
print("=" * 72)
print("TEXT- 引用点上下文（±40 字节）")
print("=" * 72)
va = 0x90C6BC
pat = b"\x68" + struct.pack("<I", va)
start = 0
while True:
    i = b.find(pat, start)
    if i < 0: break
    start = i + 1
    s = max(0, i - 48); e = min(len(b), i + 64)
    va_s = fo2va(s)
    print(f"\n--- push @ VA 0x{(fo2va(i) or 0):X} ---")
    # 按 16 字节一行打印
    for j in range(s, e, 16):
        row = b[j:j+16]
        hexs = " ".join(f"{x:02X}" for x in row)
        asc = "".join(chr(x) if 32 <= x < 127 else "." for x in row)
        mark = "  <== push" if j <= i < j + 16 else ""
        print(f"  0x{(fo2va(j) or 0):08X}  {hexs:<48s} {asc}{mark}")
