import io, collections, re, sys
WS = r"D:\DSH\军事游戏汉化"
def norm_en(s): return re.sub(r"\s+"," ",s.strip().strip('"“”「」')).strip(" .,-–—").lower()
cats = collections.defaultdict(set)
p = WS + r"\glossary\standard-glossary.tsv"
hdr=None
for ln in io.open(p, encoding="utf-8-sig"):
    if ln.startswith("#") or not ln.strip(): continue
    c = ln.rstrip("\r\n").split("\t")
    if hdr is None:
        hdr=c; ie,ic = (c.index("en"), c.index("cat")) if "en" in c and "cat" in c else (0,2); continue
    if len(c)>max(ie,ic): cats[norm_en(c[ie])].add(c[ic].strip().upper())
print("HEADER:", hdr)
for k in ("ss","pt","longest path:","number of scenarios:","message from:","son","june 15","rha/","/1/hg","lodz","tunis","leningrad","amur river","suchan","katowice","ternopil'"):
    print(f"  {k!r:26} -> {sorted(cats.get(k, set())) or '（未入库）'}")
