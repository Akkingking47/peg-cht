#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""梳理 · **映射表内未译残留扫描**（在词库/映射表层面找缺陷，而不是等成品投放后）。

三类：
  A. **整行未译**：中文列 == 英文列（或去空白后相等）。
  B. **残留段未译**：按 `/` 拆段后，某些段是纯拉丁而对应英文段是可译内容。
  C. **半译/串味**：中文段里夹 3 个以上连续拉丁字母（专名白名单除外）。

专名白名单（有意保留的原文）：舰名/人名/地名缩写等，按词库 POLICY 与本项目既有裁决。
"""
import io
import os
import re
import sys
from collections import Counter

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
TABLE = sys.argv[sys.argv.index("--table") + 1] if "--table" in sys.argv else "ww2-scn-map"
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None

CJK = re.compile(r"[\u4e00-\u9fff]")
LAT3 = re.compile(r"[A-Za-z]{3,}")
# 有意保留原文的段（POLICY）
KEEP = re.compile(
    r"^\[[IVXL]+\]$"          # 罗马数字军级标记 [XIII]
    r"|^\[?[IVXL]+\.?\]?$"    # 光杆罗马数字
    r"|^[A-Z]{1,2}$"          # 单/双字母标记
    r"|^HMS [A-Z]$"           # 舰名
    r"|^[Dd]ummy$"
    r"|^\d+$"
    r"|^[-–—]+$"
)
# 版本/网址/日期等元数据行
META = re.compile(r"(?i)^(version|gameset|scenario|equipment)\s*:|^loading scen|^map file|"
                  r"^creation ?time|^[a-z]+://|\.(scn|map|txt|eqp)\b|^converted by|^pe?gww2 conversion")


def rows():
    for ln, l in enumerate(io.open(os.path.join(RES, TABLE + ".tsv"), encoding="utf-8-sig"), 1):
        s = l.rstrip("\r\n")
        if not s or s.startswith("#"):
            continue
        c = s.split("\t")
        if len(c) >= 2 and c[0].strip() and c[0].strip() != "原文":
            yield ln, c[0], c[1], (c[2] if len(c) > 2 else "")


def main():
    if OUT:
        sys.stdout = io.open(OUT, "w", encoding="utf-8", newline="\n")
    A, B, C = [], [], []
    for ln, en, zh, src in rows():
        if META.search(en):
            continue
        if en.strip() == zh.strip() and LAT3.search(en):
            A.append((ln, en, zh, src))
            continue
        if "/" in en and "/" in zh:
            es = [x.strip() for x in en.split("/")]
            zs = [x.strip() for x in zh.split("/")]
            if len(es) == len(zs):
                bad = []
                for a, b in zip(es, zs):
                    if not a or not b:
                        continue
                    if KEEP.match(b):
                        continue
                    if LAT3.search(b) and not CJK.search(b):
                        bad.append((a, b))
                if bad:
                    B.append((ln, en, zh, src, bad))
                    continue
        # C：中文里夹拉丁
        if CJK.search(zh):
            for seg in re.split(r"[/\n]", zh):
                seg = seg.strip()
                if KEEP.match(seg) or CJK.search(seg):
                    continue
                if LAT3.search(seg):
                    C.append((ln, en, zh, src, seg))
                    break
    print("=" * 96)
    print("映射表未译残留扫描 · %s" % TABLE)
    print("=" * 96)
    print("\n【A】整行未译 %d 行" % len(A))
    for ln, en, zh, src in A[:200]:
        print("  %-6d %-46s = %s" % (ln, en[:46], zh[:30]))
    print("\n【B】残留段未译 %d 行" % len(B))
    for ln, en, zh, src, bad in B[:200]:
        print("  %-6d %-40s → %-40s  残留：%s" % (ln, en[:40], zh[:40],
              "、".join("%s→%s" % (a[:14], b[:14]) for a, b in bad)))
    print("\n【C】中文夹拉丁 %d 行" % len(C))
    for ln, en, zh, src, seg in C[:200]:
        print("  %-6d %-40s → %-40s  夹：%s" % (ln, en[:40], zh[:40], seg[:24]))
    print("\n合计 A %d · B %d · C %d" % (len(A), len(B), len(C)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
