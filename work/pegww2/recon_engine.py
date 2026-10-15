#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段0.2 引擎识别：PE 结构 / 导入表 / 文本 stem / 已知补丁落点比对。

用法:
    python recon_engine.py [游戏目录] [--ref 参照exe目录]

判据全部实测输出，不做推断。
"""
import hashlib
import os
import struct
import sys

GAME = r"D:\Program Files\PeG-WW2"
REFDIR = r"D:\Program Files\PeG"

# PeG030.exe 已实测落点（VA），来自 docs\38 与技能 ssi-modgen-peg-localization
KNOWN_VA = {
    "iCharSet(push imm)": 0x4718E3,       # 6A 00 -> 6A 86
    "_pctype table": 0x4ABA8A,            # 256 x WORD
    "__mbcodepage": 0x4ABC8C,             # 1 -> 936
    "date_LCID(mov eax)": 0x7BE86,        # A1 48 91 49 00 -> B8 04 08 00 00
    "lineterm_patch#1": 0x4AA08A,         # 行终止类别表(128B区)
    "labeldrop_patch#2": 0x46FF1C,        # 7C 08 -> EB 00
    "CreateFontA_FO_ref": 0x70CFA,        # 参照: FO 0x70CFA = VA 0x4718FA
}

IMPORTS_OF_INTEREST = [
    b"CreateFontA", b"DrawTextExA", b"GetDateFormatA", b"GetLocaleInfoA",
    b"MultiByteToWideChar", b"GetCPInfo", b"GetStringTypeA", b"GetACP",
    b"IsDBCSLeadByte", b"CharNextA", b"AnsiNext", b"CreateFontIndirectA",
    b"GetTextExtentPoint32A", b"TextOutA", b"GetCharWidth32A",
]

STEMS = [b"gui030", b"gui031", b"gui97", b"gui98", b"Equip30", b"Equip31",
         b"Equip97", b"Equip98", b"misc030", b"misc98", b"name030", b"tips030",
         b"tips97", b"tips98",
         b"WW2Gui", b"WW2Misc", b"WW2NAME", b"WW2Tips", b"ww2-eqp", b"WW2GEN",
         b"WW2", b"People", b"PEOPLES"]


class PE:
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            self.data = f.read()
        d = self.data
        self.ok = False
        if d[:2] != b"MZ":
            return
        e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
        if d[e_lfanew:e_lfanew + 4] != b"PE\0\0":
            return
        coff = e_lfanew + 4
        self.machine, self.nsec = struct.unpack_from("<HH", d, coff)
        (self.timestamp,) = struct.unpack_from("<I", d, coff + 4)
        (self.opt_size,) = struct.unpack_from("<H", d, coff + 16)
        (self.characteristics,) = struct.unpack_from("<H", d, coff + 18)
        opt = coff + 20
        self.magic = struct.unpack_from("<H", d, opt)[0]
        self.image_base = struct.unpack_from("<I", d, opt + 28)[0]
        self.sections = []
        sec = opt + self.opt_size
        for i in range(self.nsec):
            o = sec + i * 40
            name = d[o:o + 8].rstrip(b"\0")
            vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", d, o + 8)
            self.sections.append({
                "name": name.decode("latin1"), "vsize": vsize, "vaddr": vaddr,
                "rsize": rsize, "raddr": raddr,
                "va_delta": vaddr - self.image_base,
            })
        self.ok = True
        self._imports()

    def va2fo(self, va):
        if self.magic == 0x10B:
            rva = va - self.image_base
        else:
            rva = va - self.image_base
        for s in self.sections:
            if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rsize"]):
                return s["raddr"] + (rva - s["vaddr"])
        return None

    def _imports(self):
        self.imports = set()
        try:
            if self.magic == 0x10B:
                dd = 0x60 + 96  # OptionalHeader: DataDirectory[1] = Import
                imp_rva, imp_sz = struct.unpack_from("<II", self.data, self._opt_off() + 104)
            else:
                imp_rva, imp_sz = struct.unpack_from("<II", self.data, self._opt_off() + 120)
            if not imp_rva:
                return
            off = self._rva2fo(imp_rva)
            n = 0
            while n < 64:
                ent = off + n * 20
                if ent + 20 > len(self.data):
                    break
                oft, tstamp, fwd, name_rva, first = struct.unpack_from("<IIIII", self.data, ent)
                if name_rva == 0 and first == 0:
                    break
                no = self._rva2fo(name_rva)
                if no:
                    end = self.data.index(b"\0", no)
                    self.imports.add(self.data[no:end])
                n += 1
        except Exception:
            pass

    def _opt_off(self):
        e_lfanew = struct.unpack_from("<I", self.data, 0x3C)[0]
        return e_lfanew + 4 + 20

    def _rva2fo(self, rva):
        for s in self.sections:
            if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rsize"]):
                return s["raddr"] + (rva - s["vaddr"])
        return None

    def strings(self, minlen=5):
        out, cur = set(), bytearray()
        for b in self.data:
            if 32 <= b < 127:
                cur.append(b)
            else:
                if len(cur) >= minlen:
                    out.add(bytes(cur))
                cur = bytearray()
        if len(cur) >= minlen:
            out.add(bytes(cur))
        return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    game = args[0] if args else GAME
    ref = REFDIR
    if "--ref" in sys.argv:
        ref = sys.argv[sys.argv.index("--ref") + 1]

    exes = []
    for root, dirs, files in os.walk(game):
        for f in files:
            if f.lower().endswith(".exe"):
                exes.append(os.path.join(root, f))
    refs = []
    if os.path.isdir(ref):
        for f in os.listdir(ref):
            if f.lower().endswith(".exe") or f.lower().endswith(".orig-backup"):
                refs.append(os.path.join(ref, f))

    print("=" * 100)
    print("A. 参照组（已实测过的 PeG）")
    print("=" * 100)
    refmap = {}
    for p in sorted(refs):
        pe = PE(p)
        if not pe.ok:
            continue
        h = hashlib.sha256(pe.data).hexdigest()[:16]
        refmap[os.path.basename(p)] = (h, pe)
        print(f"{os.path.basename(p):40s} {len(pe.data):>9d}  ts={pe.timestamp}  sha={h}  IB={pe.image_base:#x}")
        print(f"    sections: " + " | ".join(f"{s['name']}@{s['vaddr']:#x}/{s['vsize']:#x}->{s['raddr']:#x}" for s in pe.sections))

    print()
    print("=" * 100)
    print("B. 目标组（PeG-WW2）")
    print("=" * 100)
    for p in sorted(exes):
        pe = PE(p)
        if not pe.ok:
            print(f"{os.path.basename(p):40s} <非 PE 或不可读>")
            continue
        h = hashlib.sha256(pe.data).hexdigest()[:16]
        dup = ""
        for rn, (rh, _) in refmap.items():
            if rh == h:
                dup = f"  << 与参照 {rn} 完全相同"
        print(f"{os.path.basename(p):40s} {len(pe.data):>9d}  ts={pe.timestamp}  sha={h}  IB={pe.image_base:#x}{dup}")
        print(f"    sections: " + " | ".join(f"{s['name']}@{s['vaddr']:#x}/{s['vsize']:#x}->{s['raddr']:#x}" for s in pe.sections))

        strs = pe.strings()
        hits = [s.decode() for s in STEMS if s in strs]
        print(f"    文本 stem 命中: {hits if hits else '（无）'}")
        ihits = [s.decode() for s in IMPORTS_OF_INTEREST if any(s == i for i in pe.imports)]
        # 导入表里逐个 dll 的符号：用子串近似
        ihits2 = sorted({s.decode() for s in IMPORTS_OF_INTEREST if s in pe.data})
        print(f"    关注导入(子串搜): {ihits2 if ihits2 else '（无）'}")
        print(f"    导入 DLL: {sorted(x.decode('latin1') for x in pe.imports if x.lower().endswith(b'.dll'))}")

        print("    已知落点字节:")
        for k, va in KNOWN_VA.items():
            fo = pe.va2fo(va)
            if fo is None or fo + 16 > len(pe.data):
                print(f"      {k:24s} VA={va:#x}  <映射失败>")
                continue
            bs = pe.data[fo:fo + 16]
            print(f"      {k:24s} VA={va:#x} FO={fo:#x}  {bs.hex(' ')}")
        print()


if __name__ == "__main__":
    main()
