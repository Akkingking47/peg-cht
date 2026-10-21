# -*- coding: utf-8 -*-
import io, sys, re
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = r"d:\DSH\军事游戏汉化\pegww2\research\_番号展开-对照表-20261020.tsv"
rows = [l.rstrip("\n").split("\t") for l in open(p, encoding="utf-8") if l.strip()][1:]
rows = [r for r in rows if len(r) >= 9]
pend = [r for r in rows if r[7] in ("待判", "部分待判")]
SHIP = re.compile(r"\b(HMS|KMS|USS|ITS|FRS|RAN|VK|CR|Dt|Lgt|CA|RM|SMG|R\.Smg)\b")
NEEDCODE = Counter()
def kind(s):
    if SHIP.search(s): return "舰船(前缀)"
    if re.search(r"[a-z]{3,}", s): return "人名/地名词形"
    if re.fullmatch(r"[A-Z]{1,4}[0-9]*(\s?\[[^\]]*\])?", s): return "内部代号"
    if re.search(r"\d", s) and re.search(r"[A-Za-z]", s): return "数字+字母码"
    return "其他"
for r in pend:
    NEEDCODE[kind(r[4])] += 1
print("待判/部分待判 合计 %d（占 %d 行的 %.0f%%）" % (len(pend), len(rows), 100.0*len(pend)/len(rows)))
for k, v in NEEDCODE.most_common(): print("  %s\t%d" % (k, v))
# 内部代号去重清单
codes = sorted({r[4].strip() for r in pend if kind(r[4]) == "内部代号"})
print("\n内部代号去重 %d 个：%s" % (len(codes), ", ".join(codes[:60])))
ships = sorted({r[4].strip() for r in pend if kind(r[4]) == "舰船(前缀)"})
print("\n舰船去重 %d 个（前30）：%s" % (len(ships), ", ".join(ships[:30])))
