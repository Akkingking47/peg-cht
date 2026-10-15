# -*- coding: utf-8 -*-
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

def dump(va_start, n, label):
    print("=" * 78)
    print(f"### {label}  @0x{va_start:X}")
    print("=" * 78)
    fo = va2fo(va_start)
    if fo is None:
        print("  n/a"); return
    for j in range(fo, fo + n, 16):
        row = b[j:j+16]
        hexs = " ".join(f"{x:02X}" for x in row)
        asc = "".join(chr(x) if 32 <= x < 127 else "." for x in row)
        print(f"  0x{(fo2va(j) or 0):08X}  {hexs:<48s} {asc}")

# 1) 读 equip.txt 的函数
dump(0x7BCBC0, 0x80, "读 equip.txt (push 0x90 9FD8 @0x7BCC0C)")
# 2) 读 Nations.txt
dump(0x7DCFB0, 0x70, "读 Nations.txt (push @0x7DCFF3)")
# 3) %sSCENARIO\%s
dump(0x7E8C50, 0x60, "%sSCENARIO\\%s (push @0x7E8C7A)")
# 4) tips
dump(0x7DCB80, 0x50, "%stips%d.txt (push @0x7DCBA1)")

# 5) 引用全局缓冲区 0x11951B0 / 0x11951AC / 0x11951B4
print()
print("=" * 78)
print("### 全局 0x11951B0 / 0x11951AC / 0x11951B4 的引用点")
print("=" * 78)
for gv, lbl in ((0x11951B0, "LangDirBuf"), (0x11951AC, "??"), (0x11951B4, "??")):
    pat = struct.pack("<I", gv)
    hits = []
    st = 0
    while True:
        i = b.find(pat, st)
        if i < 0: break
        va = fo2va(i)
        # 只保留 .text 中的命中
        if va and 0x401000 <= va < 0x878000:
            hits.append((va, b[max(0,i-6):i+6]))
        st = i + 1
    print(f"\n  0x{gv:X} ({lbl}) .text 引用 {len(hits)} 处")
    for va, ctx in hits[:12]:
        print(f"    0x{va:08X}  ctx={ctx.hex(' ')}")
