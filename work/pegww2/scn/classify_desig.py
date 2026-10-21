# -*- coding: utf-8 -*-
"""对 6414 行未展开番号按「形态」分类，看各国待译的实际构成。"""
import os, sys, io, re
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = r"d:\DSH\军事游戏汉化\pegww2\research\_derived\_番号未展开统计-按SCN国籍v2-20261020.tsv"
rows = [l.rstrip("\n").split("\t") for l in open(p, encoding="utf-8") if l.strip()]
data = [r for r in rows[1:] if len(r) >= 6]

def kind(s):
    if re.fullmatch(r"[0-9/\-]+", s): return "纯数字链"
    if re.fullmatch(r"\[[0-9A-Za-z ]+\]", s): return "方括号码"
    if re.fullmatch(r"[0-9]+[A-Za-z]?([/\-][0-9A-Za-z]*)*", s): return "数字+字母"
    if re.fullmatch(r"[A-Za-z]{1,4}", s): return "短字母码"
    if " " in s or re.search(r"[a-z]{3,}", s): return "词形名"
    return "其他"

by = defaultdict(Counter); uniq = defaultdict(Counter)
for r in data:
    nat, s = r[0], r[4].strip()
    by[nat][kind(s)] += 1
    uniq[nat][s] += 1

print("国别          形态分布（行数）")
for nat in sorted(by, key=lambda x: -sum(by[x].values())):
    tot = sum(by[nat].values())
    ks = "  ".join(f"{k}:{v}" for k, v in by[nat].most_common())
    print(f"{nat:8s} {tot:5d}  {ks}")
print("\n== 短字母码/其他 去重样例（每国前14） ==")
for nat in sorted(by, key=lambda x: -sum(by[x].values())):
    ex = [s for s, c in uniq[nat].most_common() if kind(s) in ("短字母码", "其他", "词形名")]
    if ex: print(f"  {nat}: {', '.join(ex[:14])}")
