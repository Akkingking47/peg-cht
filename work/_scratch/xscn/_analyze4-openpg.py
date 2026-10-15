import pathlib, re
from collections import defaultdict

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

print("=== 54 个标题：原文 -> 译文 ===")
for r in rows:
    if r[1] == "-1":
        tgt = m.get(r[3]) or pm.get(r[3]) or "**待译**"
        print("  %-22s |%-26s| %s" % (r[0], r[3], tgt))

print()
print("=== 全大写地形词各自出现在哪些场景 ===")
for w in ["BOCAGE", "FOREST", "FORTIFICATION", "MOUNTAIN", "RIVER", "ROUGH", "SAND", "SWAMP"]:
    files = sorted(set(r[0] for r in rows if r[3] == w))
    print("  %-14s %d 个场景: %s" % (w, len(files), ", ".join(files[:8]) + (" ..." if len(files) > 8 else "")))

print()
print("=== SAND 附近的同场景条目（判断语境）===")
sandfiles = sorted(set(r[0] for r in rows if r[3] == "SAND"))
for f in sandfiles[:3]:
    print("  --", f)
    for r in rows:
        if r[0] == f and r[1] == "0":
            print("       %-28s -> %s" % (r[3], m.get(r[3]) or pm.get(r[3]) or "**待译**"))

print()
print("=== 非标题、非地形的说明性条目（含空格且两表未命中）===")
for u in sorted(set(r[3] for r in rows)):
    if u not in m and u not in pm and " " in u:
        files = sorted(set(r[0] for r in rows if r[3] == u))
        print("  %-24s %s" % (u, ", ".join(files[:5])))
