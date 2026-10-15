import hint_pe as H, struct, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
d=H.load(H.SRC); md=Cs(CS_ARCH_X86,CS_MODE_32)
def refs_all(T):
    out=[];pat=struct.pack('<I',T);f=d.find(pat)
    while f>=0:
        try: va=H.fo_to_va(f)
        except: va=None
        out.append((f,va)); f=d.find(pat,f+1)
    return out
def decode_at(refva,T):
    for off in range(-8,2):
        va=refva+off
        try: fo=H.va_to_fo(va)
        except: continue
        for ins in md.disasm(d[fo:fo+15], va):
            if len(ins.bytes)==0: break
            txt=f"{ins.mnemonic} {ins.op_str}"
            if f"{T:x}" in txt.replace(" ","") and va<=refva<va+len(ins.bytes):
                return va,txt
            break
    return None,None
TARGETS=[0x4AF2E8,0x4AF2EC,0x4AF2F8,0x4AF2FC,0x4AF300,0x498D3C,0x498D40,0x498D44,0x498D64]
log=open('out/mouse_refs.txt','w',encoding='utf-8')
for T in TARGETS:
    r=refs_all(T); W=[]; R=[]
    for f,va in r:
        if va is None:
            continue
        iv,txt=decode_at(va,T)
        if iv is None: continue
        entry=(iv,txt)
        # write if the memory operand is the destination (appears before comma)
        mem=f"0x{T:x}"
        pos=txt.find(mem)
        comma=txt.find(",")
        if pos>=0 and pos<comma: W.append(entry)
        else: R.append(entry)
    log.write(f"### 0x{T:06X}  total={len(r)} writes={len(W)} reads={len(R)}\n")
    log.write("  -- WRITES --\n")
    for iv,txt in sorted(set(W)): log.write(f"    0x{iv:06X}  {txt}\n")
    log.write("  -- READS --\n")
    for iv,txt in sorted(set(R)): log.write(f"    0x{iv:06X}  {txt}\n")
    log.write("\n")
log.close()
print("written out/mouse_refs.txt")
for T in TARGETS[:4]:
    r=refs_all(T); print(f"0x{T:06X}: {len(r)} refs")
