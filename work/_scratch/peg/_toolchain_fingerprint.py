# 只读：PE 指纹（编译器/链接器/富头/导入表/路径字符串），不改任何文件
import struct, sys, re, datetime

p = sys.argv[1] if len(sys.argv) > 1 else r"D:\Program Files\PeG\PeG030.exe"
d = open(p, "rb").read()
print("file      :", p)
print("size      :", len(d), "bytes")
if d[:2] != b"MZ":
    sys.exit("not MZ")
e = struct.unpack_from("<I", d, 0x3C)[0]
print("e_lfanew  : 0x%X  sig=%r" % (e, d[e:e + 4]))
coff = e + 4
machine, nsec, tds, psym, nsym, osz, chars = struct.unpack_from("<HHIIIHH", d, coff)
try:
    stamp = datetime.datetime.utcfromtimestamp(tds).strftime("%Y-%m-%d %H:%M:%S")
except Exception:
    stamp = "?"
print("machine   : 0x%04X   sections=%d" % (machine, nsec))
print("timestamp : 0x%08X  (%s UTC)" % (tds, stamp))
print("character : 0x%04X  (bit1 EXECUTABLE=%d bit8 32BIT=%d bit9 DEBUG_STRIPPED=%d bit10 DEBUG_STRIPPED2=%d)" % (
    chars, chars & 2, (chars >> 8) & 1, (chars >> 9) & 1, (chars >> 10) & 1))
opt = coff + 20
magic = struct.unpack_from("<H", d, opt)[0]
szopt = struct.unpack_from("<H", d, coff + 16)[0]
lmaj, lmin = d[opt + 2], d[opt + 3]
szcode, szinit, szuninit = struct.unpack_from("<III", d, opt + 4)
entry, basecode, basedata = struct.unpack_from("<III", d, opt + 16)
imagebase = struct.unpack_from("<I", d, opt + 28)[0]
print("optional  : magic=0x%04X size=0x%X  linker=%d.%d" % (magic, szopt, lmaj, lmin))
print("sizes     : code=0x%X initdata=0x%X uninit=0x%X" % (szcode, szinit, szuninit))
print("entry     : 0x%08X   imagebase=0x%08X   basecode=0x%X basedata=0x%X" % (entry, imagebase, basecode, basedata))
soh = opt + szopt
secs = []
for i in range(nsec):
    o = soh + i * 40
    name = d[o:o + 8].rstrip(b"\0").decode("latin1")
    vs, va, rs, rp = struct.unpack_from("<IIII", d, o + 8)
    sc = struct.unpack_from("<I", d, o + 36)[0]
    secs.append((name, va, vs, rp, rs))
    print("  sec %-8s VA=0x%08X vsize=0x%08X raw=0x%08X rawsize=0x%08X flags=0x%08X" % (name, va, vs, rp, rs, sc))

def rva2off(rva):
    for name, va, vs, rp, rs in secs:
        if va <= rva < va + max(vs, rs):
            return rp + (rva - va)
    return None

# ---- Rich header ----
ridx = d.find(b"Rich")
print()
print("rich      :", "found at 0x%X" % ridx if ridx >= 0 else "NOT FOUND (non-MSVC or stripped)")
if ridx > 0 and ridx < e:
    key = struct.unpack_from("<I", d, ridx + 4)[0]
    print("rich key  : 0x%08X" % key)
    vals = []
    off = ridx - 4
    while off >= 0x40:
        v = struct.unpack_from("<I", d, off)[0] ^ key
        if v == 0x536E6144:  # DanS
            print("rich DanS : marker at 0x%X (%d entries decode ok)" % (off, len(vals)))
            break
        vals.append(v)
        off -= 4
    vals.reverse()
    prods = {}
    for i in range(0, len(vals) - 1, 2):
        comp, cnt = vals[i], vals[i + 1]
        prods[comp] = prods.get(comp, 0) + cnt
    for comp, cnt in sorted(prods.items()):
        print("  product 0x%08X  build=%d  count=%d" % (comp, comp >> 16, cnt))

# ---- imports ----
dd = opt + 96
irva, isz = struct.unpack_from("<II", d, dd + 8)
print()
print("imports   : dir RVA=0x%X size=%d" % (irva, isz))
io = rva2off(irva)
total = 0
if io:
    k = 0
    while True:
        oft, ts, fc, name_rva, first = struct.unpack_from("<IIIII", d, io + k * 20)
        if not any((oft, ts, fc, name_rva, first)):
            break
        no = rva2off(name_rva)
        dll = d[no:d.find(b"\0", no)].decode("latin1") if no else "?"
        thunk = oft or first
        to = rva2off(thunk)
        n = 0
        if to:
            while True:
                t = struct.unpack_from("<I", d, to + n * 4)[0]
                if t == 0:
                    break
                n += 1
        total += n
        print("  %-18s symbols=%d" % (dll, n))
        k += 1
        if k > 40:
            break
print("imports   : total symbols =", total)

# ---- path / toolchain strings ----
pats = [rb"(?i)VC98", rb"(?i)visual studio", rb"(?i)Microsoft Visual C\+\+", rb"(?i)MSVC",
        rb"(?i)\.pdb", rb"(?i)\.obj\b", rb"(?i)vctools", rb"(?i)libcmt", rb"(?i)msvcrt",
        rb"(?i)mspdb", rb"(?i)link\.exe", rb"(?i)[A-Za-z]:\\\\?[^\x00]{0,60}\.c\b"]
print()
print("strings   :")
seen = set()
for pat in pats:
    for m in re.finditer(pat, d):
        s = d[m.start():m.start() + 90].split(b"\0")[0]
        try:
            s = s.decode("latin1")
        except Exception:
            continue
        key = s[:60]
        if key in seen:
            continue
        seen.add(key)
        if len(seen) <= 25:
            print("  0x%06X  %s" % (m.start(), s))
print("strings   : matched unique =", len(seen))
