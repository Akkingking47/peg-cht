import hint_pe as H, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
d=H.load(H.SRC); P=H.load(H.PORT)
md=Cs(CS_ARCH_X86,CS_MODE_32)
def va2fo(v):
    try: return H.va_to_fo(v)
    except: return None
base=0x4A96E8
print("=== ALL refs to 0x4A96E8+0..0xE (whole table) ===")
for k in range(0,15):
    t=base+k
    pat=struct.pack('<I',t)
    f=d.find(pat)
    if f<0: continue
    while f>=0:
        va=H.fo_to_va(f) if f>=H.TEXT_FO and f<H.TEXT_FO+H.TEXT_SIZE else None
        if va is None:
            sec=H.sec_of(f)
            va=None
            for nm,sva,sraw,ssz in H.SECS:
                if sraw<=f<sraw+ssz: va=sva+(f-sraw); break
        # decode one insn at va
        s=''
        if va is not None:
            fo2=H.va_to_fo(va)
            for ins in md.disasm(d[fo2:fo2+15], va):
                s=f"{ins.mnemonic} {ins.op_str}"; break
        print(f"  +0x{k:<2} 0x{t:06X} ref@0x{va:06X}  {s}")
        f=d.find(pat, f+1)
print()
print("=== writes to [0x4AF320] and value ===")
pat=struct.pack('<I',0x4AF320)
f=d.find(pat)
tgt=[]
while f>=0:
    va=None
    for nm,sva,sraw,ssz in H.SECS:
        if sraw<=f<sraw+ssz: va=sva+(f-sraw); break
    mva = va-2 if va is not None else None
    if mva is not None:
        for ins in md.disasm(d[H.va_to_fo(mva):H.va_to_fo(mva)+8], mva):
            tgt.append((va,ins.mnemonic,ins.op_str)); break
    f=d.find(pat,f+1)
for va,m,o in tgt:
    print(f"  0x{va:06X}  {m} {o}")
