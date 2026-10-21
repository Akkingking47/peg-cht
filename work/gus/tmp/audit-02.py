import io, re

OUT = r"D:\DSH\军事游戏汉化\work\gus\zh\xscn\batch-01.tsv"
rep = io.open(r"D:\DSH\军事游戏汉化\work\gus\tmp\audit-02.txt", "w", encoding="utf-8", newline="\n")

def lines(p):
    r = open(p, "rb").read().decode("utf-8-sig")
    ls = r.split("\n")
    if ls and ls[-1] == "":
        ls.pop()
    return [x.rstrip("\r") for x in ls]

o = lines(OUT)

WORDS = ["Line","Force","Brigade","Division","Army","Air","Naval","Guard","Regiment",
         "Battalion","Station","River","Island","Lake","Hill","Port","Fort","Bridge",
         "Forest","Village","Town","Airport","Airfield","Depot","Factory","Canal","Bay",
         "Sea","Regiment","Group","Korps","Division","Bde"]
rep.write("=== dst still contains an English common noun (src had it too) ===\n")
for k in range(1, len(o)):
    p = o[k].split("\t")
    hits = [w for w in WORDS if re.search(r"(?<![A-Za-z])" + w + r"(?![A-Za-z])", p[4])]
    if hits:
        rep.write("%4d  %-42s | %-34s | %s\n" % (k, p[0], p[4], hits))

rep.write("\n=== rows mentioning 莫托 / Motow / wodka / Wodka ===\n")
for k in range(1, len(o)):
    p = o[k].split("\t")
    if re.search(r"莫托|Motow|Motow|owódk|owodk", p[0] + p[4]):
        rep.write("%4d  %-42s | %s\n" % (k, p[0], p[4]))

rep.write("\n=== rows whose dst is shorter than half the src length ===\n")
for k in range(1, len(o)):
    p = o[k].split("\t")
    if len(p[4]) * 2 < len(p[0]):
        rep.write("%4d  %-42s | %s\n" % (k, p[0], p[4]))

rep.write("\n=== all rows (src | dst) : first 60 ===\n")
for k in range(1, 61):
    p = o[k].split("\t")
    rep.write("%4d  %-42s | %s\n" % (k, p[0], p[4]))

rep.close()
print("done")
