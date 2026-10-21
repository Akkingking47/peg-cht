import io, os, sys

IN  = r"D:\DSH\军事游戏汉化\work\gus\batch\batch-01.tsv"
DST = r"D:\DSH\军事游戏汉化\work\gus\tmp\batch-01.dst.txt"
OUT = r"D:\DSH\军事游戏汉化\work\gus\zh\xscn\batch-01.tsv"

def lines(p):
    raw = open(p, "rb").read().decode("utf-8-sig")
    ls = raw.split("\n")
    if ls and ls[-1] == "":
        ls.pop()
    return [l.rstrip("\r") for l in ls]

src = lines(IN)
dst = lines(DST)

header = src[0]
src_rows = src[1:]

print("input total lines :", len(src))
print("input data rows   :", len(src_rows))
print("dst lines         :", len(dst))

if len(dst) != len(src_rows):
    print("!! ROW COUNT MISMATCH")
    for i in range(min(len(dst), len(src_rows)), max(len(dst), len(src_rows))):
        print("  extra idx", i, repr(src_rows[i] if i < len(src_rows) else dst[i]))
    sys.exit(1)

out_lines = ["src\tfreq\tgroups\texample\tdst"]
bad = 0
for i, (s, d) in enumerate(zip(src_rows, dst)):
    parts = s.split("\t")
    if len(parts) != 6:
        print("!! col count", i, len(parts), repr(s))
        sys.exit(2)
    a, f, g, e, h, _ = parts
    if d == "":
        print("!! empty dst at row", i, repr(a))
        bad += 1
    out_lines.append("\t".join([a, f, g, e, d]))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
    fh.write("\n".join(out_lines) + "\n")

print("wrote:", OUT)
print("output lines      :", len(out_lines))
print("empty dst         :", bad)
print("non-ascii src rows:", sum(1 for s in src_rows if any(ord(c) > 127 for c in s.split('\t')[0])))
