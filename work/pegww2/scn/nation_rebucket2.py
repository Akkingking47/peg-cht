# -*- coding: utf-8 -*-
"""用 +8(_u索引) 重映射 6414 行番号 -> 精确国籍；并给出各场景映射自检。"""
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

def u_of(stem):
    k = idx.get((stem+"_u.txt").lower())
    if not k: return None
    t = open(os.path.join(SCN, k), "rb").read().decode("gbk", errors="replace").split("\r\n")
    if t and t[-1] == "": t.pop()
    return t

scen = {}     # stem_lower -> (nats list, u lines, rev map line->set(unit idx))
for f in os.listdir(SCN):
    if not f.lower().endswith(".scn"): continue
    stem = f[:-4]; sl = stem.lower()
    d = open(os.path.join(SCN, f), "rb").read(); n = (len(d) - S0) // P
    nats = [d[S0+i*P+36] for i in range(n)]
    k8 = [d[S0+i*P+8] | (d[S0+i*P+9] << 8) for i in range(n)]
    u = u_of(stem)
    rev = defaultdict(set)
    if u:
        for i, x in enumerate(k8):
            if 0 <= x < len(u): rev[x].add(i)
    scen[sl] = (nats, u, rev)

src = os.path.join(DER, "_番号未展开统计-20261020.tsv")
rows = [l.rstrip("\n").split("\t") for l in open(src, encoding="utf-8") if l.strip()]
data = [r for r in rows[1:] if len(r) >= 5]

assign = {}
pat_by_nat = defaultdict(Counter)
for i, r in enumerate(data):
    sl, text = r[3].lower(), r[4].strip()
    e = scen.get(sl)
    if e is None:
        assign[i] = ("无scn", "", "scn缺失"); continue
    nats, u, rev = e
    lines = [ln for ln, t in enumerate(u) if t.strip() == text] if u else []
    if not lines:
        assign[i] = ("未匹配", "", "行文本在_u中无对应"); continue
    votes = []
    for ln in lines:
        for ui in rev.get(ln, ()): votes.append(ui)
    if not votes:
        assign[i] = ("未匹配", "", "该_u行无+8引用"); continue
    c = Counter(NAT.get(nats[ui], "?") for ui in votes)
    nat, cnt = c.most_common(1)[0]
    tie = "歧义" if len(c) > 1 else ""
    assign[i] = (nat, tie, "")
    pat_by_nat[nat][text] += 1

dst = os.path.join(DER, "_番号未展开统计-按SCN国籍v2-20261020.tsv")
with open(dst, "w", encoding="utf-8") as fh:
    fh.write("# 未展开番号 v2(.SCN +8→_u 索引)\t国别\t战役族\t战区\t场景\t原文行\t备注\t旧推断\n")
    for i, r in enumerate(data):
        nat, tie, note = assign[i]
        fh.write(f"{nat}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\t{tie}\t{r[0]}\n")

tot = Counter(v[0] for v in assign.values())
print("== 新国别分布(v2 +8映射) ==")
for k, v in tot.most_common(): print(f"  {k}\t{v}")
print("\n== 各国「未展开番号」去重后条目数 / 出现次数 ==")
for k, v in sorted(pat_by_nat.items(), key=lambda x: -sum(x[1].values())):
    print(f"  {k}\t去重{len(v)}\t总{sum(v.values())}\t样例: {', '.join(list(v)[:6])}")
