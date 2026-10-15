# -*- coding: utf-8 -*-
"""把「残留未译」拆开看清楚（只读）。

三个来源：
  1) glossary/glossary-authority-review.tsv 的 A未译残留 —— 单条词库条目的译文里还留着英文
  2) glossary/glossary-residual.tsv          —— 词库残留表
  3) pegww2/research/_未译清单.tsv           —— 场景层未命中清单
"""
import csv
import io
import os
import collections

WS = r"D:\DSH\军事游戏汉化"
REV = os.path.join(WS, "glossary", "glossary-authority-review.tsv")
RES = os.path.join(WS, "glossary", "glossary-residual.tsv")
TODO = os.path.join(WS, "pegww2", "research", "_未译清单.tsv")


def rows_of(path, encoding="utf-8-sig"):
    with io.open(path, encoding=encoding, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


print("=" * 70)
print("1) 权威核对 A未译残留")
print("=" * 70)
a = [r for r in rows_of(REV) if r["kind"] == "A未译残留"]
print("合计 %d 条" % len(a))
print("按 scope : %s" % dict(collections.Counter(r["scope"] for r in a)))
print("按 cat   : %s" % dict(collections.Counter(r["cat"] for r in a)))
print("按 note  : %s" % dict(collections.Counter(r["note"] for r in a).most_common(30)))
print()
for r in a[:40]:
    print("   [%-6s %-18s] %-42s => %-30s | 残留=%s" % (
        r["cat"], r["scope"], r["en"][:42], r["zh"][:30], r["note"]))


def peek(path, n=12, label=""):
    print()
    print("=" * 70)
    print("2/3) %s" % label)
    print("=" * 70)
    if not os.path.exists(path):
        print("   （不存在）")
        return
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        lines = f.read().splitlines()
    print("   行数 %d（含表头）· 字节 %d" % (len(lines), os.path.getsize(path)))
    for ln in lines[:n]:
        print("   %s" % ln[:200])


peek(RES, 14, RES)
peek(TODO, 14, TODO)
