#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS · 同步 `_src` 抽取表，使其行集 == `_fill` 译表行集。

背景：`_src` 由「抽取」写出、`_fill` 只在首次创建；若中途改过**可译判定**（如新增 `{\\*…}` 屏蔽），
      两者行数会不一致，审计时数字对不上（实测 `_src` 316 行 vs `_fill` 310 行）。
本脚本以 `_fill` 为准重写 `_src`（保护串按当前规则重算），使两侧严格一致。

用法: python resync_src.py [--apply]
"""
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
FILL = os.path.join(WS, "pegww2", "docs-zh", "_fill")
SRC = os.path.join(WS, "pegww2", "docs-zh", "_src")
sys.path.insert(0, os.path.join(WS, "work", "pegww2"))
import doc_rtf as R          # noqa: E402


def main():
    apply_ = "--apply" in sys.argv
    n_fix = 0
    for dp, _, fs in os.walk(FILL):
        for f in fs:
            if f.startswith("_") or not f.endswith(".tsv") or f.endswith(".cells.tsv"):
                continue
            rel = os.path.relpath(os.path.join(dp, f), FILL)[:-4]
            if not rel.endswith(".rtf"):
                continue
            fill = os.path.join(dp, f)
            ids = []
            for l in open(fill, encoding="utf-8"):
                if l.startswith("#") or l.split("\t")[0].strip() in ("段号", "行号"):
                    continue
                c = l.split("\t")
                if c[0].strip().isdigit():
                    ids.append(int(c[0]))
            src = os.path.join(SRC, rel + ".tsv")
            if not os.path.isfile(src):
                continue
            # 读旧 _src 的 protected 列（若有）
            old = {}
            for l in open(src, encoding="utf-8"):
                if l.startswith("#") or l.split("\t")[0].strip() in ("段号", "行号"):
                    continue
                c = l.rstrip("\n").split("\t")
                if len(c) >= 3 and c[0].strip().isdigit():
                    old[int(c[0])] = c
            n_old = len(old)
            if n_old == len(ids):
                continue
            # 从原文重算文本与 protected
            stage = os.path.join(WS, "pegww2", "docs-zh", "_staging", rel)
            p = stage if os.path.isfile(stage) else os.path.join(R.DOCS, rel)
            chunks = R.parse(open(p, "rb").read())
            rows = []
            for i in ids:
                t2 = re.sub(r" {2,}", " ", re.sub(r"[\r\n\t]+", " ", chunks[i][1]).strip())
                pr, saved = R.protect(t2)
                rows.append((i, t2, pr, saved))
            print("  %-56s _src %d → %d 行%s" % (rel[:56], n_old, len(rows), "" if apply_ else "  (dry-run)"))
            if apply_:
                import json
                with open(src, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write("# %s · RTF 抽取（段号 \\t 原文 \\t protected）\\n" % rel)
                    fh.write("段号\t原文\tprotected\n")
                    for i, t2, pr, saved in rows:
                        fh.write("%d\t%s\t%s\n" % (i, t2.replace("\t", "\\t"), pr.replace("\t", "\\t")))
            n_fix += 1
    print()
    print("需同步 %d 份%s" % (n_fix, "" if apply_ else "（加 --apply 落盘）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
