import hint_pe as H, struct
d=H.load(H.SRC)
def cstr(va, n=64):
    try: fo=H.va_to_fo(va)
    except: return None
    out=b''
    for i in range(n):
        c=d[fo+i]
        if c==0: break
        out+=bytes([c])
    if len(out)<3: return None
    try: return out.decode('ascii')
    except: return None
print("=== strings 0x4AB800..0x4ABC00 ===")
va=0x4AB800
while va<0x4ABC00:
    s=cstr(va)
    if s and all(32<=ord(c)<127 for c in s):
        print(f"  0x{va:06X}  {s!r}"); va+=len(s)+1
    else: va+=1
print()
print("=== call sites of 0x4704D2 with preceding push imm32 (idx) ===")
pat=struct.pack('<I',0x4704D2)
i=H.TEXT_FO
res=[]
while True:
    j=d.find(pat, i, H.TEXT_FO+H.TEXT_SIZE)
    if j<0: break
    ins_va=H.fo_to_va(j-1)
    if d[j-1]!=0xE8:
        i=j+1; continue
    # look back for pushes in the 40 bytes before
    pushes=[]
    for k in range(j-1-40, j-1):
        off=j-1-k
        try: kva=H.fo_to_va(k)
        except: continue
        if d[k]==0x68:
            pushes.append((off,H.u32(d,k+1) if hasattr(H,'u32') else struct.unpack('<I',d[k+1:k+5])[0]))
    res.append((ins_va,pushes))
    i=j+1
for va,ps in res:
    ps=[(o,v) for o,v in ps if 0<v<0x120]
    print(f"  call@0x{va:06X}  pushes(idx): {', '.join(f'-{o}:0x{v:X}({v})' for o,v in ps) if ps else '(indirect)'}")
