# -*- coding: utf-8 -*-
"""1) 彻底检查所有分块的「同一原文 → 多译法」；2) 查既有权威译表。"""
import pathlib, collections

ROOT = pathlib.Path(r"D:\OpenPG2")
OUT = pathlib.Path(r"D:\DSH\军事游戏汉化\work\efile-nashornpbem")
O = OUT / "out"

def read_any(p):
    b = p.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("gbk", errors="replace")

TAGS = ("equip-blk1", "equip-blk2", "equip-blk3",
        "names-blk1", "names-blk2", "names-blk3", "ui-blk1", "intro-blk1")

# 权威译表
def load_zh(efile, fname):
    p = ROOT / efile / "TEXT-ZH" / fname
    if not p.exists():
        return {}
    a = (ROOT / efile / fname).read_bytes().decode("gbk", errors="replace").splitlines()
    b = p.read_bytes().decode("gbk", errors="replace").splitlines()
    return {x: y for x, y in zip(a, b) if x != y and y.strip()}

AUTH = {}
for ef in ("EFILE_OLGWW2", "EFILE_OPENPG"):
    for f in ("equip.txt", "names.txt"):
        for k, v in load_zh(ef, f).items():
            AUTH.setdefault(k, v)

occ = collections.defaultdict(list)   # 原文 -> [(tag, lineno, 译文)]
for tag in TAGS:
    src = read_any(OUT / f"{tag}.tsv").splitlines()
    dst = read_any(O / f"{tag}.zh.tsv").splitlines()
    smap = {l.split("\t", 1)[0]: l.split("\t", 1)[1] for l in src if l.strip()}
    for l in dst:
        if l.count("\t") != 1:
            continue
        k, v = l.split("\t", 1)
        if k in smap:
            occ[smap[k]].append((tag, k, v))

print("=" * 78)
print("### 同一原文 → 多译法（全部，含同批内）")
print("=" * 78)
bad = 0
fixlist = []
for orig, lst in sorted(occ.items()):
    vals = {v for _, _, v in lst}
    if len(vals) > 1:
        bad += 1
        auth = AUTH.get(orig)
        print(f"\n  ✗ {orig!r}   权威表: {auth if auth else '（无）'}")
        for t, k, v in lst:
            mark = " ★建议" if auth and v == auth else ""
            print(f"       {t:12s} L{k:>5s} → {v}{mark}")
        fixlist.append((orig, auth, sorted(vals)))

print()
print(f"不一致条目数: {bad}")
print()
print("=" * 78)
print("### 建议统一译法")
print("=" * 78)
for orig, auth, vals in fixlist:
    if auth:
        print(f"  {orig!r} → {auth}   （采用既有权威译表）")
    else:
        print(f"  {orig!r} → 候选: {' / '.join(vals)}   （无权威表，需人工定夺）")
