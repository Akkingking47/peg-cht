# -*- coding: utf-8 -*-
"""Full 648-scenario nation scan + rebucket the 6414 untranslated-designation rows.
Unit layout: S0=11350, 65B/unit, +34=side, +36=nation id, id -> WW2Gui line (id-1).
_u alignment: line i -> unit i; if line0 is 'Dummy'/'dummy' -> line i -> unit i-1.
"""
import os, sys, io
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SCN = r"D:\Program Files\PeG-WW2\SCENARIO"
RES = r"d:\DSH\军事游戏汉化\pegww2\research"
DER = os.path.join(RES, "_derived")          # 生成器产出（可复算，勿手改）
os.makedirs(DER, exist_ok=True)
S0, P = 11350, 65
NAT = {1:"南斯拉夫",2:"比利时",3:"德国",4:"苏联",5:"意大利",6:"芬兰",7:"法国",8:"共和军",
       9:"希腊",10:"美国",11:"匈牙利",12:"国民军",13:"英国",14:"挪威",15:"武装党卫军",
       16:"波兰",17:"保加利亚",18:"罗马尼亚",19:"加拿大",20:"捷克斯洛伐克",0:"无国家"}

idx = {f.lower(): f for f in os.listdir(SCN)}

# ---- 1. scan all scn ----
scn_info = {}   # stem_lower -> dict
for f in os.listdir(SCN):
    if not f.lower().endswith(".scn"): continue
    stem = f[:-4]
    d = open(os.path.join(SCN, f), "rb").read()
    n = (len(d) - S0) // P
    nats = [d[S0 + i*P + 36] for i in range(n)]
    sides = [d[S0 + i*P + 34] for i in range(n)]
    scn_info[stem.lower()] = dict(stem=stem, n=n, nats=nats, sides=sides)

# ---- 2. per-scenario audit TSV ----
with open(os.path.join(RES, "_场景国籍精确归属-20261020.tsv"), "w", encoding="utf-8") as fh:
    fh.write("# .SCN 国籍精确归属 20261020\t布局 S0=11350 65B/单位 +34阵营 +36国籍\n")
    fh.write("场景\t单位数\t阵营0\t阵营1\t_u行数\tDummy头\t备注\n")
    for k in sorted(scn_info):
        info = scn_info[k]
        c0 = Counter(NAT.get(info["nats"][i], "?") for i in range(info["n"]) if info["sides"][i] == 0)
        c1 = Counter(NAT.get(info["nats"][i], "?") for i in range(info["n"]) if info["sides"][i] == 1)
        f0 = "/".join(f"{a}{b}" for a, b in sorted(c0.items(), key=lambda x: -x[1]))
        f1 = "/".join(f"{a}{b}" for a, b in sorted(c1.items(), key=lambda x: -x[1]))
        ukey = k + "_u.txt"
        nu, dum = "", ""
        if ukey in idx:
            t = open(os.path.join(SCN, idx[ukey]), "rb").read().decode("gbk", errors="replace")
            L = t.split("\r\n")
            if L and L[-1] == "": L.pop()
            nu = len(L)
            if L and L[0].strip().lower() == "dummy": dum = "Y"
        fh.write(f'{info["stem"]}\t{info["n"]}\t{f0}\t{f1}\t{nu}\t{dum}\t\n')

# ---- 3. rebucket ----
src = os.path.join(DER, "_番号未展开统计-20261020.tsv")
rows = [l.rstrip("\n").split("\t") for l in open(src, encoding="utf-8") if l.strip()]
header = rows[0]
data = [r for r in rows[1:] if len(r) >= 5]

# group row order per scenario for FIFO matching
per_scn_text = defaultdict(list)   # stem_lower -> list of (text, rowidx)
for i, r in enumerate(data):
    per_scn_text[r[3].lower()].append((r[4].strip(), i))

assign = {}   # rowidx -> (nation, lineno, side, note)
for stem_l, items in per_scn_text.items():
    ukey = stem_l + "_u.txt"
    if ukey not in idx:
        for _, i in items: assign[i] = ("无_u", -1, "", "_u缺失")
        continue
    t = open(os.path.join(SCN, idx[ukey]), "rb").read().decode("gbk", errors="replace")
    L = t.split("\r\n")
    if L and L[-1] == "": L.pop()
    dummy = bool(L and L[0].strip().lower() == "dummy")
    off = 1 if dummy else 0
    info = scn_info.get(stem_l)
    # map text -> queue of line numbers
    pos = defaultdict(list)
    for ln, txt in enumerate(L):
        s = txt.strip()
        if s: pos[s].append(ln)
    for text, i in items:
        q = pos.get(text)
        if not q:
            assign[i] = ("未匹配", -1, "", "原文行在_u中找不到(可能重复/已变)")
            continue
        ln = q.pop(0)
        unit_i = ln - off
        if info is None:
            assign[i] = ("无scn", ln, "", "")
        elif unit_i < 0:
            assign[i] = ("Dummy头", ln, "", "")
        elif unit_i >= info["n"]:
            assign[i] = ("越界", ln, "", f"行{ln}>单位数{info['n']}")
        else:
            nat = NAT.get(info["nats"][unit_i], f"?{info['nats'][unit_i]}")
            assign[i] = (nat, ln, info["sides"][unit_i], "")

# ---- 4. write new TSV ----
dst = os.path.join(DER, "_番号未展开统计-按SCN国籍-20261020.tsv")
with open(dst, "w", encoding="utf-8") as fh:
    fh.write("# 未展开番号统计v3 20261020 .SCN精确国籍\t国别(.scn)\t战役族\t战区\t场景\t行号\t阵营\t原文行\t国别(旧推断)\n")
    for i, r in enumerate(data):
        nat, ln, side, note = assign[i]
        old = r[0]
        fh.write(f"{nat}\t{r[1]}\t{r[2]}\t{r[3]}\t{ln}\t{side}\t{r[4]}\t{old}\n")

# ---- 5. summary ----
tot = Counter()
old_vs_new = Counter()
notes = Counter()
for i, r in enumerate(data):
    nat, ln, side, note = assign[i]
    tot[nat] += 1
    if note: notes[note.split("(")[0]] += 1
    old_vs_new[(r[0], nat)] += 1

print("== 新国别分布 ==")
for k, v in tot.most_common(): print(f"  {k}\t{v}")
print("== 异常/诊断 ==")
for k, v in notes.most_common(): print(f"  {k}\t{v}")
print("== 旧推断 -> 新归属 主要变化 ==")
for (o, n), v in sorted(old_vs_new.items(), key=lambda x: -x[1]):
    if o != n and v >= 5: print(f"  {o} -> {n}\t{v}")
