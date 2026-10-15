#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS · 为 RTF/TXT 源的译表生成「分片任务表」（每片 ≤ N 段）。

背景：一次性 400+ 段的子代理曾两度零产出（且根因是它在写辅助脚本）；
      改为**小片 + 明确禁止写脚本 + 分批落盘**后一次通过。
本脚本把 `_fill\<rel>.tsv` 切成 `_fill\_task-<TAG>-NN.tsv`，译完由 `merge_tasks.py` 合回。

用法: python make_chunks.py <TAG> <rel> [每片段数=250]
     python make_chunks.py D2 "Band of Brothers\PeG-WW2 BoB Campaign Install.rtf" 250
"""
import math
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
FILL = os.path.join(WS, "pegww2", "docs-zh", "_fill")


def main():
    tag, rel = sys.argv[1], sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 250
    src = os.path.join(FILL, rel + ".tsv")
    rows = []
    for l in open(src, encoding="utf-8"):
        if l.startswith("#") or l.split("\t")[0].strip() in ("段号", "行号"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) >= 2 and c[0].strip().isdigit():
            rows.append((c[0].strip(), c[1], c[2] if len(c) > 2 else ""))
    # 只切**尚未翻译**的段
    todo = [r for r in rows if not r[2].strip()]
    if not todo:
        print("  %s：已全部译完，无需切片" % rel)
        return 0
    parts = math.ceil(len(todo) / size)
    print("%s：待译 %d 段 → 切 %d 片（每片 ≤%d）" % (rel, len(todo), parts, size))
    made = []
    index_path = os.path.join(FILL, "_chunks-index.tsv")
    idx_rows = []
    if os.path.isfile(index_path):
        idx_rows = [l.rstrip("\n") for l in open(index_path, encoding="utf-8")]
    for i in range(parts):
        seg = todo[i * size:(i + 1) * size]
        p = os.path.join(FILL, "_task-%s-%02d.tsv" % (tag, i + 1))
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("# %s · 第 %d/%d 片（%d 段）——只填第三列\n" % (rel, i + 1, parts, len(seg)))
            f.write("段号\t原文\t译文\n")
            for a, b, _ in seg:
                f.write("%s\t%s\t\n" % (a, b))
        made.append((i + 1, len(seg), seg[0][0], seg[-1][0]))
        idx_rows.append("%s\t%d\t%s" % (tag, i + 1, rel))
    # ⭐ 维护 tag→rel 索引：合并时按 **tag** 找分片，不再依赖任务表首行注释
    #    （曾因子代理改写首行注释、把 PeGWW2 写成 PeG-WW2，导致 `rel in 首行` 匹配失败、35 段没并进去）
    idx_rows = [r for r in dict.fromkeys(idx_rows)]      # 去重保序
    with open(index_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# tag\t片号\trel（由 make_chunks.py 维护，合并时按 tag 定位）\n")
        for r in idx_rows:
            if r.startswith("#"):
                continue
            f.write(r + "\n")
    for n, c, a, b in made:
        print("   _task-%s-%02d.tsv  %3d 段（%s..%s）" % (tag, n, c, a, b))
    return 0


if __name__ == "__main__":
    sys.exit(main())
