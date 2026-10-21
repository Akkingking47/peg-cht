import io, re, random, sys

class Tee:
    def __init__(self, path):
        self.f = io.open(path, "w", encoding="utf-8", newline="\n")
    def write(self, s):
        self.f.write(s)
    def flush(self):
        self.f.flush()

sys.stdout = Tee(r"D:\DSH\军事游戏汉化\work\gus\tmp\check-01.report.txt")

IN  = r"D:\DSH\军事游戏汉化\work\gus\batch\batch-01.tsv"
OUT = r"D:\DSH\军事游戏汉化\work\gus\zh\xscn\batch-01.tsv"

def lines(p):
    r = open(p, "rb").read().decode("utf-8-sig")
    ls = r.split("\n")
    if ls and ls[-1] == "":
        ls.pop()
    return [x.rstrip("\r") for x in ls]

raw = open(OUT, "rb").read()
i, o = lines(IN), lines(OUT)
print("BOM:", raw.startswith(b"\xef\xbb\xbf"), "| CR:", b"\r" in raw)
print("in lines:", len(i), "out lines:", len(o))
mm = sum(1 for k in range(1, min(len(i), len(o))) if i[k].split("\t")[0] != o[k].split("\t")[0])
cols = sum(1 for k in range(1, len(o)) if len(o[k].split("\t")) != 5)
print("src mismatch:", mm, "| bad cols:", cols)
noCJK = [o[k].split("\t")[0] for k in range(1, len(o)) if not re.search(r"[\u4e00-\u9fff]", o[k].split("\t")[4])]
print("rows without any CJK (dst):", len(noCJK))

GLOSS = ["InfDiv","PzDiv","PanzDiv","PzGrenDiv","VolksGrenDiv","FJDiv","ArtReg","ArtRgt",
         "PionAbt","AufklAbt","Recb","PzJagAbt","PzJgAbt","GrenReg","StuGAbt","FlakAbt",
         "Hauptquartier","LSSAH","LAH","Totenkopf","Wiking","NKWD","Gvd","Gwd","Guards",
         "DStrz","DywStrz","BPanc","DywPanc","PAL","ArmDiv","AirDiv","InfReg","Rifle",
         "Rifles","HMS","USS","Corps","Brig","Bde","Brygada","Div","Rgt","Reg","Bn"]
flag = []
for k in range(1, len(o)):
    s = o[k].split("\t")[0]
    d = o[k].split("\t")[4]
    hits = [g for g in GLOSS if re.search(r"(?<![A-Za-z])" + re.escape(g) + r"(?![A-Za-z])", s) and re.search(re.escape(g), d)]
    if hits:
        flag.append((s, d, hits))
print("rows still carrying glossary abbrev in dst:", len(flag))
for s, d, h in flag[:40]:
    print("   ", s, "=>", d, h)

random.seed(7)
idx = sorted(random.sample(range(1, len(o)), 45))
print("\n--- random sample ---")
for k in idx:
    print(o[k])
