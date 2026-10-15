# -*- coding: utf-8 -*-
"""按战役块统计“尚未被 r00/模板/先例覆盖”的唯一散文行，挑 ROI 最高的块。

用法：
  python extract_block_todo.py            # 仅打印所有块的总览（unique 行数 / 字符数）
  python extract_block_todo.py <block>    # 额外写出 <block>_todo.tsv（src\tblock内出现次数）

复用 translate_prose 的覆盖判定（r00 > prose_dict > precedent），只统计仍未被覆盖的行。
"""
import os
import io
import re
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r"D:\OpenPG2"
SC = os.path.join(GAME, "EFILE_BASEKORP", "SCENARIO")


def load_map(path):
    d = {}
    if not os.path.exists(path):
        return d
    with io.open(path, encoding="utf-8") as f:
        next(f, None)
        for ln in f:
            p = ln.rstrip("\r\n").split("\t")
            if len(p) >= 2:
                d[p[0].rstrip()] = p[1]
    return d


pre = load_map(os.path.join(HERE, "txt-precedent.tsv"))
pd = load_map(os.path.join(HERE, "prose_dict.tsv"))
r00 = collections.defaultdict(dict)
if os.path.exists(os.path.join(HERE, "zh-r00.tsv")):
    with io.open(os.path.join(HERE, "zh-r00.tsv"), encoding="utf-8") as f:
        next(f, None)
        for ln in f:
            p = ln.rstrip("\r\n").split("\t")
            if len(p) >= 3:
                r00[p[0]][p[1].rstrip()] = p[2]

DEC = re.compile(r"^[\s_*=.®¯Â\-]+$")

# rep -> kind
kind = {}
with io.open(os.path.join(HERE, "rep-list.tsv"), encoding="utf-8") as f:
    next(f, None)
    for ln in f:
        p = ln.rstrip("\r\n").split("\t")
        if len(p) >= 4:
            kind[p[1]] = p[3]

# 块定义
blocks = []
with io.open(os.path.join(HERE, "blocks.tsv"), encoding="utf-8") as f:
    next(f, None)
    for ln in f:
        p = ln.rstrip("\r\n").split("\t")
        if len(p) >= 4:
            blocks.append((p[0], int(p[1]), int(p[2]), p[3].split(",")))

summary = []
for blk, nreps, nchars, reps in blocks:
    seen = {}
    tot_u = tot_c = 0
    for rep in reps:
        if kind.get(rep) != "prose":
            continue
        p = os.path.join(SC, rep)
        if not os.path.exists(p):
            continue
        raw = open(p, "rb").read()
        for lb in raw.split(b"\r\n"):
            line = lb.decode("cp1252")
            key = line.rstrip()
            if not key.strip():
                continue
            if DEC.match(key):
                continue
            if rep in r00 and key in r00[rep]:
                continue
            if key in pd:
                continue
            if line in pre:
                continue
            seen[key] = seen.get(key, 0) + 1
    tot_u = len(seen)
    tot_c = sum(len(k) * v for k, v in seen.items())
    summary.append((blk, tot_u, tot_c))

summary.sort(key=lambda x: -x[2])
print("block\tunique_untranslated\tchars")
for blk, u, c in summary:
    print("%s\t%d\t%d" % (blk, u, c))

# 若指定块，写出该块 todo
if len(sys.argv) > 1:
    target = sys.argv[1]
    blk_reps = dict((b[0], b[3]) for b in blocks).get(target)
    if blk_reps is None:
        print("⚠️ 未知块 %s" % target)
        sys.exit(1)
    seen = collections.Counter()
    for rep in blk_reps:
        if kind.get(rep) != "prose":
            continue
        p = os.path.join(SC, rep)
        if not os.path.exists(p):
            continue
        raw = open(p, "rb").read()
        for lb in raw.split(b"\r\n"):
            line = lb.decode("cp1252")
            key = line.rstrip()
            if not key.strip():
                continue
            if DEC.match(key):
                continue
            if rep in r00 and key in r00[rep]:
                continue
            if key in pd:
                continue
            if line in pre:
                continue
            seen[key] += 1
    out = os.path.join(HERE, "%s_todo.tsv" % target)
    with io.open(out, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("src\tn_in_block\r\n")
        for k, v in sorted(seen.items(), key=lambda x: -x[1]):
            f.write("%s\t%d\r\n" % (k, v))
    print("写出 %s (%d 唯一行, %d 字符)" % (out, len(seen), sum(len(k) * v for k, v in seen.items())))
