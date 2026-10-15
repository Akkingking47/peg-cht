#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 名栏修复（MOD 数据问题）：找出「场景名栏被填成简报段落」的场景，提取候选名。

背景：66 个 `_m.txt` 的第 0 行是**简报段落**而非场景名（英文原版亦然）。
本作 `_m.txt` 第 0 行 = 场景列表显示名（`.SCN@4==0`）⇒ 列表里显示成长文。
修复方式：在 `ww2-scn-map.tsv` 里把该段的**译文改写成场景名**（生成器按整行取值，无需改文件结构）。

产出：research/_m-namefix.tsv（stem / 段落原文 / 候选名 / 真源已有译文 / 候选名来源）
"""
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
MAP = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")
OUT = os.path.join(WS, "pegww2", "research", "_m-namefix.tsv")


def main():
    mp = {}
    with open(MAP, encoding="utf-8-sig") as f:
        for i, l in enumerate(f):
            if i < 4 or not l.strip():
                continue
            f2 = l.rstrip("\n").split("\t")
            if len(f2) >= 3 and f2[1].strip():
                mp[f2[0]] = f2[1]
    rows = []
    for fn in sorted(os.listdir(BK)):
        if not fn.lower().endswith("_m.txt"):
            continue
        st = fn[:-6]
        t = open(os.path.join(BK, fn), "rb").read().decode("latin-1")
        para = re.split(r"\r\n|\r|\n", t)[0].strip()
        if len(para) <= 120:
            continue
        cand = src = ""
        for suf, tag in ((".TXT", ".TXT"), (".txt", ".txt"), ("_u.txt", "_u")):
            p = os.path.join(BK, st + suf)
            if os.path.isfile(p):
                first = re.split(r"\r\n|\r|\n", open(p, "rb").read().decode("latin-1"))[0].strip()
                if first and len(first) <= 120 and first.lower() != "dummy":
                    cand, src = first, tag
                    break
        rows.append((st, para, cand, mp.get(cand, ""), src))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 名栏修复清单（MOD 数据问题）：_m.txt 第0行是简报段落 ⇒ 译文拟改为场景名\n")
        f.write("stem\t段落原文\t候选名\t真源已有译文\t候选名来源\t我方定名\n")
        for r in rows:
            f.write("\t".join(x.replace("\t", " ") for x in r) + "\t\n")
    print(f"受影响 {len(rows)} 条｜有候选名 {sum(1 for r in rows if r[2])} 条 → {os.path.relpath(OUT, WS)}")
    print("=" * 100)
    print(f"{'stem':18s} {'候选名(MOD原文)':40s} {'真源已有':14s} 源")
    print("=" * 100)
    for st, para, cand, zh, src in rows:
        print(f"{st:18s} {cand[:40]:42s} {zh[:14]:16s} {src}")
    print()
    print("—— 无候选名（需人工定名）——")
    for st, para, cand, zh, src in rows:
        if not cand:
            print(f"  {st:18s} 段落开头: {para[:70]}")


if __name__ == "__main__":
    main()
