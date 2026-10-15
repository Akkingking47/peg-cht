# -*- coding: utf-8 -*-
r"""KAISER `.xscn` 覆盖面量测：唯一串里有多少能由既有资产直接填出。

资产（优先级从高到低）：
  1. `work\xscn\_xscn_dict.tsv`（跨 efile `.xscn` 词典，7 个已交付 efile 实证）
  2. `work\kaiser\root-manual.tsv` 的 equip/names/nations 条目（**跨层一致**）
  3. `glossary\standard-glossary.tsv`（标准译名库）
  4. 口径保留判据（纯代号/罗马数字/纯符号）

用法: python measure_xscn_cov.py
"""
import collections
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
W = r"D:\DSH\军事游戏汉化"


def rd2(p, strip_cols=0):
    d = {}
    if not os.path.exists(p):
        return d
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        f.readline()
        for ln in f:
            ln = ln.rstrip("\r\n")
            if not ln:
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0].strip() and c[1].strip():
                k = c[0].strip()
                v = c[1] if strip_cols is None else c[strip_cols]
                d.setdefault(k, v)
    return d


uniq = {}
with io.open(os.path.join(HERE, "xscn-uniq.tsv"), encoding="utf-8-sig", newline="") as f:
    f.readline()
    for ln in f:
        ln = ln.rstrip("\r\n")
        if not ln:
            continue
        c = ln.split("\t")
        uniq[c[0]] = int(c[1])

DICT = rd2(os.path.join(W, "work", "xscn", "_xscn_dict.tsv"))
ROOTM = rd2(os.path.join(W, "work", "kaiser", "root-manual.tsv"), 1)   # file,src,dst -> 用 src->dst
ROOTM2 = {}
with io.open(os.path.join(W, "work", "kaiser", "root-manual.tsv"), encoding="utf-8-sig", newline="") as f:
    f.readline()
    for ln in f:
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= 3 and c[0] in ("equip.txt", "names.txt", "nations.txt", "strings_efile.txt"):
            ROOTM2.setdefault(c[1].strip(), c[2])
GLOSS = rd2(os.path.join(W, "glossary", "standard-glossary.tsv"))

CODE = [
    re.compile(r"^[\[\]A-Za-z0-9\.\-/ '&,+()#]*$"),      # 纯 ASCII 代号型
    re.compile(r"^[IVXLCDM]+$"),
    re.compile(r"^[\W_]+$"),
    re.compile(r"^\d+$"),
]

hit = collections.Counter()
rest = collections.Counter()
for k, n in uniq.items():
    if k in DICT:
        hit["_xscn_dict"] += 1
    elif k in ROOTM2:
        hit["root-manual"] += 1
    elif k in GLOSS:
        hit["glossary"] += 1
    elif any(rx.match(k) for rx in CODE):
        hit["口径保留(纯 ASCII)"] += 1
    else:
        rest[k] = n

tot = len(uniq)
print("KAISER .xscn 唯一串 %d" % tot)
for k, v in hit.most_common():
    print("   %-20s %6d  (%.1f%%)" % (k, v, 100.0 * v / tot))
print("   %-20s %6d  (%.1f%%)  ← 待译" % ("其余", len(rest), 100.0 * len(rest) / tot))
print("   合计命中 %.1f%%" % (100.0 * (tot - len(rest)) / tot))

# 待译按组分类
gi_of = collections.defaultdict(collections.Counter)
with io.open(os.path.join(HERE, "xscn-uniq.tsv"), encoding="utf-8-sig", newline="") as f:
    f.readline()
    for ln in f:
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= 3 and c[0] in rest:
            for g in c[2].split(","):
                gi_of[g][c[0]] = rest[c[0]]
print("\n待译按组：")
for g in sorted(gi_of, key=lambda x: -sum(gi_of[x].values())):
    print("   组%-4s %6d 串 / %6d 处" % (g, len(gi_of[g]), sum(gi_of[g].values())))
with io.open(os.path.join(HERE, "_xscn_todo.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("src\tfreq\tgroups\n")
    for k, n in sorted(rest.items(), key=lambda kv: -kv[1]):
        gs = []
        for g, cc in gi_of.items():
            if k in cc:
                gs.append(g)
        f.write("%s\t%d\t%s\n" % (k, n, ",".join(sorted(gs))))
print("\n已写 _xscn_todo.tsv（%d 条）" % len(rest))
