#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回滚名栏修复的**全部**改动：从历史 fill 文件里恢复这些键的原始译文。

为什么必须回滚：名栏修复用「整串键控」改译文，但同一个串在**别的文件里是正文简报**
（审计发现 36 个键有此情况）⇒ 那些简报正文被改成了场景名。
正解是 **per-file 覆盖**（按「文件+行号」改，而不是按串），另做。

本脚本：对 `_scn-fill-namefix.tsv` 里的每个键，在所有历史 fill 里找到它的原始译文并写回。
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-scn-map.tsv")
NAMEFIX = os.path.join(RES, "_scn-fill-namefix.tsv")
OUT = os.path.join(RES, "_scn-fill-namefix-rollback.tsv")


def main():
    keys = set()
    for i, l in enumerate(open(NAMEFIX, encoding="utf-8")):
        if i < 2 or not l.strip():
            continue
        f = l.rstrip("\n").split("\t")
        if f and f[0].strip():
            keys.add(f[0])
    print(f"需回滚的键: {len(keys)}")
    # 历史 fill：名字里含 -fill- 且不含 namefix
    hist = {}
    files = [f for f in sorted(os.listdir(RES)) if "-fill-" in f and "namefix" not in f and f.endswith(".tsv")]
    for fn in files:
        for i, l in enumerate(open(os.path.join(RES, fn), encoding="utf-8")):
            if i < 1 or not l.strip() or l.startswith("#"):
                continue
            f = l.rstrip("\n").split("\t")
            if len(f) >= 2 and f[0] in keys and f[1].strip():
                hist.setdefault(f[0], f[1])   # 取最早出现的（最早的才是原名栏译文之外的正译本）
    print(f"  在 {len(files)} 个历史 fill 里找到 {len(hist)} 个键的原始译文")
    # 补充来源：术语库（有些键的译文是 `add_value_reuse.py` 从词库直接复用的，不在 fill 里）
    gl = []
    for p in (os.path.join(WS, "glossary", "standard-glossary.tsv"),
              os.path.join(WS, "work", "xscn", "master-glossary.tsv")):
        if os.path.isfile(p):
            gl.append(p)
    n_gl = 0
    for p in gl:
        for i, l in enumerate(open(p, encoding="utf-8", errors="replace")):
            if i == 0 or not l.strip():
                continue
            f = l.rstrip("\n").split("\t")
            if len(f) >= 2 and f[0] in keys and f[1].strip() and f[0] not in hist:
                hist[f[0]] = f[1]
                n_gl += 1
    print(f"  另从 {len(gl)} 个术语库补到 {n_gl} 个")
    missing = keys - set(hist)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 名栏修复回滚：把这些键的译文恢复为原始（简报）译文\n原文\t译文\t说明\n")
        for k, v in hist.items():
            f.write(f"{k}\t{v}\t回滚\n")
    print(f"  → {os.path.relpath(OUT, WS)}")
    if missing:
        print(f"  ⚠️ 未找到原始译文 {len(missing)} 个（需另行处理）:")
        for k in sorted(missing)[:12]:
            print(f"     {k[:66]!r}")


if __name__ == "__main__":
    main()
