import pathlib, re

W = pathlib.Path(r"D:\DSH\军事游戏汉化\work")

rows = []
for ln in (W / "xscn" / "openpg-orig.tsv").read_text(encoding="utf-8").splitlines():
    c = ln.split("\t")
    if len(c) >= 5:
        rows.append(c)

m = {}
for ln in (W / "xscn-all-map.tsv").read_text(encoding="utf-8").splitlines():
    c = ln.split("\t")
    if len(c) >= 5 and c[3]:
        m.setdefault(c[3], c[4])

pm = {}
for ln in (W / "xscn" / "pgf-lookup.tsv").read_text(encoding="utf-8").splitlines():
    c = ln.split("\t")
    if len(c) >= 2 and c[0]:
        pm.setdefault(c[0], c[1])

print("=== 54 个战役标题（-1 组）及其复用状态 ===")
titles = [r for r in rows if r[1] == "-1"]
for r in titles:
    src = "OLGWW2" if r[3] in m else ("PGForever" if r[3] in pm else "**待译**")
    tgt = m.get(r[3]) or pm.get(r[3]) or ""
    print("  %-22s %-12s %s" % (r[0], tgt, src))

allcap = sorted(set(r[3] for r in rows if re.fullmatch(r"[A-Z0-9 \-\./()\[\]]+", r[3])))
print()
print("=== 场景中出现的全大写词（全部，共 %d 条）===" % len(allcap))
for u in allcap:
    tgt = m.get(u) or pm.get(u) or ""
    src = "OLGWW2" if u in m else ("PGForever" if u in pm else "**待译**")
    print("  %-20s %-10s %s" % (u, tgt, src))

print()
print("=== OLGWW2 映射里的同类地形词，供口径参考 ===")
for k, v in m.items():
    if re.fullmatch(r"[A-Z]{3,12}", k):
        print("  %-20s -> %s" % (k, v))
