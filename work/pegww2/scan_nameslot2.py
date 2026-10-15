#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""名栏修复：为**无候选名**的场景，从 `.scn@11210`（地图名）/ 地图文件取定名依据。

产出：research/_m-namefix2.tsv（stem / 段落 / 地图名 / 地图名在真源的译文）
"""
import os
import re
import struct

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
SCN = os.path.join(GAME, "SCENARIO")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
MAP = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")
OUT = os.path.join(WS, "pegww2", "research", "_m-namefix2.tsv")


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
        para = re.split(r"\r\n|\r|\n", open(os.path.join(BK, fn), "rb").read().decode("latin-1"))[0].strip()
        if len(para) <= 120:
            continue
        # 有无候选名
        cand = ""
        for suf in (".TXT", ".txt", "_u.txt"):
            p = os.path.join(BK, st + suf)
            if os.path.isfile(p):
                first = re.split(r"\r\n|\r|\n", open(p, "rb").read().decode("latin-1"))[0].strip()
                if first and len(first) <= 120 and first.lower() != "dummy":
                    cand = first
                    break
        if cand:
            continue
        # 取地图名
        mapname = ""
        for cand_scn in (st + ".scn", st.lower() + ".scn", st + ".SCN"):
            p = os.path.join(SCN, cand_scn)
            if os.path.isfile(p):
                b = open(p, "rb").read()
                if len(b) > 11230:
                    mapname = b[11210:11230].split(b"\x00")[0].decode("latin-1")
                break
        rows.append((st, para, mapname, mp.get(mapname, ""), mp.get(os.path.splitext(mapname)[0], "")))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 无候选名场景：以地图名作定名依据\n")
        f.write("stem\t段落原文\t地图名\t地图名真源译文\t地图短名译文\n")
        for r in rows:
            f.write("\t".join(x.replace("\t", " ") for x in r) + "\n")
    print(f"无候选名场景 {len(rows)} 条 → {os.path.relpath(OUT, WS)}")
    for st, para, mn, zh, zh2 in rows:
        print(f"  {st:16s} 地图={mn:16s} 真源={zh or zh2 or '(无)':12s} 段落: {para[:52]}")


if __name__ == "__main__":
    main()
