# -*- coding: utf-8 -*-
"""对照表最终版：各类形态的 改前 -> 改后 抽样（供审阅）。"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = r"d:\DSH\军事游戏汉化\pegww2\research\_番号展开-对照表-20261020.tsv"
rows = [l.rstrip("\n").split("\t") for l in open(p, encoding="utf-8") if l.strip()][1:]
rows = [r for r in rows if len(r) >= 9]
def kind(s):
    s = s.strip()
    if re.fullmatch(r"\d+", s): return "单段裸数字"
    if re.fullmatch(r"[\d/\-]+", s): return "多段纯数字链"
    if re.search(r"[Uu]-[0-9]+", s): return "潜艇番号"
    if re.search(r"\d+[A-Za-z]", s): return "数字+字母后缀"
    if re.fullmatch(r"[A-Za-z]{1,5}", s): return "纯字母代号"
    if re.search(r"[a-z]{3,}", s): return "词形名/舰名"
    return "其他"
buckets = {}
for r in rows:
    buckets.setdefault(kind(r[4]), []).append(r)
for k in ["单段裸数字", "多段纯数字链", "数字+字母后缀", "纯字母代号", "潜艇番号", "词形名/舰名", "其他"]:
    v = buckets.get(k, [])
    print("\n### %s（%d 行）###" % (k, len(v)))
    seen = set()
    for r in v:
        key = (r[0], r[5])
        if key in seen: continue
        seen.add(key)
        print("  %-8s %-22s -> %-28s [%s %s]" % (r[0], r[4][:22], r[5][:28], r[7], r[6][:26]))
        if len(seen) >= 8: break
