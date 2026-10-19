import hint_pe as H
d=H.load(H.SRC)
pros=[0x401000]
fo=H.va_to_fo(0x401000)
i=0
n=H.TEXT_SIZE
while True:
    j=d.find(b"\x55\x8b\xec", H.TEXT_FO+i, H.TEXT_FO+n)
    if j<0: break
    pros.append(H.fo_to_va(j)); i=j-H.TEXT_FO+1
pros=sorted(set(pros))
def owner(va):
    p=0x401000
    for q in pros:
        if q<=va: p=q
        else: break
    return p
readers=[0x413AE1,0x4140EA,0x4309BB,0x44603C,0x446A0B,0x447AB6,0x451E06,0x452E2C,0x46D0C2,0x46D6C6,0x47053B,0x47076D,0x4709AC,0x470BFD,0x4712BF,0x4716F8,0x4716FE,0x45E4B1]
print("reader -> enclosing prologue (nearest 55 8B EC at or before)")
for r in sorted(readers):
    print(f"  ref@0x{r:06X}  in function 0x{owner(r):06X}")
print()
print("prologues in 0x470200..0x471800:")
print("  "+", ".join(f"0x{p:06X}" for p in pros if 0x470200<=p<0x471800))
print("prologues in 0x413000..0x415000:")
print("  "+", ".join(f"0x{p:06X}" for p in pros if 0x413000<=p<0x415000))
