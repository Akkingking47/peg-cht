# 只读：从 assert 的 __FILE__ 字符串反推模块划分与函数归属
import struct, re, collections

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
    name = d[o:o + 8].rstrip(b"\0").decode("latin1")
    vs, va, rs, rp = struct.unpack_from("<IIII", d, o + 8)
    secs.append((name, va, vs, rp, rs))
imagebase = struct.unpack_from("<I", d, coff + 20 + 28)[0]

def off2va(off):
    for name, va, vs, rp, rs in secs:
        if rp <= off < rp + rs:
            return imagebase + va + (off - rp)

tname, tva, tvs, trp, trs = [s for s in secs if s[0] == ".text"][0]
t = d[trp:trp + trs]

mods = collections.defaultdict(list)
for m in re.finditer(rb"C:\\modgen\\[^\x00]{3,90}\.[ch]\b", d):
    mods[m.group().decode("latin1")].append(off2va(m.start()))

def func_start(x):
    o = x - tva - 0x400000
    o = x - 0x400000 - tva
    if o < 0 or o >= len(t):
        return None
    for k in range(o, max(0, o - 4000), -1):
        if t[k] == 0x55 and t[k + 1] == 0x8B and t[k + 2] == 0xEC:
            return 0x400000 + tva + k
    return None

print("模块数 =", len(mods))
print()
print("%-42s %6s %6s  %s" % ("source file", "strs", "xrefs", "functions (部分)"))
tot_x = 0
allfuncs = set()
for s in sorted(mods):
    refs = []
    for v in mods[s]:
        b = struct.pack("<I", v)
        start = 0
        while True:
            j = t.find(b, start)
            if j < 0:
                break
            refs.append(0x400000 + tva + j)
            start = j + 1
    fns = []
    for r in refs:
        f = func_start(r)
        if f and f not in fns:
            fns.append(f)
    allfuncs.update(fns)
    tot_x += len(refs)
    short = s.replace("C:\\modgen\\main\\", "")
    print("%-42s %6d %6d  %s%s" % (short, len(mods[s]), len(refs),
                                   " ".join("%X" % f for f in fns[:8]),
                                   " …" if len(fns) > 8 else ""))
print()
print("xref 总数 =", tot_x, " 涉及函数数 =", len(allfuncs))
lo = min(allfuncs) if allfuncs else 0
hi = max(allfuncs) if allfuncs else 0
print("函数地址跨度 = 0x%X .. 0x%X" % (lo, hi))
