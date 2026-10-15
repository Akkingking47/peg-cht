#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全局 `.xscn` 词典构建器 —— 备份原文 ↔ 已交付件 逐条配对

为什么不用各 efile 的 `*-xscn-map.tsv`：那些表**不完整**。
实测：`EFILE_BASEKORP` 部署件里有「丘陵」，但 `bk-xscn-map.tsv` 查不到该行
⇒ 直接拿备份原文与部署件配对，才是**全量**的 src→dst 记录。

产出：
  `_xscn_dict.tsv`      src \t dst \t efiles \t n   （多译法时每个 dst 一行，按支持 efile 数降序）
  `_xscn_conflicts.tsv` src \t 各译法（只列真冲突），供人工裁定，**不自动择一**
  `_xscn_dict_stat.txt` 统计

用法: python build_dict.py
"""
import collections
import importlib.util
import io
import os
import sys

ROOT = r"D:\OpenPG2"
BACKUP = r"D:\DSH\军事游戏汉化\backup"
HERE = os.path.dirname(os.path.abspath(__file__))
EFS = ["EFILE_AG", "EFILE_AO", "EFILE_ATOMIC", "EFILE_BASEKORP",
       "EFILE_COMWW2", "EFILE_GCE", "EFILE_KAISER",
       "EFILE_NASHORNPBEM", "EFILE_OLGWW2", "EFILE_OPENPG", "EFILE_PzLIGA"]

spec = importlib.util.spec_from_file_location("x", os.path.join(HERE, "xscn.py"))
xm = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(xm)
except SystemExit:
    pass


def items_of(path):
    """[(gi,idx,src)] ；失败返回 None"""
    try:
        data, items, meta = xm.parse(path)
    except Exception:
        return None
    if items is None:
        return None
    out = []
    for gi, idx, off, L in items:
        out.append((gi, idx, xm.decode(xm.raw_at(data, off, L))[1]))
    return out


def main():
    pairs = collections.defaultdict(lambda: collections.Counter())   # src -> Counter(dst -> #efile)
    stat = []
    for ef in EFS:
        bdir = os.path.join(BACKUP, "ORIGINAL-" + ef, "SCENARIO")
        gdir = os.path.join(ROOT, ef, "SCENARIO")
        if not os.path.isdir(bdir):
            stat.append((ef, "无备份", 0, 0, 0, 0))
            continue
        nf = npair = nskip = nsame = 0
        for f in sorted(os.listdir(bdir)):
            if not f.lower().endswith(".xscn"):
                continue
            gp = os.path.join(gdir, f)
            if not os.path.exists(gp):
                nskip += 1
                continue
            a = items_of(os.path.join(bdir, f))
            b = items_of(gp)
            if a is None or b is None or len(a) != len(b):
                nskip += 1
                continue
            nf += 1
            for (ga, ia, sa), (gb, ib, sb) in zip(a, b):
                if ga != gb or ia != ib:
                    continue
                sa, sb = sa.rstrip(), sb.rstrip()
                if not sa:
                    continue
                if sa == sb:
                    nsame += 1
                    continue
                pairs[sa][sb] += 1
                npair += 1
        stat.append((ef, "OK", nf, npair, nsame, nskip))

    print("%-20s %-6s %5s %7s %8s %6s" % ("efile", "状态", "配对文件", "真译文对", "恒等对", "跳过"))
    for s in stat:
        print("%-20s %-6s %5d %7d %8d %6d" % s)

    uniq = len(pairs)
    conflict = {k: v for k, v in pairs.items() if len(v) > 1}
    print()
    print("词典唯一 src %d ；其中**多译法冲突** %d (%.1f%%)"
          % (uniq, len(conflict), 100.0 * len(conflict) / max(1, uniq)))

    with io.open(os.path.join(HERE, "_xscn_dict.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\tefiles\tn\n")
        for s in sorted(pairs):
            for d, n in sorted(pairs[s].items(), key=lambda kv: (-kv[1], kv[0])):
                f.write("%s\t%s\t%d\t%d\n" % (s, d, n, sum(pairs[s].values())))
    with io.open(os.path.join(HERE, "_xscn_conflicts.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("src\tvariants\n")
        for s in sorted(conflict, key=lambda k: (-sum(conflict[k].values()), k)):
            f.write("%s\t%s\n" % (s, " | ".join("%s(%d)" % (d, n)
                                                for d, n in sorted(conflict[s].items(),
                                                                   key=lambda kv: -kv[1]))))
    with io.open(os.path.join(HERE, "_xscn_dict_stat.txt"), "w", encoding="utf-8", newline="") as f:
        f.write("efile\t状态\t配对文件\t真译文对\t恒等对\t跳过\n")
        for s in stat:
            f.write("%s\t%s\t%d\t%d\t%d\t%d\n" % s)
        f.write("唯一src\t%d\n冲突\t%d\n" % (uniq, len(conflict)))
    print("已写 _xscn_dict.tsv / _xscn_conflicts.tsv / _xscn_dict_stat.txt")
    print("冲突样例（前 12）:")
    for s in sorted(conflict, key=lambda k: -sum(conflict[k].values()))[:12]:
        print("   %-28s %s" % (s[:28], " | ".join("%s(%d)" % (d, n)
                                                  for d, n in sorted(conflict[s].items(), key=lambda kv: -kv[1]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
