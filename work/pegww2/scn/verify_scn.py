# -*- coding: utf-8 -*-
"""SCN 布局复核：确认 +14=全局单位索引、65B/单位、S0=11350；并定位 _u 行索引字段。"""
import os, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SCN = r"D:\Program Files\PeG-WW2\SCENARIO"
S0, P = 11350, 65
idx = {f.lower(): f for f in os.listdir(SCN)}

def rd(f): return open(os.path.join(SCN, f), "rb").read()

def u_of(stem):
    k = (stem + "_u.txt").lower()
    if k not in idx: return None
    t = open(os.path.join(SCN, idx[k]), "rb").read().decode("gbk", errors="replace").split("\r\n")
    if t and t[-1] == "": t.pop()
    return t

scns = sorted(f for f in os.listdir(SCN) if f.lower().endswith(".scn"))
bad14 = []
udiff = Counter()
for f in scns:
    d = rd(f); n = (len(d) - S0) // P
    for i in range(n):
        if (d[S0+i*P+14] | (d[S0+i*P+15] << 8)) != i:
            bad14.append((f, i, d[S0+i*P+14] | (d[S0+i*P+15] << 8))); break
    u = u_of(f[:-4])
    udiff[n - (len(u) if u else -1)] += 1
print(f"scn 总数 {len(scns)}   +14==i 校验失败 {len(bad14)}  失败样例 {bad14[:8]}")
print(f"单位数 - _u行数 分布（前12）: {udiff.most_common(12)}")

# 对 RTB01 逐列测试：哪一列是 _u 行索引
d = rd("RTB01.scn"); n = (len(d) - S0) // P
u = u_of("RTB01")
print(f"\nRTB01 units={n} u_lines={len(u)}  (+14 校验: {all((d[S0+i*P+14]|(d[S0+i*P+15]<<8))==i for i in range(n))})")
for c in range(0, 64):
    vec = [d[S0+i*P+c] | (d[S0+i*P+c+1] << 8) for i in range(n)]
    if max(vec) <= max(len(u), n) and len(set(vec)) > n * 0.8:
        perm = sorted(vec) == list(range(n)) or sorted(vec) == list(range(1, n+1))
        if max(vec) <= len(u) or perm:
            print(f"  col+{c}: min={min(vec)} max={max(vec)} distinct={len(set(vec))} 是0..n排列={perm} 值域占u比例={max(vec)/len(u):.2f}")
# 打印 RTB01 每单位 [i, +8, +10, +12, +14, +34, +36]
print("\nRTB01 前6/后6单位 [i +8 +10 +12 +14 +34 +36]:")
for i in list(range(0, 6)) + list(range(n-6, n)):
    r = S0 + i*P
    print(f"  {i:3d} +8={d[r+8]|(d[r+9]<<8):5d} +10={d[r+10]|(d[r+11]<<8):5d} +12={d[r+12]|(d[r+13]<<8):5d} +14={d[r+14]|(d[r+15]<<8):5d} side={d[r+34]} nat={d[r+36]}")
