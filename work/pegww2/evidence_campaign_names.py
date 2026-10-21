#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为「名栏疑借用 18 条 + 待判 28 条」逐行拉证据（**只读**，打印到 stdout）。

每行给出：战役 / 场次 / 场景 / 名栏中英 / 说明名中英 / 地图 / 同图场景(中) / 战役前后场 /
          <stem>.TXT 行0 / <stem>_u.txt 行0 / 该名是否别处场景的名（借用指示）。
用法: python evidence_campaign_names.py
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
RES = os.path.join(WS, "pegww2", "research")
SRC = os.path.join(RES, "_战役-名栏与说明不符-20261019.tsv")
LEDGER = os.path.join(RES, "_战役-场景与地图核准.tsv")


def idx(root):
    return {n.lower(): n for n in os.listdir(root) if os.path.isfile(os.path.join(root, n))}


G, B = idx(GAME), idx(BK)


def rd(i, root, name, k=0, enc="gbk"):
    real = i.get(name.lower())
    if not real:
        return ""
    try:
        ls = io.open(os.path.join(root, real), encoding=enc, errors="replace").read().splitlines()
    except Exception:
        return ""
    return ls[k].strip() if len(ls) > k else ""


def maptok(stem):
    real = G.get((stem + ".scn").lower())
    if not real:
        return ""
    b = io.open(os.path.join(GAME, real), "rb").read()
    return ",".join(m.decode("latin1")[:-4].upper() for m in
                    sorted({t for t in re.findall(rb"[ -~]{4,}", b) if t.lower().endswith(b".map")})[:3])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    # 前后场：把 ledger 的 前后场 列(prev→stem→next) 取出
    seqmap = {}
    peers = {}
    for l in io.open(LEDGER, encoding="utf-8"):
        if not l.strip() or l.startswith("#"):
            continue
        c = l.rstrip("\n").split("\t")
        if c[0] == "战役":
            continue
        seqmap[(c[1], c[3])] = c[12]
        peers[(c[1], c[3])] = c[9]

    for l in io.open(SRC, encoding="utf-8"):
        if not l.strip() or l.startswith("#"):
            continue
        c = l.rstrip("\n").split("\t")
        if c[0] == "战役":
            continue
        if c[9] not in ("名栏疑借用·改按说明名", "待判"):
            continue
        camp, cf, idxn, stem, M, I, Iraw, MP = c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]
        seq = seqmap.get((cf, stem), c[12] if len(c) > 12 else "")
        print("### %-16s #%-2s %-15s [%s]" % (cf, idxn, stem, c[9]))
        print("    名栏 : %s" % M)
        print("    说明 : %s   (原文行 %s)" % (I, Iraw))
        print("    英文 : _m=%s | _i=%s | .TXT=%s | _u=%s" % (
            rd(B, BK, stem + "_m.txt", 0, "cp1252"), rd(B, BK, stem + "_i.txt", 0, "cp1252"),
            rd(B, BK, stem + ".TXT", 0, "cp1252"), rd(B, BK, stem + "_u.txt", 0, "cp1252")))
        print("    中文 : .TXT=%s | _u=%s" % (rd(G, GAME, stem + ".TXT"), rd(G, GAME, stem + "_u.txt")))
        print("    地图 : %-12s 同图场景=%s" % (MP, peers.get((cf, stem), "")[:80]))
        print("    序列 : %s" % seq)
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
