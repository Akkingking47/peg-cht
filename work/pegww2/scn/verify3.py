# -*- coding: utf-8 -*-
"""复核 v3：并排对比 +8索引名 与 位置名，判定 _u↔单位 映射。"""
import os, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SCN = r"D:\Program Files\PeG-WW2\SCENARIO"
S0, P = 11350, 65
NAT = {1:"南斯拉夫",2:"比利时",3:"德国",4:"苏联",5:"意大利",6:"芬兰",7:"法国",8:"共和军",
       9:"希腊",10:"美国",11:"匈牙利",12:"国民军",13:"英国",14:"挪威",15:"武装党卫军",
       16:"波兰",17:"保加利亚",18:"罗马尼亚",19:"加拿大",20:"捷克斯洛伐克",0:"无国家"}
idx = {f.lower(): f for f in os.listdir(SCN)}

def scn(stem): return open(os.path.join(SCN, idx[(stem+".scn").lower()]), "rb").read()

def u_of(stem):
    k = idx.get((stem+"_u.txt").lower())
    if not k: return None
    t = open(os.path.join(SCN, k), "rb").read().decode("gbk", errors="replace").split("\r\n")
    if t and t[-1] == "": t.pop()
    return t

d = scn("RTB01"); n = (len(d)-S0)//P; u = u_of("RTB01")
print(f"RTB01 units={n} u_lines={len(u)}")
print(" i  sid  nat  +8  | _u[+8]                     | _u[i]")
for i in list(range(0,8)) + list(range(82,110)) + list(range(153, n)):
    r = S0+i*P
    k8 = d[r+8] | (d[r+9] << 8)
    a = u[k8][:26] if k8 < len(u) else "<OOR %d>" % k8
    b = u[i][:26] if i < len(u) else "<无>"
    print(f"{i:3d}  {d[r+34]:3d}  {d[r+36]:3d}  {k8:4d} | {a:26s} | {b}")

print("\n== 全局：+8 是否对各场景构成「按side分组」的连续块 ==")
tot = Counter()
for f in sorted(os.listdir(SCN)):
    if not f.lower().endswith(".scn"): continue
    stem = f[:-4]
    dd = open(os.path.join(SCN, f), "rb").read(); nn = (len(dd)-S0)//P
    uu = u_of(stem)
    if not uu: tot["无_u"] += 1; continue
    s0 = [dd[S0+i*P+8] | (dd[S0+i*P+9] << 8) for i in range(nn) if dd[S0+i*P+34] == 0]
    s1 = [dd[S0+i*P+8] | (dd[S0+i*P+9] << 8) for i in range(nn) if dd[S0+i*P+34] == 1]
    if s0 and s1 and max(s0) < min(s1): tot["side分块干净"] += 1
    elif s0 and s1 and max(s1) < min(s0): tot["side分块干净(逆)"] += 1
    else: tot["side混叠"] += 1
print(dict(tot))
