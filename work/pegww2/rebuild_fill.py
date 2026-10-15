#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS · 从 `_src` 抽取表**重建**译表（按段号保住已有译文）。

用途：译表被误裁/被写坏时恢复骨架（原文列回到权威来源）。
      踩过：`prune_fills.py` 曾把 `.txt` 源当 RTF 处理 ⇒ 译表被裁到只剩 2 行。

用法: python rebuild_fill.py <rel> [--apply]
"""
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
OUT = os.path.join(WS, "pegww2", "docs-zh")
FILL = os.path.join(OUT, "_fill")
SRC = os.path.join(OUT, "_src")


def main():
    rel = sys.argv[1]
    apply_ = "--apply" in sys.argv
    sp = os.path.join(SRC, rel + ".tsv")
    fp = os.path.join(FILL, rel + ".tsv")
    if not os.path.isfile(sp):
        print("缺 _src：%s" % rel)
        return 1
    # 旧译表的译文（按段号）
    old = {}
    if os.path.isfile(fp):
        for l in open(fp, encoding="utf-8"):
            if l.startswith("#") or l.split("\t")[0].strip() in ("段号", "行号"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 3 and c[0].strip().isdigit():
                old[c[0].strip()] = c[2]
    rows = []
    for l in open(sp, encoding="utf-8"):
        if l.startswith("#") or l.split("\t")[0].strip() in ("段号", "行号"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) >= 2 and c[0].strip().isdigit():
            rows.append((c[0].strip(), c[1]))
    kept = sum(1 for k, _ in rows if old.get(k, "").strip())
    print("  %s：_src %d 行 · 旧译表保回 %d 段译文%s" % (rel[:52], len(rows), kept, "" if apply_ else "  (dry-run)"))
    if apply_:
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8", newline="\n") as f:
            f.write("# %s · 译文填写表：只改第三列（译文），其余别动\n" % rel)
            f.write("行号\t原文\t译文\n")
            for k, t in rows:
                f.write("%s\t%s\t%s\n" % (k, t, old.get(k, "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
