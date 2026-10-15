# -*- coding: utf-8 -*-
"""只读：词库真源结构盘点。"""
import os, io, collections

WS = r"D:\DSH\军事游戏汉化"
G = os.path.join(WS, "glossary")


def rows(p):
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        t = f.read().replace("\r\n", "\n")
    out, head = [], None
    for ln in t.split("\n"):
        if not ln.strip():
            continue
        c = ln.split("\t")
        if head is None:
            head = c; continue
        out.append({head[k]: (c[k] if k < len(c) else "") for k in range(len(head))})
    return head, out


print("#" * 78)
p = os.path.join(G, "standard-glossary.tsv")
head, r = rows(p)
print("### standard-glossary.tsv  行数 =", len(r))
print("  列：", head)
for col in ("scope", "status", "cat"):
    if col in head:
        c = collections.Counter(x[col] for x in r)
        print(f"  {col}:", dict(c.most_common(24)))
print("  样例 5 行：")
for x in r[:5]:
    print("   ", {k: (v[:30] if v else "") for k, v in x.items()})

print()
print("#" * 78)
print("### glossary/layers/*.tsv")
for fn in sorted(os.listdir(os.path.join(G, "layers"))):
    if not fn.endswith(".tsv"):
        continue
    pp = os.path.join(G, "layers", fn)
    try:
        h, rr = rows(pp)
    except Exception as e:
        print(f"  {fn}: 读取失败 {e}"); continue
    print(f"  {fn}  {len(rr)} 行  列={h}")
    for x in rr[:2]:
        print("      ", [v[:24] for v in x.values()])
