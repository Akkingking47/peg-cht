# 只读：在整份 exe 里找"800,600"相邻对（word 与 dword 两种），找 800x600 的静态 RECT/尺寸
import struct, sys

p = r"D:\Program Files\PeG\PeG030.exe"
d = open(p, "rb").read()
e = struct.unpack_from("<I", d, 0x3C)[0]
coff = e + 4
nsec = struct.unpack_from("<H", d, coff + 2)[0]
szopt = struct.unpack_from("<H", d, coff + 16)[0]
soh = coff + 20 + szopt
secs = []
for i in range(nsec):
    o = soh + i * 40
    nm = d[o:o + 8].rstrip(b"\0").decode("latin1")
    vs, va, rs, rp = struct.unpack_from("<IIII", d, o + 8)
    secs.append((nm, va, vs, rp, rs))
IB = struct.unpack_from("<I", d, coff + 20 + 28)[0]

def sec_of(off):
    for nm, va, vs, rp, rs in secs:
        if rp <= off < rp + rs:
            return nm, IB + va + (off - rp)
    return None, None

hits_w, hits_d = [], []
for i in range(0, len(d) - 8):
    if d[i:i+2] == b"\x20\x03" and d[i+2:i+4] == b"\x58\x02":
        hits_w.append(i)
    if d[i:i+4] == b"\x20\x03\x00\x00" and d[i+4:i+8] == b"\x58\x02\x00\x00":
        hits_d.append(i)

def show(tag, hits):
    print("== %s : %d 处" % (tag, len(hits)))
    for h in hits[:40]:
        nm, va = sec_of(h)
        ctx = d[max(0, h - 8):h + 16].hex(" ")
        print("   %-8s VA=%08X  ctx[-8..+16]: %s" % (nm, va, ctx))
    if len(hits) > 40:
        print("   ... 其余 %d 处省略" % (len(hits) - 40))

show("word 0x0320,0x0258", hits_w)
show("dword 0x320,0x258", hits_d)
