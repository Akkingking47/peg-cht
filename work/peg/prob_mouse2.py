import hint_pe as H, struct
d=H.load(H.SRC)
def allrefs(T):
    out=[];pat=struct.pack('<I',T);f=d.find(pat)
    while f>=0:
        try: out.append(H.fo_to_va(f))
        except: pass
        f=d.find(pat,f+1)
    return out
def funcstart(va):
    fo=H.va_to_fo(va)
    for i in range(fo, max(0x400,fo-0x2000), -1):
        if d[i]==0x55 and d[i+1]==0x8b and d[i+2]==0xec:
            return H.fo_to_va(i)
    return None
G={n:allrefs(a) for n,a in [('mX',0x4AF2E8),('mY',0x4AF2EC),('scX',0x4AF2F8),('scY',0x4AF2FC),
                            ('vpL',0x4AF300),('vpT',0x498D3C),('vpR',0x498D40),('vpB',0x498D44)]}
funcs={}
for n,rs in G.items():
    for va in rs:
        fs=funcstart(va)
        funcs.setdefault(fs,{}).setdefault(n,[]).append(va)
print("func     hits(which globals)   mX/mY reader VAs")
for fs in sorted(funcs, key=lambda x:(x is None, x or 0)):
    g=funcs[fs]
    tag=",".join(sorted(g))
    if 'mX' in g or 'mY' in g:
        s=f"0x{fs:06X}" if fs else "  ???  "
        print(f"{s}  [{tag}]")
        for n in ('mX','mY'):
            if n in g: print(f"      {n}: "+", ".join(f"0x{v:06X}" for v in sorted(g[n])))
