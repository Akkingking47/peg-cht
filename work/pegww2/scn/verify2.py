# -*- coding: utf-8 -*-
"""复核 v2：_u 翻译率普查 + 定位 _u 行索引字段（疑 +8）。"""
import os, sys, io, re
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SCN = r"D:\Program Files\PeG-WW2\SCENARIO"
S0, P = 11350, 65
NAT = {1:"南斯拉夫",2:"比利时",3:"德国",4:"苏联",5:"意大利",6:"芬兰",7:"法国",8:"共和军",
       9:"希腊",10:"美国",11:"匈牙利",12:"国民军",13:"英国",14:"挪威",15:"武装党卫军",
       16:"波兰",17:"保加利亚",18:"罗马尼亚",19:"加拿大",20:"捷克斯洛伐克",0:"无国家"}
idx = {f.lower(): f for f in os.listdir(SCN)}
CJK = re.compile(r"[\u4e00-\u9fff]")

def rdkey(stem, ext):
    return idx.get((stem + ext).lower())

def u_of(stem):
    k = rdkey(stem, "_u.txt")
    if not k: return None
    t = open(os.path.join(SCN, k), "rb").read().decode("gbk", errors="replace").split("\r\n")
    if t and t[-1] == "": t.pop()
    return t

rows = []
for f in sorted(os.listdir(SCN)):
    if not f.lower().endswith("_u.txt"): continue
    t = open(os.path.join(SCN, f), "rb").read().decode("gbk", errors="replace").split("\r\n")
    if t and t[-1] == "": t.pop()
    nz = [x for x in t if x.strip()]
    cj = sum(1 for x in nz if CJK.search(x))
    rows.append((cj / max(1, len(nz)), len(nz), cj, f))
rows.sort(reverse=True)
print("== _u 中文率 最高12 ==")
for r in rows[:12]: print(f"  {r[3]}  行{r[1]} 中文{r[2]} 率{r[0]:.0%}")
print("== 中文率 最低(>0)10 ==")
for r in [x for x in rows if x[0] > 0][-10:]: print(f"  {r[3]}  行{r[1]} 中文{r[2]} 率{r[0]:.0%}")
z = sum(1 for r in rows if r[0] == 0)
print(f"中文率=0 的 _u 文件数: {z} / {len(rows)}")

print("\n== +8 作为 _u 行索引 验证 ==")
for stem in ["RTB01", "viipuri", "DAK_DAK1", "fi01"]:
    k = rdkey(stem, ".scn")
    if not k: print(f"  {stem}: no scn"); continue
    d = open(os.path.join(SCN, k), "rb").read(); n = (len(d) - S0) // P
    u = u_of(stem); v = None
    if u is None: print(f"  {stem}: no _u"); continue
    vals = [d[S0+i*P+8] | (d[S0+i*P+9] << 8) for i in range(n)]
    inr = sum(1 for x in vals if x < len(u))
    cjk_nat = Counter()
    for i, x in enumerate(vals):
        if x < len(u) and CJK.search(u[x]):
            cjk_nat[NAT.get(d[S0+i*P+36], "?")] += 1
    print(f"  {stem}: units={n} u_lines={len(u)} +8域[{min(vals)},{max(vals)}] 入范围{inr}/{n} 重复={len(set(vals))!=len(vals)}")
    print(f"      中文名单位国籍分布: {dict(cjk_nat)}")
    if stem == "RTB01":
        for i in range(6):
            r = S0 + i*P
            nm = u[vals[i]] if vals[i] < len(u) else "<OOR>"
            print(f"      u{i} raw20={' '.join('%02x' % d[r+k] for k in range(20))} idx8={vals[i]} name={nm[:28]}")
