import pathlib, re

W = pathlib.Path(r"D:\DSH\军事游戏汉化\work")

rows = []
for ln in (W / "xscn" / "openpg-orig.tsv").read_text(encoding="utf-8").splitlines():
    c = ln.split("\t")
    if len(c) >= 5:
        rows.append(c)

uniq = {}
for r in rows:
    uniq[r[3]] = uniq.get(r[3], 0) + 1

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

miss = sorted(u for u in uniq if u not in m)

print("=== A. 全大写词（地形/类别，共 %d 条）===" % len([u for u in miss if re.fullmatch(r"[A-Z0-9 \-\./()\[\]]+", u)]))
for u in miss:
    if re.fullmatch(r"[A-Z0-9 \-\./()\[\]]+", u):
        print("   ", u)

rest = [u for u in miss if u not in pm]
print()
print("=== B. 两张表都未命中（需新译）：%d 条 ===" % len(rest))
for u in rest:
    print("   ", u)

print()
print("=== C. PGForever 表命中抽样（前 30 条，验证复用质量）===")
n = 0
for u in miss:
    if u in pm:
        print("    %-30s -> %s" % (u, pm[u]))
        n += 1
    if n >= 30:
        break

print()
print("=== D. OLGWW2 映射命中抽样（前 20 条）===")
n = 0
for u in sorted(uniq):
    if u in m:
        print("    %-30s -> %s" % (u, m[u]))
        n += 1
    if n >= 20:
        break

out = W / "xscn" / "openpg-todo.tsv"
with out.open("w", encoding="utf-8", newline="\n") as f:
    for u in miss:
        f.write("%s\t%s\n" % (u, pm.get(u, "")))
print()
print("待译清单已写出 ->", out)
