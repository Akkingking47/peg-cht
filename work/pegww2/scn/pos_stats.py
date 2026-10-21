# -*- coding: utf-8 -*-
"""统计「斜杠位次 -> 编制规模词」概率：从 原版_u ↔ 已译_u 整行对齐中挖掘。
用途：给纯数字链补 师/团/营/连 等规模词。"""
import os, sys, io, re
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
DEP = r"D:\Program Files\PeG-WW2\SCENARIO"
BK = r"d:\DSH\军事游戏汉化\pegww2\testbed\backup\SCENARIO"
CJK = re.compile(r"[\u4e00-\u9fff]")
ECH = ["集团军群","集团军","装甲集团军","坦克集团军","骑兵军","机械化军","坦克军","步兵军",
       "装甲军","空降军","掷弹兵师","装甲师","步兵师","摩托化师","伞兵师","空降师","骑兵师",
       "坦克师","轻装师","守备师","警备师","军","师","旅","团","营","连","大队","中队","航空队","舰队","高地"]

def rd(p): return open(p, "rb").read().decode("gbk", errors="replace").split("\r\n")

def word_of(seg):
    """从中文段里取出编制规模词（去掉 第N / 罗马 前缀与括注）"""
    s = seg.split("[")[0]
    s = re.sub(r"^第\s*[0-9]+\s*", "", s).strip()
    for e in ECH:
        if s.endswith(e) and len(s) > len(e):
            return e
    return s if s in ECH else ""

stat = defaultdict(Counter)      # (segnum, pos) -> Counter(word)
stat2 = defaultdict(Counter)     # segnum -> Counter(每段是否带词模式)
tot = Counter()
for f in sorted(os.listdir(DEP)):
    if not f.lower().endswith("_u.txt"): continue
    bk = os.path.join(BK, f)
    if not os.path.isfile(bk): continue
    d = rd(os.path.join(DEP, f)); b = rd(bk)
    if len(d) < 2 or len(d) != len(b): continue
    for i in range(len(d)):
        x, y = b[i].strip(), d[i].strip()
        if not x or not y or x == y or CJK.search(x) or not CJK.search(y): continue
        xs = x.split("/"); ys = y.split("/")
        if len(xs) != len(ys) or len(xs) < 2: continue
        n = len(xs); tot[n] += 1
        pat = ""
        for p, seg in enumerate(ys):
            w = word_of(seg)
            if w: stat[(n, p)][w] += 1
            pat += ("W" if w else "-")
        stat2[n][pat] += 1

print("整行对齐（同段数）样本：", dict(tot))
for n in sorted({k[0] for k in stat}):
    print("\n== {} 段链 ==".format(n))
    for p in range(n):
        c = stat[(n, p)]
        if c:
            print("   位次%d（从0起）：%s" % (p, "  ".join("%s(%d)" % kv for kv in c.most_common(8))))
    print("   带词模式分布：", "  ".join("%s(%d)" % kv for kv in stat2[n].most_common(8)))
