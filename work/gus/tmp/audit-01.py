import io, re

OUT = r"D:\DSH\军事游戏汉化\work\gus\zh\xscn\batch-01.tsv"
rep = io.open(r"D:\DSH\军事游戏汉化\work\gus\tmp\audit-01.txt", "w", encoding="utf-8", newline="\n")

def lines(p):
    r = open(p, "rb").read().decode("utf-8-sig")
    ls = r.split("\n")
    if ls and ls[-1] == "":
        ls.pop()
    return [x.rstrip("\r") for x in ls]

o = lines(OUT)

rep.write("=== rows whose src contains a double quote ===\n")
for k in range(1, len(o)):
    p = o[k].split("\t")
    if '"' in p[0]:
        rep.write("%-46s | %s\n" % (p[0], p[4]))

rep.write("\n=== rows containing Bullingen/Bull/Bul/ligen ===\n")
for k in range(1, len(o)):
    p = o[k].split("\t")
    if re.search(r"B[uü]l|Bull|Ullingen|Uelingen", p[0]):
        rep.write("%-46s | %s\n" % (p[0], p[4]))

rep.write("\n=== rows whose src contains a slash ===\n")
for k in range(1, len(o)):
    p = o[k].split("\t")
    if "/" in p[0]:
        rep.write("%-46s | %s\n" % (p[0], p[4]))

rep.write("\n=== rows whose src contains a bracket or paren ===\n")
for k in range(1, len(o)):
    p = o[k].split("\t")
    if re.search(r"[\[\]()]", p[0]):
        rep.write("%-46s | %s\n" % (p[0], p[4]))

rep.write("\n=== all 31 rows with no CJK in dst ===\n")
for k in range(1, len(o)):
    p = o[k].split("\t")
    if not re.search(r"[\u4e00-\u9fff]", p[4]):
        rep.write("row %4d  %-34s | %s\n" % (k, p[0], p[4]))

rep.close()
print("done")
