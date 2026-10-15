import hint_pe as H
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
d=H.load(H.SRC); md=Cs(CS_ARCH_X86,CS_MODE_32)
def dis(lo,hi):
    fo=H.va_to_fo(lo); out=[]
    for ins in md.disasm(d[fo:fo+(hi-lo)], lo):
        out.append((ins.address,f"{ins.mnemonic} {ins.op_str}"))
    return out
def encl(va):
    for start in range(va-0x400, va):
        try: fo=H.va_to_fo(start)
        except: continue
        # candidate prologue?
        if d[fo:fo+3] not in (b"\x55\x8b\xec",) : continue
        # decode from here, see if we pass va exactly
        for ins in md.disasm(d[fo:fo+0x400], start):
            if ins.address==va: return start
            if ins.address>va: break
    return None
for v in (0x470520,0x470980,0x47053F,0x4709E9,0x41407A,0x471294,0x470D48):
    e=encl(v)
    print(f"0x{v:06X} enclosed by prologue 0x{e:06X}" if e else f"0x{v:06X} -> prologue not found")
print()
for v in (0x4704D0,0x47096E,0x470D48,0x471294):
    print(f"--- around 0x{v:06X} ---")
    for a,t in dis(v, v+0x20): print(f"  0x{a:06X}  {t}")
