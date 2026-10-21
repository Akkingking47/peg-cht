# -*- coding: utf-8 -*-
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"D:\Program Files\PeG-WW2\SCENARIO"
idx = {f.lower(): f for f in os.listdir(D)}
NAT = {1:"南斯拉夫",2:"比利时",3:"德国",4:"苏联",5:"意大利",6:"芬兰",7:"法国",8:"共和军",
       9:"希腊",10:"美国",11:"匈牙利",12:"国民军",13:"英国",14:"挪威",15:"武装党卫军",
       16:"波兰",17:"保加利亚",18:"罗马尼亚",19:"加拿大",20:"捷克斯洛伐克",0:"无国家"}

print("=== 已完全汉化的 _u 输出格式样例 ===")
for stem in ["drkhar19", "drstlo25", "drboro14", "LAH_IT_15"]:
    k = idx.get((stem + "_u.txt").lower())
    if not k: continue
    t = open(os.path.join(D, k), "rb").read().decode("gbk", errors="replace").split("\r\n")
    print("-- %s (%d行)" % (stem, len(t)))
    for l in t[:18]: print("     ", l[:46])

print("\n=== oakridge 单位明细 ===")
d = open(os.path.join(D, idx["oakridge.scn"]), "rb").read(); n = (len(d) - 11350) // 65
u = open(os.path.join(D, idx["oakridge_u.txt"]), "rb").read().decode("gbk", errors="replace").split("\r\n")
print("i side nat +8 | _u[+8] | _u[i]")
for i in range(n):
    r = 11350 + i * 65
    k8 = d[r+8] | (d[r+9] << 8)
    a = u[k8][:24] if k8 < len(u) else "<OOR%d>" % k8
    b = u[i][:24] if i < len(u) else "<无>"
    print("%3d  %d   %d  %4d | %-24s | %s" % (i, d[r+34], d[r+36], k8, a, b))
