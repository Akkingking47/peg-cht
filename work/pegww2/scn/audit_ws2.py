# -*- coding: utf-8 -*-
"""pegww2 专项：精确重复、迭代轮次冗余、被脚本引用情况。"""
import os, sys, io, hashlib, re, subprocess
from collections import defaultdict, Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"d:\DSH\军事游戏汉化"
P = os.path.join(ROOT, "pegww2")
WS = os.path.join(ROOT, "work")

files = []
for dp, dn, fn in os.walk(P):
    dn[:] = [d for d in dn if d not in ("__pycache__",)]
    for f in fn:
        p = os.path.join(dp, f)
        try: files.append((p, os.path.getsize(p)))
        except OSError: pass
print("pegww2 文件 %d，%.1f MB" % (len(files), sum(s for _, s in files) / 1048576))
sub = defaultdict(lambda: [0, 0])
for p, s in files:
    k = os.path.relpath(p, P).split(os.sep)[0]
    sub[k][0] += 1; sub[k][1] += s
for k, (n, s) in sorted(sub.items(), key=lambda x: -x[1][1]): print("   %-16s %5d  %7.2f MB" % (k, n, s / 1048576))

h = defaultdict(list)
for p, s in files:
    try: h[hashlib.md5(open(p, "rb").read()).hexdigest()].append((p, s))
    except OSError: pass
dups = {k: v for k, v in h.items() if len(v) > 1}
print("\n== pegww2 内精确重复 %d 组，可省 %.2f MB ==" % (len(dups), sum(sum(s for _, s in v[1:]) for v in dups.values()) / 1048576))
for k, v in sorted(dups.items(), key=lambda x: -len(x[1]))[:12]:
    print("  x%-3d %7.1fKB  %s" % (len(v), v[0][1] / 1024, os.path.relpath(v[0][0], P)))
    print("       " + " ; ".join(os.path.basename(p2) for p2, _ in v[1:6]))

# 迭代轮次家族
fam = defaultdict(list)
for p, s in files:
    b = os.path.basename(p)
    m = re.match(r"(.+?)[-_]r(\d+)[-_]\d+\.tsv$", b)
    if m: fam[m.group(1)].append((int(m.group(2)), p, s))
    elif ".pre-" in b: fam["*.pre-*"].append((0, p, s))
print("\n== 按轮次迭代的家族（只列含>=3轮的） ==")
tot = 0
for k, v in sorted(fam.items(), key=lambda x: -sum(s for _, _, s in x[1])):
    if len(v) >= 3:
        rounds = sorted(set(r for r, _, _ in v))
        mm = defaultdict(list)
        for r, p, s in v: mm[hashlib.md5(open(p, "rb").read()).hexdigest()].append((r, os.path.basename(p)))
        uniq = len(mm)
        print("  %-42s 轮次%d~%d 共%d个文件 内容去重后%d种  %.2fMB" % (k, min(rounds), max(rounds), len(v), uniq, sum(s for _, _, s in v) / 1048576))
        tot += sum(s for _, _, s in v)
print("  迭代家族合计 %.2f MB" % (tot / 1048576))

# 脚本引用检查：work/ 下的 .py 是否引用 research 里的名字
pytext = ""
for dp, dn, fn in os.walk(WS):
    dn[:] = [d for d in dn if d not in ("__pycache__",)]
    for f in fn:
        if f.endswith(".py"):
            try: pytext += open(os.path.join(dp, f), encoding="utf-8", errors="replace").read()
            except OSError: pass
plain = set(re.findall(r"[\w\-.]+\.tsv", pytext))
print("\n== 脚本里出现的 .tsv 名（去重 %d） ==" % len(plain))
inter = sorted(n for n in plain if os.path.isfile(os.path.join(P, "research", n)))
print("  其中在 research 目录真实存在：", len(inter))
print("  ", ", ".join(inter[:40]))
