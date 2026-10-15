import pathlib, re

W = pathlib.Path(r"D:\DSH\军事游戏汉化\work")
rows = []
for ln in (W / "xscn" / "openpg-orig.tsv").read_text(encoding="utf-8").splitlines():
    c = ln.split("\t")
    if len(c) >= 5:
        rows.append(c)
uniq = set(r[3] for r in rows)
m = {}
for ln in (W / "xscn-all-map.tsv").read_text(encoding="utf-8").splitlines():
    c = ln.split("\t")
    if len(c) >= 5 and c[3]:
        m.setdefault(c[3], c[4])
pm = {}
for ln in (W / "xscn" / "pgf-lookup.tsv").read_text(encoding="utf-8").splitlines():
    c = ln.split("\t")
    if len(c) >= 2 and c[0]:
        pm.setdefault(c[0], c[1])

reuse = sorted(u for u in uniq if u not in m and u in pm)
print("PGForever 复用条目：", len(reuse))

def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))

# 可疑判据：原文含空格（多词），译文汉字 <= 4 且不含通名后缀
SUF = ["河", "溪", "湖", "湾", "港", "山", "城", "岛", "海", "运河", "机场", "营地", "站", "要塞", "村", "镇", "岭", "峡", "平原", "高地", "角", "桥"]
sus = []
for u in reuse:
    v = pm[u]
    if " " in u and cjk(v) <= 4 and not any(s in v for s in SUF):
        sus.append((u, v))
print("可疑（多词原文只译了首词，共 %d 条）：" % len(sus))
for u, v in sus:
    print("   %-30s -> %s" % (u, v))

print()
print("原文最长的 30 条复用（人工扫一遍）：")
for u in sorted(reuse, key=lambda x: -len(x))[:30]:
    print("   %-32s -> %s" % (u, pm[u]))
