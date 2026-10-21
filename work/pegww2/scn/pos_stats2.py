# -*- coding: utf-8 -*-
"""按【国别】统计「斜杠位次 -> 编制规模词」，用于给纯数字链补规模词。"""
import os, sys, io, re
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
DEP = r"D:\Program Files\PeG-WW2\SCENARIO"
BK = r"d:\DSH\军事游戏汉化\pegww2\testbed\backup\SCENARIO"
S0, P = 11350, 65
NAT = {1:"南斯拉夫",2:"比利时",3:"德国",4:"苏联",5:"意大利",6:"芬兰",7:"法国",8:"共和军",
       9:"希腊",10:"美国",11:"匈牙利",12:"国民军",13:"英国",14:"挪威",15:"武装党卫军",
       16:"波兰",17:"保加利亚",18:"罗马尼亚",19:"加拿大",20:"捷克斯洛伐克",0:"无国家"}
CJK = re.compile(r"[\u4e00-\u9fff]")
ECH = ["集团军群","集团军","装甲集团军","坦克集团军","骑兵军","机械化军","坦克军","步兵军",
       "装甲军","空降军","掷弹兵师","装甲师","步兵师","摩托化师","伞兵师","空降师","骑兵师",
       "坦克师","轻装师","守备师","警备师","航空师","军","师","旅","团","营","连","大队","中队","舰队"]

def rd(p): return open(p, "rb").read().decode("gbk", errors="replace").split("\r\n")

def word_of(seg):
    s = seg.split("[")[0]
    s = re.sub(r"^第\s*[0-9IVXLCDM]+\s*", "", s).strip()
    for e in ECH:
        if s.endswith(e) and len(s) > len(e): return e
    return s if s in ECH else ""

idx = {f.lower(): f for f in os.listdir(DEP)}
stat = defaultdict(Counter)     # (nat, seg, pos) -> Counter(word)
for f in sorted(os.listdir(DEP)):
    if not f.lower().endswith("_u.txt"): continue
    stem = f[:-6]
    k = idx.get((stem + ".scn").lower())
    if not k: continue
    dd = open(os.path.join(DEP, k), "rb").read(); nu = (len(dd) - S0) // P
    nats = [NAT.get(dd[S0 + i*P + 36], "?") for i in range(nu)]
    k8 = [dd[S0 + i*P + 8] | (dd[S0 + i*P + 9] << 8) for i in range(nu)]
    bk = os.path.join(BK, idx.get(f.lower(), f))
    if not os.path.isfile(bk): continue
    d = rd(os.path.join(DEP, f)); b = rd(bk)
    if len(d) < 2 or len(d) != len(b): continue
    for i in range(min(len(d), len(b))):
        x, y = b[i].strip(), d[i].strip()
        if not x or not y or x == y or CJK.search(x) or not CJK.search(y): continue
        nat = nats[k8[i]] if i < nu and 0 <= k8[i] < nu else (nats[i] if i < nu else "")
        if not nat: continue
        xs = x.split("/"); ys = y.split("/")
        if len(xs) != len(ys) or len(xs) < 1: continue
        for p, seg in enumerate(ys):
            w = word_of(seg)
            if w: stat[(nat, len(xs), p)][w] += 1

NATS = ["德国","苏联","美国","英国","意大利","罗马尼亚","芬兰","法国","波兰","武装党卫军","加拿大","匈牙利"]
for nat in NATS:
    print("\n### {} ###".format(nat))
    for n in sorted({k[1] for k in stat if k[0] == nat}):
        row = []
        for p in range(n):
            c = stat[(nat, n, p)]
            row.append("位%d:%s" % (p, ">".join("%s%d" % kv for kv in c.most_common(3)) if c else "—"))
        print("   {}段  {}".format(n, "  ".join(row)))
# ---- 生成编制阶梯：实测定「最高级(末位)」，再按标准编制逐级下推（禁重复） ----
ASC = ["连","营","团","师","军","集团军","集团军群"]      # 兜底下推用（不含旅）
BASE = {"连":0,"营":1,"团":2,"大队":2,"中队":2,"旅":3,"师":4,"军":5,"集团军":6,"集团军群":7}
def rank(w):
    if not w: return 99
    if w in BASE: return BASE[w]
    for b, r in (("师",4),("军",5),("旅",3),("团",2),("营",1),("连",0)):
        if w.endswith(b) and len(w) > len(b): return r
    return 2

NATIONS = list(NAT.values()) + ["无scn", "未匹配"]
ladder = {}
for nat in NATIONS:
    for n in range(1, 6):
        top = None
        c = stat.get((nat, n, n-1))
        if c:
            w, cnt = c.most_common(1)[0]
            if cnt >= 3 and (n != 1 or w in ("团", "营")): top = w
        if top is None:
            if n == 1:                                  # 单段裸数字：按国别在 团/营 中二选一
                c2 = stat.get((nat, 2, 0))
                w2 = c2.most_common(1)[0][0] if c2 else ""
                if w2 not in ("团", "营"): w2 = "团"
                top = w2
            elif not any(k[0] == nat for k in stat):
                top = "师"                              # 无实测 → 通用锚点「师」
            else:
                continue                                # 有实测但证据不足 → 留裸数字
        words = [""] * n; words[n-1] = top; cur = rank(top)
        for p in range(n-2, -1, -1):
            cc = stat.get((nat, n, p))
            cands = [(w2, k2) for w2, k2 in (cc.items() if cc else []) if rank(w2) < cur and k2 >= 5]
            if cands:
                w2 = max(cands, key=lambda x: x[1])[0]
            else:
                w2 = max([a for a in ASC if rank(a) < cur], key=rank, default="连")
            words[p] = w2; cur = rank(w2)
        ladder[(nat, n)] = words
with io.open(os.path.join(r"d:\DSH\军事游戏汉化\pegww2\research", "_u-position-ladder.tsv"),
             "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# 位次→编制规模 阶梯（实测；单调：位次0最小 → 末位最大）\n国别\t段数\t\t".rstrip() + "\n")
    for (nat, n) in sorted(ladder):
        fh.write("%s\t%d\t%s\n" % (nat, n, "/".join(ladder[(nat, n)])))
print("\n### 单调阶梯（位次0 → 末位）###")
for k in sorted(ladder):
    if k[0] in NATS: print("  {}/{}段: {}".format(k[0], k[1], "/".join(ladder[k])))
print("阶梯条目 %d -> research/_u-position-ladder.tsv" % len(ladder))
