# -*- coding: utf-8 -*-
"""Find how OpenGen.exe resolves the scenario .ply path:
does it use LangDir (TEXT-XX, 0x11951B0) or EfileRoot (0x11951AC)?"""
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
so = opt + sizeopt
secs = []
for i in range(nsec):
    off = so + i * 40
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


def read_cstr(va, maxlen=120):
    fo = va2fo(va)
    if fo is None:
        return None
    e = b.find(b"\0", fo)
    if e < 0:
        return None
    raw = b[fo:e]
    if not raw or len(raw) > maxlen:
        return None
    return raw.decode("latin1")

LANGDIR = 0x11951B0
EFILEROOT = 0x11951AC
GAMEROOT = 0x11951A8

print("=== all '.ply' / '.plv' / '.pll' string literals in the exe ===")
targets = []
for pat in (b".ply", b".plv", b".pll", b"_i.ply", b"_v.ply", b"_l.ply"):
    start = 0
    while True:
        p = b.find(pat, start)
        if p < 0:
            break
        start = p + 1
        va = fo2va(p)
        if va:
            # walk back to the start of the string
            q = p
            while q > 0 and 32 <= b[q - 1] < 127:
                q -= 1
            s = b[q:b.find(b"\0", p)]
            try:
                s = s.decode("latin1")
            except Exception:
                continue
            if len(s) < 40:
                print("  FO 0x%06X  VA 0x%08X  %r" % (q, fo2va(q) or 0, s))
                targets.append((fo2va(q), s))
        if len(targets) > 40:
            break

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

print("\n=== code refs to those VAs (push imm32) ===")
text = None
for nm, sva, vsz, f, rsz in secs:
    if nm == ".text":
        text = (f, vsz, sva)
        break
tf, tsz, tva = text
code = b[tf:tf + tsz]
for va, s in targets[:12]:
    needle = struct.pack("<I", va)
    idx = 0
    found = []
    while True:
        p = code.find(needle, idx)
        if p < 0:
            break
        idx = p + 1
        # check for push imm32 opcode 0x68
        if p >= 1 and code[p - 1] == 0x68:
            found.append(tva + p - 1)
    if found:
        print("  %-24r -> %s" % (s, ["0x%08X" % x for x in found]))
