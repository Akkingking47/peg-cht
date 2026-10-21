import io

OUT = r"D:\DSH\军事游戏汉化\work\gus\zh\xscn\batch-01.tsv"
fix = {
    "EAM Forces": "EAM部队",
    'Div "Ciociosan"': '"Ciociosan"师',
}

raw = open(OUT, "rb").read().decode("utf-8")
ls = raw.split("\n")
if ls and ls[-1] == "":
    ls.pop()

n = 0
for k in range(1, len(ls)):
    p = ls[k].split("\t")
    if p[0] in fix:
        print("patched row", k, repr(p[0]), "->", repr(fix[p[0]]))
        p[4] = fix[p[0]]
        ls[k] = "\t".join(p)
        n += 1
print("patched:", n)
open(OUT, "wb").write(("\n".join(ls) + "\n").encode("utf-8"))
