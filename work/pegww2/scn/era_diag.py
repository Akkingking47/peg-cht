# -*- coding: utf-8 -*-
"""年代维度可行性诊断：
 ① .SCN 头部是否含年份字段（1939~1947）
 ② 能否为每个场景定出年代（.SCN 字段 优先，_i/.TXT 日期 兜底）
 ③ 同一后缀 token 在不同年代的实测译法差异（差异大⇒必须分年代）
"""
import os, sys, io, re
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
DEP = r"D:\Program Files\PeG-WW2\SCENARIO"
BK = r"d:\DSH\军事游戏汉化\pegww2\testbed\backup\SCENARIO"
S0, P = 11350, 65
CJK = re.compile(r"[\u4e00-\u9fff]")
idx = {f.lower(): f for f in os.listdir(DEP)}

def rd(p): return open(p, "rb").read().decode("gbk", errors="replace").split("\r\n")
def rdb(p): return open(p, "rb").read()

# ① SCN 头部扫年份 u16
pos_hit = Counter(); scn_year = {}
for f in sorted(os.listdir(DEP)):
    if not f.lower().endswith(".scn"): continue
    d = rdb(os.path.join(DEP, f)); stem = f[:-4].lower()
    yrs = sorted({d[i] | (d[i+1] << 8) for i in range(0, min(S0, len(d)-1)) if 1939 <= (d[i] | (d[i+1] << 8)) <= 1947})
    if yrs: scn_year[stem] = yrs
print("① .SCN 头部含 1939~1947 字段的场景：%d / 648" % len(scn_year))
print("   年份分布：", dict(Counter(y for v in scn_year.values() for y in v).most_common(12)))

# ② 文本日期兜底
def txt_year(stem):
    for suf in ("_i.txt", ".TXT", "_i.TXT", "_m.txt"):
        k = idx.get((stem + suf).lower())
        if not k: continue
        head = "\n".join(rd(os.path.join(DEP, k))[:6])
        m = re.search(r"(19[34]\d)(?:\s*年|[/\-])", head) or re.search(r"19[34]\d", head)
        if m: return int(m.group(1) if m.lastindex else m.group(0))
    return 0
Y = {}
for stem in [f[:-6].lower() for f in os.listdir(DEP) if f.lower().endswith("_u.txt")]:
    y = 0
    if stem in scn_year: y = min(scn_year[stem])
    if not y: y = txt_year(stem)
    Y[stem] = y
cov = sum(1 for v in Y.values() if v)
print("\n② 可定年代的场景：%d / %d（SCN字段+文本日期）" % (cov, len(Y)))
print("   年代分布：", dict(Counter((v // 2 * 2) for v in Y.values() if v).most_common(12)))

# ③ 同后缀跨年代译法差异
def era(y):
    if not y: return "?"
    if y <= 1941: return "1939-41"
    if y <= 1943: return "1942-43"
    return "1944-46"
sfx = defaultdict(lambda: defaultdict(Counter))
for f in sorted(os.listdir(DEP)):
    if not f.lower().endswith("_u.txt"): continue
    stem = f[:-6].lower(); E = era(Y.get(stem, 0))
    bk = os.path.join(BK, idx.get(f.lower(), f))
    if not os.path.isfile(bk): continue
    d = rd(os.path.join(DEP, f)); b = rd(bk)
    if len(d) < 2 or len(d) != len(b): continue
    for i in range(len(d)):
        x, y2 = b[i].strip(), d[i].strip()
        if not x or not y2 or x == y2 or CJK.search(x) or not CJK.search(y2): continue
        xt = [t for t in re.split(r"[/ ]+", x) if t]
        yt = [t for t in re.split(r"[/ ]+", y2) if t]
        if len(xt) != len(yt): continue
        for a, c in zip(xt, yt):
            if CJK.search(a) or not CJK.search(c) or a == c: continue
            m = re.fullmatch(r"(\d+)?([A-Za-z]{1,3})", a)
            if m and m.group(2):
                sfx[m.group(2)][E][c] += 1
print("\n③ 同后缀 token 跨年代译法（只列跨年代差异大的）")
for s in sorted(sfx, key=lambda k: -sum(sum(v.values()) for v in sfx[k].values())):
    eras = sfx[s]
    if len(eras) < 2: continue
    tops = {e: eras[e].most_common(3) for e in sorted(eras)}
    dif = len({t[0][0] for t in tops.values() if t})
    if dif >= 2:
        print("   后缀 %-3s : %s" % (s, " | ".join("%s=%s" % (e, ",".join("%s(%d)" % kv for kv in t)) for e, t in tops.items())))
