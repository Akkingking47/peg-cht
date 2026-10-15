# -*- coding: utf-8 -*-
"""定位 PeG030.exe 的 GUI 文本加载器 与 标签绘制/滚动逻辑"""
import pefile, capstone, re, struct

PE = r"D:\Program Files\PeG\PeG030.exe"
pe = pefile.PE(PE)
text = [s for s in pe.sections if s.Name.startswith(b".text")][0]
code = text.get_data()
base = pe.OPTIONAL_HEADER.ImageBase + text.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True

def sec_of_va(va):
    for s in pe.sections:
        sv = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        if sv <= va < sv + s.SizeOfRawData:
            return s
    return None

def cstr(va, n=40):
    s = sec_of_va(va)
    if not s: return ""
    off = va - (pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress)
    raw = s.get_data()[off:off+n].split(b"\x00")[0]
    return raw.decode("latin-1", "replace")

# 1) 找 "gui030" 字符串的 VA
hit_va = None
for s in pe.sections:
    sv = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
    d = s.get_data()
    i = d.find(b"gui030\x00")
    if i >= 0:
        hit_va = sv + i
        break
print("'gui030' string VA =", hex(hit_va) if hit_va else None, repr(cstr(hit_va,20)))

# 2) 全 .text 找 push imm == 该 VA
pushes = []
for ins in md.disasm(code, base):
    if ins.mnemonic == "push" and ins.op_str.startswith("0x"):
        try: v = int(ins.op_str, 16)
        except ValueError: continue
        if v == hit_va:
            pushes.append(ins.address)
print("push 'gui030' 处:", [hex(a) for a in pushes])

# 3) 也找 mov imm (有些编译器用 mov)
movs = []
for ins in md.disasm(code, base):
    if ins.mnemonic == "mov" and hex(hit_va) in ins.op_str:
        movs.append((ins.address, ins.op_str))
print("mov 引用:", [(hex(a), o) for a, o in movs][:10])

# 4) 打印引用点上下文
def dump(va, back=120, fwd=60, tag=""):
    print(f"\n--- {tag} @ {hex(va)} ---")
    off = va - base
    for ins in md.disasm(code[max(0, off-back): off+fwd], base + max(0, off-back)):
        note = ""
        if ins.mnemonic in ("push", "mov", "cmp") :
            for t in re.findall(r"0x[0-9a-f]+", ins.op_str):
                v = int(t, 16)
                if 0x48c000 <= v < 0x6b0000:
                    s = cstr(v, 32)
                    if s and all(32 <= ord(c) < 127 for c in s):
                        note = f"   ; \"{s}\""
        print(f"  {ins.address:08x}  {ins.mnemonic:7s} {ins.op_str}{note}")

for a in pushes[:2]:
    dump(a, tag="GUI loader ref")
