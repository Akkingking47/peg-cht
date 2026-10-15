# -*- coding: utf-8 -*-
"""plan_place_cat_fix.py — 出「PLACE 误标」纠正提案表（只读，不改任何文件）。

复用 `work/glossary/cat_fix_rules.py` 的规则（与 `build_glossary.py` 将采用的**同一份**），
保证「提案 = 将来实际落盘」。
"""
import io
import os
import sys
from collections import Counter, defaultdict

W = r"D:\DSH\军事游戏汉化"
GL = os.path.join(W, "glossary")
LIB = os.path.join(GL, "standard-glossary.tsv")
OUT = os.path.join(W, "work", "_sync-audit", "cat-place-fix-proposal.tsv")
sys.path.insert(0, os.path.join(W, "work", "glossary"))
import cat_fix_rules as R  # noqa: E402


def main():
    rows = []
    for i, l in enumerate(io.open(LIB, encoding="utf-8-sig")):
        if i == 0:
            head = l.rstrip("\n").split("\t")
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) < 3:
            continue
        rows.append(c)
    idx = {k: i for i, k in enumerate(head)}
    ip, iz, ic, isc = idx["en"], idx["zh"], idx["cat"], idx["scope"]

    prop = []
    for c in rows:
        if c[ic] != "PLACE":
            continue
        r = R.recat(c[ip], c[iz])
        if r:
            prop.append((c[ip], c[iz], c[isc], r[0], r[1]))

    with io.open(OUT, "w", encoding="utf-8") as fp:
        fp.write("en\tzh\tscope\t原cat\t新cat\t理由\n")
        for p in sorted(prop):
            fp.write("\t".join(p) + "\n")

    place_all = sum(1 for c in rows if c[ic] == "PLACE")
    print("=== PLACE 误标纠正提案 ===")
    print("  库总行 %d · PLACE %d · 建议改判 %d（%.1f%%）"
          % (len(rows), place_all, len(prop), 100.0 * len(prop) / max(place_all, 1)))
    print()
    print("-- 按 scope --")
    for k, v in Counter(p[2] for p in prop).most_common():
        print("   %-18s %d" % (k, v))
    print()
    print("-- 按理由 --")
    for k, v in Counter(p[4] for p in prop).most_common(12):
        print("   %5d  %s" % (v, k))
    print()
    print("-- 抽样（每 scope 6 条）--")
    by = defaultdict(list)
    for p in prop:
        by[p[2]].append(p)
    for sc in sorted(by):
        print("  [%s] %d 条" % (sc, len(by[sc])))
        for p in by[sc][:6]:
            print("     en=%-32s zh=%-22s ← %s" % (p[0][:32], p[1][:22], p[4][:40]))
    print()
    print("-- 未改判的 PLACE 抽样（须确认没漏部队/没误伤地名）--")
    keep = [c for c in rows if c[ic] == "PLACE" and not R.recat(c[ip], c[iz])]
    for c in keep[:12]:
        print("     en=%-34s zh=%-20s scope=%s" % (c[ip][:34], c[iz][:20], c[isc]))
    print("     共 %d 条保持 PLACE" % len(keep))


if __name__ == "__main__":
    main()
