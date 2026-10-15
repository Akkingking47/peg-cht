#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查「追击至图卜鲁格｜鲁格」这个场景：它到底该读哪个说明文件，那个文件里是什么。"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
BKS = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
MAP = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")


def fld(b, o, n=20):
    return b[o:o + n].split(b"\x00")[0].decode("latin-1")


# 1) 找出这条列表名的原文
KEY = re.compile(r"追击至图卜鲁格")
key = None
for i, l in enumerate(open(MAP, encoding="utf-8-sig")):
    if i < 4 or not l.strip():
        continue
    f = l.rstrip("\n").split("\t")
    if len(f) >= 3 and KEY.search(f[1]) and ("重制" in f[1] or "Redux" in f[0]):
        print(f"  真源: 原文={f[0]!r}  译文={f[1]!r}")
        key = f[0]
print(f"  用键: {key!r}")

# 2) 哪个 _m.txt / 文件里有这一行
if key:
    for fn in sorted(os.listdir(BKS)):
        b = open(os.path.join(BKS, fn), "rb").read()
        t = b.decode("latin-1")
        if key in t:
            idx = [i for i, x in enumerate(re.split(r"\r\n|\r|\n", t)) if x.strip() == key]
            print(f"  文件 {fn}: 行 {idx}")

# 3) 找该场景的 .scn，读它指向的说明文件内容
print()
print("=== 名字含 pursuit/tobruk/rug 的 .scn ===")
for fn in sorted(os.listdir(os.path.join(G, "SCENARIO"))):
    if fn.lower().endswith(".scn") and re.search(r"(?i)(pursuit|tobruk|rug|rgh)", fn):
        stem = fn[:-4]
        b = open(os.path.join(G, "SCENARIO", fn), "rb").read()
        intro, flag = fld(b, 11329), b[11349]
        print(f"  {fn}: @4={int.from_bytes(b[4:6],'little')} map={fld(b,11210)!r} intro={intro!r} flag={flag}")
        for dd, ff in ((os.path.join(G, "SCENARIO"), ".TXT"), (os.path.join(G, "USERSCEN"), ".ply")):
            for nm in (intro + ff, intro + ff.lower()):
                p = os.path.join(dd, nm)
                if os.path.isfile(p):
                    t = open(p, "rb").read().decode("gbk", "replace")
                    ls = [x for x in re.split(r"\r\n|\r|\n", t) if x.strip()]
                    print(f"     → {os.path.relpath(p, G)} ({os.path.getsize(p)} B, {len(ls)} 非空行)")
                    for x in ls[:5]:
                        print(f"         {x[:66]}")
                    break
