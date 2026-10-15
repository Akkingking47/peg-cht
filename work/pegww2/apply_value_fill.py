#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 通用「值模式」人工覆盖应用器：把 <map>-fill.tsv 覆盖进 <map>.tsv。

用法: python apply_value_fill.py <map文件> <fill文件> [--verbose]
fill 格式：原文\t译文[\t说明]（# 开头为注释）
效果：命中行的译文 → fill 值，来源 → 人工确认；未命中即报出（防静默失配）。
      · 默认**只打印汇总**（大批量时不再淹没会话）
      · 自动把弯引号 “ ” 规范为「 」（全项目体例）
"""
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")


def norm_quotes(s: str) -> str:
    """体例统一：弯引号 → 「」；并去掉**全角括号前的多余半角空格**（中文排版无此空格）。"""
    s = s.replace("“", "「").replace("”", "」")
    for p in ("（", "「", "【"):
        s = s.replace(" " + p, p)
    return s


def main():
    mapn, filln = sys.argv[1], sys.argv[2]
    mp = os.path.join(RES, mapn)
    fp = os.path.join(RES, filln)
    fills = {}
    with open(fp, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if not s or s.startswith("#") or s.split("\t")[0].strip() == "原文":
                continue
            f2 = s.split("\t")
            if len(f2) >= 2:
                fills[f2[0]] = f2[1]
    head, rows = [], []
    with open(mp, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if s.startswith("#") or s.split("\t")[0].strip() == "原文":
                head.append(s)
            else:
                rows.append(s.split("\t"))
    n = n_q = 0
    verbose = "--verbose" in sys.argv
    for f2 in rows:
        if len(f2) >= 2 and f2[0] in fills:
            old = f2[1]
            new = norm_quotes(fills[f2[0]])
            f2[1] = new
            if len(f2) > 2:
                f2[2] = "人工确认"
            if old != new:
                n += 1
                if verbose:
                    print(f"  覆盖 {f2[0][:34]:36s} {old[:16]:18s} → {new}")
    # 顺带把全表遗留弯引号一并规范（统一体例，不动词）
    for f2 in rows:
        if len(f2) >= 2 and ("“" in f2[1] or "”" in f2[1]):
            f2[1] = norm_quotes(f2[1])
            n_q += 1
    used = {f2[0] for f2 in rows}
    miss = [k for k in fills if k not in used]
    with open(mp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(head + ["\t".join(x) for x in rows]) + "\n")
    print(f"  {mapn}: 覆盖 {n} 行 · 引号规范 {n_q} 行 · fill 未命中 {len(miss)}")
    for k in miss[:20]:
        print(f"    ⚠ 未命中: {k!r}")


if __name__ == "__main__":
    main()
