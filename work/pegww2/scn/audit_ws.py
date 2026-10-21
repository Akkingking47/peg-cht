# -*- coding: utf-8 -*-
"""工作区体检：目录规模、精确重复文件、疑似迭代冗余家族。"""
import os, sys, io, hashlib, re
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"d:\DSH\军事游戏汉化"
SKIP_DIRS = {"__pycache__", "_rebuild-tmp", "_regen-catfix", ".git"}

files = []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in SKIP_DIRS]
    for f in fn:
        p = os.path.join(dp, f)
        try: sz = os.path.getsize(p)
        except OSError: continue
        files.append((p, sz))
print("工作区文件总数 %d，合计 %.1f MB" % (len(files), sum(s for _, s in files) / 1048576))
dirstat = defaultdict(lambda: [0, 0])
for p, s in files:
    d = os.path.relpath(os.path.dirname(p), ROOT).split(os.sep)[0]
    dirstat[d][0] += 1; dirstat[d][1] += s
print("\n== 顶层目录规模 ==")
for d, (n, s) in sorted(dirstat.items(), key=lambda x: -x[1][1]):
    print("  %-14s %4d 个文件  %7.2f MB" % (d, n, s / 1048576))

# 精确重复
h = defaultdict(list)
for p, s in files:
    try:
        h[hashlib.md5(open(p, "rb").read()).hexdigest()].append((p, s))
    except OSError: pass
dups = {k: v for k, v in h.items() if len(v) > 1}
waste = sum(sum(s for _, s in v[1:]) for v in dups.values())
print("\n== 精确重复：%d 组，可省 %.1f MB ==" % (len(dups), waste / 1048576))
for k, v in sorted(dups.items(), key=lambda x: -sum(s for _, s in x[1]))[:25]:
    print("  x%d  %6.1fKB  %s" % (len(v), v[0][1] / 1024, os.path.relpath(v[0][0], ROOT)))
    for p2, _ in v[1:4]: print("       同 → %s" % os.path.relpath(p2, ROOT))

# 迭代冗余家族（_scn-todo-prose-rN、_scn-fill-u-rN、.pre-*）
fam = defaultdict(list)
for p, s in files:
    b = os.path.basename(p)
    m = re.match(r"(_scn-(?:todo|fill)-(?:prose|u|m)[-_].*?)[-_]r\d+", b)
    if m: fam[m.group(1) + "__rNN"].append((p, s))
    elif ".pre-" in b: fam["*.pre-*"].append((p, s))
print("\n== 迭代/备份家族 ==")
for k, v in sorted(fam.items(), key=lambda x: -sum(s for _, s in x[1])):
    if len(v) > 1:
        print("  %-40s %3d 个  %7.2f MB" % (k, len(v), sum(s for _, s in v) / 1048576))
