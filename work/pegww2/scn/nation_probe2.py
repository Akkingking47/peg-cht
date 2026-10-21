# -*- coding: utf-8 -*-
"""Probe v2: fixed S0=11350, 65B/unit. Dump nation(+36)/side(+34) and _u alignment."""
import os, sys, io
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SCN_DIR = r"D:\Program Files\PeG-WW2\SCENARIO"
S0, P = 11350, 65

NAT = {1:"南斯拉夫",2:"比利时",3:"德国",4:"苏联",5:"意大利",6:"芬兰",7:"法国",8:"共和军",
       9:"希腊",10:"美国",11:"匈牙利",12:"国民军",13:"英国",14:"挪威",15:"武装党卫军",
       16:"波兰",17:"保加利亚",18:"罗马尼亚",19:"加拿大",20:"捷克斯洛伐克"}

idx = {f.lower(): f for f in os.listdir(SCN_DIR)}

def rd(stem):
    return open(os.path.join(SCN_DIR, idx[(stem + ".scn").lower()]), "rb").read()

def ulines(stem):
    key = (stem + "_u.txt").lower()
    if key not in idx: return None
    t = open(os.path.join(SCN_DIR, idx[key]), "rb").read().decode("gbk", errors="replace")
    L = t.split("\r\n")
    if L and L[-1] == "": L.pop()
    return L

def probe(stem, note=""):
    d = rd(stem)
    n = (len(d) - S0) // P
    u = ulines(stem)
    nu = len(u) if u else 0
    nat = [d[S0 + i * P + 36] for i in range(n)]
    side = [d[S0 + i * P + 34] for i in range(n)]
    nd = Counter(nat)
    nds = {NAT.get(k, f"?{k}"): v for k, v in sorted(nd.items())}
    sd = Counter(side)
    # side x nation cross
    cross = Counter((side[i], NAT.get(nat[i], f"?{nat[i]}")) for i in range(n))
    print(f"== {stem} ({note}) units={n} u_lines={nu} diff={n-nu}")
    print(f"   nation: {nds}")
    print(f"   side: {dict(sd)}   side x nation: {dict(cross)}")
    if u:
        named = nu if nu <= n else n
        nn = Counter(NAT.get(nat[i], f"?{nat[i]}") for i in range(named))
        print(f"   named-range(0..{named-1}) nations: {dict(nn)}")
        # first mismatch between _u implicit order and nation blocks: show first 3 and around first side flip
        print(f"   u[0]={u[0][:40]!r}  u[last]={u[-1][:40]!r}")

for s, note in [
    ("RTB01", "斯大林格勒 Sov vs Ger"),
    ("kanev", "Ger vs Sov"),
    ("fi01", "Ger vs Fra"),
    ("ciechan", "Ger vs Pol"),
    ("salerno1", "Ger vs US"),
    ("antisal", "Ger vs UK/US"),
    ("oakridge", "Sov? vs US"),
    ("viipuri", "Sov vs Fin"),
    ("DAK_DAK1", "Ger/Ita vs UK"),
]:
    probe(s, note)
