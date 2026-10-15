# -*- coding: utf-8 -*-
"""诊断：640 个「未判定视角」到底卡在哪 —— 决定「补视角」该往哪使劲。只读。"""
import collections, io, os, re, sys

WS = r"D:\DSH\军事游戏汉化"
sys.path.insert(0, os.path.join(WS, "work", "glossary"))
import faction_place_audit as FPA

data = FPA.load_scenarios()
pin = FPA.load_pin()
side, origin, voice = FPA.resolve_sides(data, pin)
und = [fn for fn in data if fn not in side]
print("总数 %d · 已判定 %d · 未判定 %d" % (len(data), len(side), len(und)))

# ① 未判定的文件名后缀分布（揭示它们是什么类型的文件）
def suf(fn):
    s = os.path.splitext(fn)[0]
    m = re.search(r"(?i)(_i|_m|_u|_l|_bv|_tv|_v)$", s)
    return m.group(1).lower() if m else "(其它)"
print("\n① 未判定文件的后缀分布：")
for k, v in collections.Counter(suf(f) for f in und).most_common():
    print("   %-7s %d" % (k, v))
print("   对照·已判定文件的后缀分布：")
for k, v in collections.Counter(suf(f) for f in side).most_common(6):
    print("   %-7s %d" % (k, v))

# ② 未判定的：同 stem 里有没有已判定的？（→ 二遍传播能救多少）
by_stem_res = collections.defaultdict(list)
for f, s in side.items():
    by_stem_res[FPA.stem_of(f).lower()].append(s)
by_fam_res = collections.defaultdict(collections.Counter)
for f, s in side.items():
    fa = FPA.family_of(f)
    if fa:
        by_fam_res[fa][s] += 1
stem_res = sum(1 for f in und if by_stem_res.get(FPA.stem_of(f).lower()))
fam_ok = 0
for f in und:
    if by_stem_res.get(FPA.stem_of(f).lower()):
        continue
    c = by_fam_res.get(FPA.family_of(f))
    if c and sum(c.values()) >= 3 and c.most_common(1)[0][1] * 10 >= sum(c.values()) * 6:
        fam_ok += 1
print("\n② 二遍传播（用**全部已判定**重建 stem/战役族计数，再跑一遍）能救：")
print("   同 stem 有已判定  → %d 个（%.0f%%）" % (stem_res, 100.0 * stem_res / max(1, len(und))))
print("   战役族够票数      → %d 个（%.0f%%）" % (fam_ok, 100.0 * fam_ok / max(1, len(und))))
print("   合计可补          → %d 个（%.0f%%）" % (stem_res + fam_ok, 100.0 * (stem_res + fam_ok) / max(1, len(und))))

# ③ 未判定的有没有 .scn？@22 值是什么？
idx = {}
for n in os.listdir(FPA.GAME):
    if n.lower().endswith(".scn"):
        idx.setdefault(n.lower(), os.path.join(FPA.GAME, n))
have, vals = 0, collections.Counter()
for f in und:
    stem = FPA.stem_of(f)
    p = None
    for cand in (stem + ".scn", "zz" + stem + ".scn"):
        p = idx.get(cand.lower())
        if p:
            break
    if not p:
        continue
    have += 1
    b = open(p, "rb").read()
    if len(b) > 22:
        vals[b[22]] += 1
print("\n③ 未判定里能找到 .scn 的：%d 个（%.0f%%）" % (have, 100.0 * have / max(1, len(und))))
print("   其 @22 取值分布（已知映射 %s）：" % FPA.SCN_SIDE)
for v, n in vals.most_common(12):
    tag = "已映射→%s" % FPA.SCN_SIDE[v] if v in FPA.SCN_SIDE else "❌未映射"
    print("   @22=%-4d (0x%02x)  %4d 个   %s" % (v, v, n, tag))

# ④ 未判定的样本文件名
print("\n④ 未判定文件名示例（前 20）：")
for f in und[:20]:
    print("   %s" % f)
