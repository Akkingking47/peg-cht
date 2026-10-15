# -*- coding: utf-8 -*-
"""在 OpenGen.exe 中搜索语言机制相关字符串及其引用点。"""
import pathlib, re, struct

EXE = pathlib.Path(r"D:\OpenPG2\OpenGen.exe")
b = EXE.read_bytes()
print("exe 大小:", len(b))

# PE 段表，用于 VA<->FO 换算
pe = struct.unpack_from("<I", b, 0x3C)[0]
assert b[pe:pe+4] == b"PE\0\0"
nsec = struct.unpack_from("<H", b, pe + 6)[0]
opt = pe + 24
magic = struct.unpack_from("<H", b, opt)[0]
imgbase = struct.unpack_from("<I", b, opt + 28)[0]
print(f"ImageBase=0x{imgbase:X}  段数={nsec}  PE offset=0x{pe:X}")
secs = []
so = opt + struct.unpack_from("<H", b, opt-16+16)[0] if False else opt + 224  # PE32: SizeOfOptionalHeader 从 opt-16+16
# 更稳妥：直接读 SizeOfOptionalHeader
sizeopt = struct.unpack_from("<H", b, pe + 20)[0]
so = opt + sizeopt
for i in range(nsec):
    off = so + i * 40
    nm = b[off:off+8].rstrip(b"\0").decode("latin1")
    vsz, va, rsz, fo = struct.unpack_from("<IIII", b, off + 8)
    secs.append((nm, va, vsz, fo, rsz))
    print(f"  {nm:8s} VA=0x{imgbase+va:X} VS=0x{vsz:X} FO=0x{fo:X} RS=0x{rsz:X}")

def fo2va(fo):
    for nm, va, vsz, f, rsz in secs:
        if f <= fo < f + rsz:
            return imgbase + va + (fo - f)
    return None

def va2fo(va):
    r = va - imgbase
    for nm, sva, vsz, f, rsz in secs:
        if sva <= r < sva + vsz:
            return f + (r - sva)
    return None

print()
targets = [b"TEXT-", b"TEXT_", b"equip.txt", b"names.txt", b"nations.txt",
           b"strings_efile", b"TerrainEx", b"weather.txt", b"fronts.txt",
           b"tips1", b"SCENARIO", b"STRS-", b"strings-", b"OPENGUI"]
for t in targets:
    idxs = [m.start() for m in re.finditer(re.escape(t), b)]
    print(f"{t!r:20s} 命中 {len(idxs)} 处", end="")
    if idxs:
        locs = []
        for i in idxs[:8]:
            va = fo2va(i)
            # 取上下文
            s = max(0, i - 24); e = min(len(b), i + 40)
            ctx = b[s:e].replace(b"\0", b".").decode("latin1")
            locs.append(f"@0x{(va if va else 0):X}(fo 0x{i:X}): ...{ctx}...")
        print()
        for l in locs:
            print("     ", l)
    else:
        print()
