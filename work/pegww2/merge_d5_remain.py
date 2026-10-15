#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS · 把 D5 余量合并表的译法回填进 27 张格表（按**原文精确匹配**）。

用法: python merge_d5_remain.py [--apply]
"""
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
FILL = os.path.join(WS, "pegww2", "docs-zh", "_fill")
REMAIN = os.path.join(FILL, "_task-D5-remain.tsv")


def main():
    apply_ = "--apply" in sys.argv
    tr = {}
    for l in open(REMAIN, encoding="utf-8"):
        if l.startswith("#") or l.startswith("出现次数") or not l.strip():
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) >= 3 and c[2].strip():
            tr[c[1].strip()] = c[2].strip()
    print("余量译法 %d 条" % len(tr))
    tot_fill = 0
    changed_files = 0
    for dp, _, fs in os.walk(FILL):
        for f in fs:
            if not f.endswith(".cells.tsv"):
                continue
            p = os.path.join(dp, f)
            lines = [l.rstrip("\n") for l in open(p, encoding="utf-8")]
            head = [l for l in lines if l.startswith("#") or l.startswith("工作表")]
            out, n = [], 0
            for l in lines:
                if l in head:
                    out.append(l)
                    continue
                c = l.split("\t")
                if len(c) >= 5 and c[3].strip() and not c[4].strip() and c[3].strip() in tr:
                    c[4] = tr[c[3].strip()]
                    n += 1
                out.append("\t".join(c))
            if n:
                changed_files += 1
                tot_fill += n
                if apply_:
                    with open(p, "w", encoding="utf-8", newline="\n") as fh:
                        fh.write("\n".join(out) + "\n")
                print("  %-56s 回填 %3d 格" % (os.path.relpath(p, FILL)[:56], n))
    print()
    print("合计命中 %d 格 / 涉及 %d 个文件%s" % (tot_fill, changed_files,
                                          "" if apply_ else "   ← dry-run（加 --apply 落盘）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
