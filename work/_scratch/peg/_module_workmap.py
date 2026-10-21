# 只读：模块工作图（利用 MSVC 链接器把同一 .obj 的代码放成连续区间）
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
    nm = d[o:o + 8].rstrip(b"\0").decode("latin1")
    vs, va, rs, rp = struct.unpack_from("<IIII", d, o + 8)
    secs.append((nm, va, vs, rp, rs))
IB = struct.unpack_from("<I", d, coff + 20 + 28)[0]
_, tva, tvs, trp, trs = [s for s in secs if s[0] == ".text"][0]
t = d[trp:trp + trs]
text_end = tva + tvs

def off2va(off):
    for nm, va, vs, rp, rs in secs:
        if rp <= off < rp + rs:
            return IB + va + (off - rp)

mods = collections.defaultdict(list)
for m in re.finditer(rb"C:\\modgen\\[^\x00]{3,90}\.[ch]\b", d):
    b = struct.pack("<I", off2va(m.start()))
    s0 = 0
    while True:
        j = t.find(b, s0)
        if j < 0:
            break
        mods[m.group().decode("latin1")].append(tva + j)
        s0 = j + 1

starts = []
for i in range(len(t) - 3):
    if t[i] == 0x55 and t[i + 1] == 0x8B and t[i + 2] == 0xEC:
        if i == 0 or t[i - 1] in (0xC3, 0xCC, 0x90, 0xC2, 0x5D, 0xE9, 0xEB,
                                  0x5F, 0x5E, 0x5B, 0x5A, 0x59, 0x58, 0x66):
            starts.append(tva + i)

rng = {s: (min(v), max(v)) for s, v in mods.items()}
order = sorted(rng.items(), key=lambda kv: kv[1][0])
# 用相邻模块的 assert 区间中点做边界
bounds = []
for i in range(len(order) - 1):
    bounds.append(((order[i][1][1] + order[i + 1][1][0]) // 2))

def mod_of(rva):
    for i, b in enumerate(bounds):
        if rva <= b:
            return order[i][0]
    return order[-1][0]

count = collections.Counter()
for s in starts:
    count[mod_of(s)] += 1

print("函数序言数 = %d   游戏模块数 = %d" % (len(starts), len(order)))
print()
print("%-30s %8s %8s %8s %8s" % ("module", "lo(RVA)", "hi(RVA)", "funcs", "bytes~"))
tot_f = 0
for i, (s, (lo, hi)) in enumerate(order):
    nxt = order[i + 1][1][0] if i + 1 < len(order) else text_end
    hi2 = min(hi, nxt)
    span = hi2 - lo
    n = count.get(s, 0)
    tot_f += n
    print("%-30s %8X %8X %8d %8d" % (s.replace("C:\\modgen\\main\\", ""), lo, hi2, n, span))
print()
print("已归属函数 = %d / %d" % (tot_f, len(starts)))
print(".text RVA 范围 = %X .. %X" % (tva, tva + tvs))
