# -*- coding: utf-8 -*-
"""反汇编：PeG030.exe 的文本绘制函数（0x4718A2 帮手）与所有 DrawTextExA 调用点
目的：判定 ① nCount 传的是字节数还是 -1；② 绘制标志（DT_*）；③ 是否有定长缓冲/截断
"""
import pefile, capstone, struct, re

PE = r"D:\Program Files\PeG\PeG030.exe"
pe = pefile.PE(PE)
text = [s for s in pe.sections if s.Name.startswith(b".text")][0]
code = text.get_data()
base = pe.OPTIONAL_HEADER.ImageBase + text.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

def rd(va, n=64):
    for s in pe.sections:
        sv = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        if sv <= va < sv + s.SizeOfRawData:
            return s.get_data()[va - sv: va - sv + n]
    return b""

def cstr(va, n=48):
    raw = rd(va, n).split(b"\x00")[0]
    try:
        return raw.decode("latin-1")
    except Exception:
        return ""

# ---- IAT 地址 ----
IAT = {}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for i in e.imports:
        if i.name:
            IAT[i.name.decode()] = i.address
for k in ("DrawTextExA", "CreateFontA", "GetTextExtentPoint32A", "SetTextColor", "SelectObject"):
    print(f"  IAT {k:22s} = {IAT.get(k) and hex(IAT[k])}")

# ---- 找 DrawTextExA 调用点 ----
pat = b"\xff\x15" + struct.pack("<I", IAT["DrawTextExA"])
sites = [m.start() for m in re.finditer(re.escape(pat), pe.__data__)]
print(f"\n=== DrawTextExA 调用点 {len(sites)} 处 (FO) ===")
def fo2va(fo):
    for s in pe.sections:
        if s.PointerToRawData <= fo < s.PointerToRawData + s.SizeOfRawData:
            return pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress + (fo - s.PointerToRawData)
    return None
vas = sorted(filter(None, (fo2va(f) for f in sites)))
print("  VA:", [hex(v) for v in vas])

# ---- 逐个调用点看前 60 条指令 ----
def dump(va, back=140, fwd=20, tag=""):
    off = va - base
    print(f"\n--- 上下文 {tag} @ {hex(va)} ---")
    for ins in md.disasm(code[max(0, off-back): off+fwd], base + max(0, off-back)):
        note = ""
        if ins.mnemonic == "push" and ins.op_str.startswith("0x"):
            try:
                v = int(ins.op_str, 16)
            except ValueError:
                v = None
            if v and 0x48c000 <= v < 0x6b0000:
                s = cstr(v, 40)
                if s and all(32 <= ord(c) < 127 for c in s):
                    note = f"   ; \"{s}\""
        print(f"  {ins.address:08x}  {ins.mnemonic:7s} {ins.op_str}{note}")

# 只看前 4 个调用点（通常就是通用 helper 的调用）
for v in vas[:4]:
    dump(v, tag="DrawTextExA")
