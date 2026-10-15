# -*- coding: utf-8 -*-
"""量化：修正 `stem_of()` 的「无下划线后缀」漏剥之后，能救回多少未判定视角。只读。"""
import collections, os, re, sys

WS = r"D:\DSH\军事游戏汉化"
sys.path.insert(0, os.path.join(WS, "work", "glossary"))
import faction_place_audit as FPA

OLD = re.compile(r"(?i)(_i|_m|_u|_l|_bv|_tv|_v)$")
NEW = re.compile(r"(?i)(?:_(i|m|u|l|bv|tv|v)$|(?<=[0-9])(i|m|u|l|bv|tv|v)$)")
TAIL = re.compile(r"(?i)(?<=[0-9v])e$")


def stem_new(fn):
    s = OLD.sub("", os.path.splitext(fn)[0])
    s = NEW.sub("", s)
    return TAIL.sub("", s)


data = FPA.load_scenarios()
pin = FPA.load_pin()
side, origin, _v = FPA.resolve_sides(data, pin)
und = [fn for fn in data if fn not in side]

# 修正后 stem 的变化
changed = [f for f in data if stem_new(f).lower() != FPA.stem_of(f).lower()]
print("stem 被修正的文件：%d / %d" % (len(changed), len(data)))
print("示例：")
for f in changed[:8]:
    print("   %-18s  旧 stem=%-14s  新 stem=%s" % (f, FPA.stem_of(f), stem_new(f)))

# 用修正后的 stem 重建「同场景」计数（来源仍只用**已判定**文件，保持不循环）
by_stem = collections.defaultdict(collections.Counter)
for f, s in side.items():
    by_stem[stem_new(f).lower()][s] += 1
by_fam = collections.defaultdict(collections.Counter)
for f, s in side.items():
    fa = FPA.family_of(f)
    if fa:
        by_fam[fa][s] += 1

resc1 = resc2 = 0
dist1, dist2 = collections.Counter(), collections.Counter()
for f in und:
    c = by_stem.get(stem_new(f).lower())
    if c:
        resc1 += 1
        dist1[c.most_common(1)[0][0]] += 1
        continue
    c = by_fam.get(FPA.family_of(f))
    if c and sum(c.values()) >= 3 and c.most_common(1)[0][1] * 10 >= sum(c.values()) * 6:
        resc2 += 1
        dist2[c.most_common(1)[0][0]] += 1
tot = resc1 + resc2
print("\n未判定 %d 个，修正 stem 后："
      "\n   同场景继承可救 %d 个（%.0f%%）%s"
      "\n   战役族可救     %d 个（%.0f%%）%s"
      "\n   合计           %d 个（%.0f%%）⇒ 覆盖率 %.0f%% → %.0f%%"
      % (len(und), resc1, 100.0 * resc1 / max(1, len(und)), dict(dist1),
         resc2, 100.0 * resc2 / max(1, len(und)), dict(dist2),
         tot, 100.0 * tot / max(1, len(und)),
         100.0 * len(side) / len(data), 100.0 * (len(side) + tot) / len(data)))

# 再叠加：修正 stem 后 .scn 查找能多命中多少
idx = {}
for n in os.listdir(FPA.GAME):
    if n.lower().endswith(".scn"):
        idx.setdefault(n.lower(), os.path.join(FPA.GAME, n))
scn_old = sum(1 for f in und if any(idx.get((FPA.stem_of(f) + s).lower()) for s in (".scn",) )
              or idx.get(("zz" + FPA.stem_of(f) + ".scn").lower()))
scn_new = sum(1 for f in und if idx.get((stem_new(f) + ".scn").lower())
              or idx.get(("zz" + stem_new(f) + ".scn").lower()))
print("\n.scn 查找：修正前能命中 %d 个 ⇒ 修正后 %d 个" % (scn_old, scn_new))

# @22 值分布（修正 stem 后可查到的那些）
vals = collections.Counter()
for f in und:
    for cand in (stem_new(f) + ".scn", "zz" + stem_new(f) + ".scn"):
        p = idx.get(cand.lower())
        if p:
            b = open(p, "rb").read()
            if len(b) > 22:
                vals[b[22]] += 1
            break
print("   其 @22 分布（已知映射 %s）：" % FPA.SCN_SIDE)
for v, n in vals.most_common(12):
    print("      @22=%-4d %4d 个  %s" % (v, n, "→%s" % FPA.SCN_SIDE[v] if v in FPA.SCN_SIDE else "❌未映射"))
