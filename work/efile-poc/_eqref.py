# -*- coding: utf-8 -*-
import pathlib, struct, re
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
        if sva <= r < sva + vsz: return f + (r - sva)
def fo2va(fo):
    for nm, sva, vsz, f, rsz in secs:
        if f <= fo < f + rsz: return imgbase + sva + (fo - f)
# 找出 .rdata 中所有含 equip/names/nations/strings_efile/fronts 的 C 字符串及 VA
print("### 含关键词的字符串（VA / 内容）")
kw = re.compile(rb"equip|EQUIP|\.eqp|eqp", re.I)
# 扫描 .rdata 与 .data 的字符串
for nm, sva, vsz, f, rsz in secs:
    if nm not in (".rdata", ".data"): continue
    data = b[f:f+rsz]
    for m in re.finditer(rb"[\x20-\x7e]{4,}", data):
        s = m.group()
        if kw.search(s) and len(s) < 80:
            va = imgbase + sva + m.start()
            # 引用
            pat = struct.pack("<I", va)
            hits = []
            st = 0
            while True:
                i = b.find(pat, st)
                if i < 0: break
                v2 = fo2va(i)
                if v2 and 0x401000 <= v2 < 0x878000: hits.append(v2)
                st = i + 1
            print(f"  0x{va:08X} {s.decode('latin1')!r:44s} refs={[hex(h) for h in hits[:6]]}")
