import hint_pe as H, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
d=H.load(H.SRC); md=Cs(CS_ARCH_X86,CS_MODE_32)
def decode_containing(refva, T):
    """find an instruction start in [refva-8, refva+1] whose text mentions T"""
    for off in range(-8,2):
        va=refva+off
        if va<0x401000: continue
        try: fo=H.va_to_fo(va)
        except: continue
        for ins in md.disasm(d[fo:fo+15], va):
            if len(ins.bytes)==0: break
            if va+len(ins.bytes)<=refva: break
            txt=f"{ins.mnemonic} {ins.op_str}"
            if hex(T) in txt or f"{T:06x}" in txt:
                return va,txt
            break
    return None,None
def refs(T):
    out=[];pat=struct.pack('<I',T);f=d.find(pat)
    while f>=0:
        va=H.fo_to_va(f)
        out.append(va); f=d.find(pat,f+1)
    return out
for T in [0x4AF320]:
    print(f"=== refs to 0x{T:06X} ===")
    for va in refs(T):
        iv,txt=decode_containing(va,T)
        print(f"  0x{va:06X} -> insn@0x{iv:06X}  {txt}" if iv else f"  0x{va:06X} -> ???")
print()
print("=== table 0x4A96E8 field refs (proper decode) ===")
for k in range(0,15):
    T=0x4A96E8+k
    r=refs(T)
    if not r: continue
    print(f"-- +0x{k:X} (0x{T:06X}) : {len(r)} refs")
    for va in r:
        iv,txt=decode_containing(va,T)
        print(f"     ref@0x{va:06X}  insn@0x{iv:06X}  {txt}" if iv else f"     ref@0x{va:06X}  ???")
