#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层：**表级规范化**（在已并入真源里做批量一致性修正）。

用途：跨片出现「同一表达两种译法」时（如「航空野战军」vs「航空军」），
     不必回头改某一片的 fill —— 直接扫真源、生成覆盖 fill、再并入即可。

用法: python scan_fix.py <包含子串> <替换为> [输出文件= _scn-fill-autofix.tsv]
"""
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-scn-map.tsv")


def main():
    needle, repl = sys.argv[1], sys.argv[2]
    out = os.path.join(RES, sys.argv[3] if len(sys.argv) > 3 else "_scn-fill-autofix.tsv")
    fixed = []
    with open(MAP, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if not s or s.startswith("#") or s.split("\t")[0].strip() == "原文":
                continue
            f2 = s.split("\t")
            if len(f2) >= 3 and needle in f2[1]:
                fixed.append((f2[0], f2[1].replace(needle, repl), f2[2]))
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# 表级规范化：{needle} ⇒ {repl}（scan_fix.py 生成）\n原文\t译文\n")
        for a, b, _ in fixed:
            f.write(f"{a}\t{b}\n")
    print(f"  命中 {len(fixed)} 行 → {os.path.basename(out)}")
    for a, b, tag in fixed[:8]:
        print(f"     {a[:34]:36s} {b[:36]}  [{tag}]")


if __name__ == "__main__":
    main()
