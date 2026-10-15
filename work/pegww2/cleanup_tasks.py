#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS · 安全清理「已完全并入主译表」的分片任务表。

⚠️ **判据必须严格**：只有「该片**每一行都已翻译**」且「译文与主译表逐行相同」才可删。
   曾写错过一版：把「空译文」当成"无需比对即通过" ⇒ 会把**尚未翻译**的分片表判成可删（差点删掉 13 片待译表）。

用法: python cleanup_tasks.py [--apply]
"""
import glob
import os
import sys

FILL = r"D:\DSH\军事游戏汉化\pegww2\docs-zh\_fill"


def main():
    apply_ = "--apply" in sys.argv
    idx = {}
    p = os.path.join(FILL, "_chunks-index.tsv")
    if os.path.isfile(p):
        for l in open(p, encoding="utf-8"):
            if l.startswith("#") or not l.strip():
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 3:
                idx[(c[0], int(c[1]))] = c[2]

    def main_rows(rel):
        m = os.path.join(FILL, rel + ".tsv")
        if not os.path.isfile(m):
            return None
        d = {}
        for l in open(m, encoding="utf-8"):
            if l.startswith("#") or l.split("\t")[0].strip() in ("段号", "行号"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 2 and c[0].strip().isdigit():
                d[c[0].strip()] = (c[1], c[2] if len(c) > 2 else "")
        return d

    dele = []
    for q in sorted(glob.glob(os.path.join(FILL, "_task-*.tsv"))):
        name = os.path.basename(q)[len("_task-"):-len(".tsv")]
        if "-" not in name:
            continue
        tag, part = name.rsplit("-", 1)
        if not part.isdigit():
            continue
        rel = idx.get((tag, int(part)))
        if not rel:
            continue
        main = main_rows(rel)
        if main is None:
            continue
        rows = 0
        ok = True
        for l in open(q, encoding="utf-8"):
            if l.startswith("#") or l.split("\t")[0].strip() in ("段号", "行号"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 2 and c[0].strip().isdigit():
                rows += 1
                zh = (c[2] if len(c) > 2 else "").strip()
                m = main.get(c[0].strip())
                if not zh:                      # ⭐ 本行**未翻译** ⇒ 绝不能删
                    ok = False
                    break
                if not m or m[1] != zh:         # ⭐ 译文必须与主表逐字相同
                    ok = False
                    break
        if rows and ok:
            dele.append(os.path.basename(q))
    print("可安全删除（该片**每行都已译**且与主表逐字相同）%d 个：" % len(dele))
    for d in dele:
        print("   ", d)
        if apply_:
            os.remove(os.path.join(FILL, d))
    print()
    print("（%s）" % ("已删除" if apply_ else "dry-run；加 --apply 执行"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
