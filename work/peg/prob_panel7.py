import hint_pe as H, struct
d=H.load(H.SRC)
TEXT=H.TEXT_FO; N=H.TEXT_SIZE; BASE=H.TEXT_VA
def scans(targets):
    out={t:[] for t in targets}
    for k in range(TEXT, TEXT+N-5):
        if d[k]!=0xE8: continue
        rel=struct.unpack('<i', d[k+1:k+5])[0]
        va=H.fo_to_va(k); tgt=(va+5+rel)&0xffffffff
        if tgt not in targets: continue
        pushes=[]
        for m in range(k-40,k):
            if d[m]==0x68:
                pushes.append((k-m, struct.unpack('<I',d[m+1:m+5])[0]))
        out[tgt].append((va, pushes))
    return out
r=scans({0x4704D2,0x47097A})
for t,items in r.items():
    print(f"=== call sites of 0x{t:X} : {len(items)} ===")
    for va,ps in items:
        idx=[f"0x{v:X}({v})" for o,v in ps if 0<v<0x120]
        print(f"  call@0x{va:06X}  push-imm idx: {', '.join(idx) if idx else '(computed)'}")
