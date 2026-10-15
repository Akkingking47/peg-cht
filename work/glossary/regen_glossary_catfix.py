# -*- coding: utf-8 -*-
"""在临时目录重建 standard-glossary.tsv（含 cat 纠正），与现库逐行比对。

只读：不写 glossary/ 下任何正式文件（把 build_glossary.OUTD 指到临时目录）。

用法:  python regen_glossary_catfix.py
"""
import collections
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = r"D:\DSH\军事游戏汉化"
TMP = os.path.join(WS, "work", "glossary", "_regen-catfix")
CUR = os.path.join(WS, "glossary", "standard-glossary.tsv")

sys.path.insert(0, HERE)
import build_glossary as G  # noqa: E402


def load(p):
    rows = {}
    head = []
    with io.open(p, encoding="utf-8-sig") as f:
        head = f.readline().rstrip("\r\n").split("\t")
        for ln in f:
            c = ln.rstrip("\r\n").split("\t")
            if len(c) < 4:
                continue
            rows[(c[0], c[3])] = c
    return head, rows


def strip_cat(r):
    return [c for i, c in enumerate(r) if i != 2]


def main():
    os.makedirs(TMP, exist_ok=True)
    G.OUTD = TMP
    G.main()

    h_new, new = load(os.path.join(TMP, "standard-glossary.tsv"))
    h_old, old = load(CUR)
    print("\n=== 临时 vs 现库 ===")
    print("表头一致: %s" % (h_new == h_old))
    print("临时 %d 行 · 现库 %d 行" % (len(new), len(old)))

    only_new = sorted(set(new) - set(old))
    only_old = sorted(set(old) - set(new))
    both = sorted(set(new) & set(old))
    diffs = [(k, old[k], new[k]) for k in both if old[k] != new[k]]
    cat_only = [d for d in diffs if strip_cat(d[1]) == strip_cat(d[2])]
    other = [d for d in diffs if strip_cat(d[1]) != strip_cat(d[2])]

    print("仅临时有 %d · 仅现库有 %d · 内容不同 %d（其中**只差 cat 列** %d）"
          % (len(only_new), len(only_old), len(diffs), len(cat_only)))
    print("cat 迁移:")
    for (a, b), n in collections.Counter((o[2], n2[2]) for _, o, n2 in cat_only).most_common(20):
        print("   %-8s → %-8s %5d" % (a, b, n))
    if only_new[:10]:
        print("仅临时有(前 10):")
        for k in only_new[:10]:
            print("   +", k, new[k])
    if only_old[:10]:
        print("仅现库有(前 10):")
        for k in only_old[:10]:
            print("   -", k, old[k])
    if other:
        print("⚠ 非 cat 列的差异 %d 条（前 20）:" % len(other))
        for k, o, n2 in other[:20]:
            print("   ", k)
            print("      旧:", o)
            print("      新:", n2)
    print("\n临时产物: %s" % os.path.join(TMP, "standard-glossary.tsv"))


if __name__ == "__main__":
    main()
