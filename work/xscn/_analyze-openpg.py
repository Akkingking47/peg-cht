import pathlib
from collections import Counter

W = pathlib.Path(r"D:\DSH\军事游戏汉化\work")

rows = []
for ln in (W / "xscn" / "openpg-orig.tsv").read_text(encoding="utf-8").splitlines():
    c = ln.split("\t")
    if len(c) >= 5:
        rows.append(c)

print("总行数            :", len(rows))
titles = [r for r in rows if r[1] == "-1"]
g0 = [r for r in rows if r[1] == "0"]
g1 = [r for r in rows if r[1] not in ("-1", "0")]
print("  标题            :", len(titles))
print("  组0 (地名/说明) :", len(g0))
print("  组1+ (部队番号) :", len(g1))
print("  文件数          :", len(set(r[0] for r in rows)))

uniq = {}
for r in rows:
    uniq.setdefault(r[3], 0)
    uniq[r[3]] += 1
print("唯一原文          :", len(uniq))

# 复用源 1：OLGWW2 已完成的映射表
m = {}
for ln in (W / "xscn-all-map.tsv").read_text(encoding="utf-8").splitlines():
    c = ln.split("\t")
    if len(c) >= 5 and c[3]:
        m.setdefault(c[3], c[4])
print("OLGWW2 映射原文数 :", len(m))
hit = [u for u in uniq if u in m]
print("  -> 命中可复用   :", len(hit))
print("  -> 未命中       :", len(uniq) - len(hit))

# 复用源 2：PGForever 旧译表
pm = {}
p = W / "xscn" / "pgf-lookup.tsv"
if p.exists():
    for ln in p.read_text(encoding="utf-8").splitlines():
        c = ln.split("\t")
        if len(c) >= 2 and c[0]:
            pm.setdefault(c[0], c[1])
    print("PGForever 表原文数:", len(pm))
    extra = [u for u in uniq if u not in m and u in pm]
    print("  -> 额外补命中   :", len(extra))

miss = [u for u in uniq if u not in m]
print()
print("待译唯一原文      :", len(miss))

# 形态分类：纯 ASCII 类别词 / 含拉丁重音 / 其他
import re
pure_num = [u for u in miss if re.fullmatch(r"[0-9\-/\. ]+", u)]
allcap = [u for u in miss if re.fullmatch(r"[A-Z0-9 \-\./()\[\]]+", u)]
print("  纯数字/符号     :", len(pure_num))
print("  全大写(类别等)  :", len(allcap))
print()
print("待译样例 (前 60 条):")
for u in sorted(miss)[:60]:
    print("   ", u)
