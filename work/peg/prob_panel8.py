import hint_pe as H, struct
d=H.load(H.SRC)
base=0x4A96E8
rows=[]
W,Hh=800,600
for idx in range(0x110):
    va=base+idx*0xF
    try: fo=H.va_to_fo(va)
    except: continue
    b=d[fo:fo+15]
    x1,y1,x2,y2,f8,f10,f12=struct.unpack('<7h',b[:14])
    w=x2-x1; h=y2-y1
    # role by geometry
    if x1<0 or y1<0 or x2>x1+2000: role='?'
    elif x2>=700: role='RIGHT(+1120)'
    elif w>=150 and h>=120: role='PANEL(+560)'
    elif x2<=500 and x1>=100 and (x1<=640): role='MID(+560)'
    else: role='KEEP'
    dx=1120 if role.startswith('RIGHT') else (560 if role.startswith(('PANEL','MID')) else 0)
    rows.append((idx,va,x1,y1,x2,y2,w,h,f8,f10,f12,role,dx))
with open('out/panel_table_manifest.tsv','w',encoding='utf-8') as f:
    f.write("idx\tVA\tx1\ty1\tx2\ty2\tw\th\t+8\t+a\t+c\trole\tdx\n")
    for r in rows:
        f.write("\t".join(str(x) for x in r)+"\n")
print("records:",len(rows),"-> out/panel_table_manifest.tsv")
from collections import Counter
print(Counter(r[11] for r in rows))
print()
print("=== 非 KEEP 记录（可打候选）===")
for r in rows:
    if r[11]!='KEEP' and 0<=r[2] and 0<=r[3]:
        idx,va,x1,y1,x2,y2,w,h,f8,f10,f12,role,dx=r
        print(f"  idx {idx:3d}(0x{idx:02X}) @0x{va:06X} ({x1:4d},{y1:4d})-({x2:4d},{y2:4d}) {w:4d}x{h:<4d} +8={f8:5d} {role} -> ({x1+dx},{y1})-({x2+dx},{y2})")
