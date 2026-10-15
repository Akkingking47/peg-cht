# -*- coding: utf-8 -*-
"""对每个 `push LangDir` 引用点，向后（低地址）找最近的
`mov dword ptr [ebp+disp8], imm32`（c7 45 xx xx + imm32），把 imm 解成文件名。

不依赖指令对齐：直接在原始字节里做模式匹配。
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


def read_cstr(va, maxlen=40):
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


SITES = [0x7DC5A0, 0x7DCFF8, 0x7E7236, 0x7E83F5, 0x7E8586]
BACK = 0x80

for site in SITES:
    fo = va2fo(site)
    lo = fo - BACK
    blob = b[lo:fo]
    print("=" * 88)
    print("### push LangDir @ 0x%08X" % site)
    hits = []
    for i in range(len(blob) - 7):
        if blob[i] == 0xC7 and blob[i + 1] == 0x45:
            imm = struct.unpack_from("<I", blob, i + 3)[0]
            s = read_cstr(imm)
            if s:
                hits.append((lo + i, imm, s))
    if hits:
        # 取最后一个（最靠近 site）
        for fo2, imm, s in hits[-3:]:
            print("   mov [ebp+disp8], 0x%08X  ; \"%s\"   (@VA 0x%08X)" % (imm, s, fo2va(fo2)))
        print("   -> 文件名 = \"%s\"" % hits[-1][2])
    else:
        print("   前 0x%X 内无可解析的 mov [ebp+x], <string>" % BACK)
