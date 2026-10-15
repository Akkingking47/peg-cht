import hint_pe as H, struct
d=H.load(H.SRC)
base=0x4A96E8
print("=== records idx 160..190 (x1,y1,x2,y2, f+8, w+0xa, w+0xc, byte+0xe) ===")
for idx in range(160,191):
    va=base+idx*0xF
    try: fo=H.va_to_fo(va)
    except: continue
    b=d[fo:fo+15]
    x1,y1,x2,y2,f8,f10,f12=struct.unpack('<7h',b[:14])
    print(f"  idx {idx:3d}(0x{idx:02X}) @0x{va:06X}  ({x1:5d},{y1:4d})-({x2:5d},{y2:4d}) sz=({x2-x1:4d}x{y2-y1:4d})  +8={f8:6d} +a={f10:6d} +c={f12:6d} +e={b[14]:3d}")
print()
print("=== strings around 0x4AB860..0x4ABB40 ===")
for va in range(0x4AB860,0x4ABB40,4):
    try: fo=H.va_to_fo(va)
    except: continue
    s=H.cstr(d,fo,48) if hasattr(H,'cstr') else None
    if s and len(s)>=3 and all(32<=ord(c)<127 for c in s):
        print(f"  0x{va:06X}  {s!r}")
