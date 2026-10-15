# -*- coding: utf-8 -*-
"""对一组字符串 VA，列出 .text 中所有引用点，并反汇编其上下文（含对语言目录全局的引用）。"""
import pathlib, struct
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
def read_cstr(va, maxlen=100):
    fo = va2fo(va)
    if fo is None: return None
    e = b.find(b"\0", fo)
    if e < 0: return None
    raw = b[fo:e]
    if not raw or len(raw) > maxlen or any(x < 9 or (13 < x < 32) or x > 126 for x in raw): return None
    return raw.decode("latin1")

for nm, sva, vsz, f, rsz in secs:
    if nm == ".text": T0, T1 = f, f + rsz
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True

TARGETS = {
    "names.txt":        0x90E1B0,
    "TERRAIN.txt":      0x90E1EC,
    "%sSCENARIO\%s":    0x90E1F8,
    "STRINGS_EFILE.txt":0x90E208,
    "TERRAINEX.txt":    0x90E21C,
    "Nations.txt":      0x90C740,
    "equip.txt":        0x90B5B4,
    "%sequip.txt":      0x909FD8,
    "equip.xeqp":       0x90E138,
    "names(x2)":        0x90E1E0,
}
for label, va in TARGETS.items():
    pat = struct.pack("<I", va)
    refs = []
    st = 0
    while True:
        i = b.find(pat, st)
        if i < 0: break
        st = i + 1
        v = fo2va(i)
        if v and T0 <= (v - 0x400000 - 0) + imgbase - imgbase and 0x401000 <= v < 0x878000:
            refs.append(v)
    print("=" * 84)
    print(f"### {label}  VA=0x{va:X}   引用 {len(refs)} 处")
    print("=" * 84)
    for rv in refs:
        # 反汇编从 rv-4 起，确保覆盖指令；并向前找对齐
        fo = va2fo(rv - 30)
        insns = list(md.disasm(b[fo:fo + 80], rv - 30))
        # 找到包含 rv 的指令的下标
        idx = None
        for k, ins in enumerate(insns):
            if ins.address <= rv < ins.address + ins.size:
                idx = k; break
        lo = max(0, (idx or 0) - 8)
        hi = min(len(insns), (idx or 0) + 3)
        print(f"  --- ref @0x{rv:X} ---")
        for k in range(lo, hi):
            ins = insns[k]
            ann = ""
            for op in ins.operands:
                if op.type == 2:
                    s = read_cstr(op.imm & 0xFFFFFFFF)
                    if s: ann = f'  ; "{s}"'
            gl = ""
            if hex(0x11951B0) in ins.op_str: gl = "   <<< LangDir(TEXT-ZH)"
            elif hex(0x11951AC) in ins.op_str: gl = "   <<< EfileRoot"
            mk = " <==" if k == idx else ""
            print(f"      0x{ins.address:08X}  {ins.mnemonic:<7s} {ins.op_str}{ann}{gl}{mk}")
    print()
