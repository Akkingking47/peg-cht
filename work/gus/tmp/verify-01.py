import io, os

IN  = r"D:\DSH\军事游戏汉化\work\gus\batch\batch-01.tsv"
OUT = r"D:\DSH\军事游戏汉化\work\gus\zh\xscn\batch-01.tsv"

raw = open(OUT, "rb").read()
print("BOM present        :", raw.startswith(b"\xef\xbb\xbf"))
print("CR present         :", b"\r" in raw)

def lines(p):
    r = open(p, "rb").read().decode("utf-8-sig")
    ls = r.split("\n")
    if ls and ls[-1] == "":
        ls.pop()
    return [x.rstrip("\r") for x in ls]

i = lines(IN)
o = lines(OUT)
print("input lines        :", len(i))
print("output lines       :", len(o))
print("header in          :", repr(i[0]))
print("header out         :", repr(o[0]))

mismatch = 0
colbad = 0
for n in range(1, min(len(i), len(o))):
    a = i[n].split("\t")[0]
    p = o[n].split("\t")
    if len(p) != 5:
        colbad += 1
        print("col count", n, len(p), repr(o[n]))
        continue
    if p[0] != a:
        mismatch += 1
        if mismatch <= 10:
            print("MISMATCH row", n)
            print("  in :", repr(a))
            print("  out:", repr(p[0]))
print("src mismatch rows  :", mismatch)
print("bad column rows    :", colbad)

# freq/groups/example fidelity
fge = 0
for n in range(1, min(len(i), len(o))):
    pin = i[n].split("\t")[:4]
    pout = o[n].split("\t")[:4]
    if pin != pout:
        fge += 1
        if fge <= 5:
            print("FGE diff row", n, pin, pout)
print("freq/group/example diff rows:", fge)

# identity-preserved count (dst equals src)
same = sum(1 for n in range(1, min(len(i), len(o))) if o[n].split("\t")[4] == i[n].split("\t")[0])
print("dst == src rows    :", same)

# duplicate src check
from collections import Counter
c = Counter(x.split("\t")[0] for x in o[1:])
print("unique src values  :", len(c))
print("dup src groups     :", sum(1 for k, v in c.items() if v > 1))
print("sample out rows    :")
for n in (1, 2, 43, 500, 999, 1000):
    print("  ", o[n])
