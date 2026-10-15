# -*- coding: utf-8 -*-
"""对比本次「铺设到 PeG-WW2」前后的词库：glossary/standard-glossary.tsv
   vs backup/post-naming/glossary/standard-glossary.tsv（= 定名后、铺设前的快照）。
只读。输出增/删/改三类，按 (en, scope) 对齐。"""
import io
import os

WS = r"D:\DSH\军事游戏汉化"
NEW = os.path.join(WS, "glossary", "standard-glossary.tsv")
OLD = os.path.join(WS, "backup", "post-naming", "glossary", "standard-glossary.tsv")


def load(p):
    d = {}
    dup = 0
    L = io.open(p, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
    for i, ln in enumerate(L):
        if i == 0 or not ln.strip():
            continue
        c = ln.split("\t")
        k = (c[0], c[3] if len(c) > 3 else "")
        if k in d:
            dup += 1
        d[k] = c
    return d, dup


def main():
    n, dn = load(NEW)
    o, do = load(OLD)
    print("新库 %d 行(重复键 %d) · 旧库 %d 行(重复键 %d)" % (len(n), dn, len(o), do))
    only_new = sorted(set(n) - set(o))
    only_old = sorted(set(o) - set(n))
    print("\n-- 仅新库有 %d --" % len(only_new))
    for k in only_new[:20]:
        print("   + %s | %s" % (k[0][:60], "/".join(n[k][1:4])))
    print("\n-- 仅旧库有 %d --" % len(only_old))
    for k in only_old[:20]:
        print("   - %s | %s" % (k[0][:60], "/".join(o[k][1:4])))
    chg = []
    for k in set(n) & set(o):
        if n[k] != o[k]:
            chg.append(k)
    print("\n-- 同键有差异 %d --" % len(chg))
    for k in sorted(chg):
        a, b = o[k], n[k]
        diff = [i for i in range(max(len(a), len(b)))
                if (a[i] if i < len(a) else None) != (b[i] if i < len(b) else None)]
        print("   %s" % k[0][:70])
        for i in diff:
            print("      col%d: %s -> %s" % (i, a[i] if i < len(a) else "-",
                                             b[i] if i < len(b) else "-"))


if __name__ == "__main__":
    main()
