# -*- coding: utf-8 -*-
"""dump exe 中关键字符串区的完整 C 字符串。"""
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

def dump_zone(va_start, va_end, label):
    print("=" * 72)
    print(f"### {label}  VA 0x{va_start:X}–0x{va_end:X}")
    print("=" * 72)
    fo = va2fo(va_start); fo_end = va2fo(va_end)
    if fo is None:
        print("  VA 无法换算"); return
    data = b[fo:fo_end]
    # 切分 C 字符串
    cur = bytearray(); start = 0
    for i, ch in enumerate(data + b"\0"):
        if ch == 0:
            if cur:
                s = bytes(cur).decode("latin1")
                if len(s) >= 2 and all(32 <= ord(c) < 127 or c in "\t" for c in s):
                    print(f"  0x{va_start+i-len(cur):08X}  {s!r}")
            cur = bytearray()
        else:
            cur.append(ch)

dump_zone(0x90C640, 0x90C780, "TEXT- / STRINGS- 邻域")
dump_zone(0x909F80, 0x90A040, "equip.txt 邻域")
dump_zone(0x90E1A0, 0x90E240, "names.txt 邻域")
dump_zone(0x8FD040, 0x8FD0A0, "strings- 邻域")
