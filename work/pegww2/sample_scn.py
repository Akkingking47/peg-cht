#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层：抽取**文风验收样本**（覆盖各载体 × 不同视角国别）。

选取原则：
  · 散文类（txt/i/bv/v/l/log/tx）取**长度 180–700 字符**的整行（够长才看得出文风与机翻味）
  · 命名类（_m 地名 / _u 部队名）取短串，兼顾不同国别与含意象的
  · 每个样本来自**不同文件**，尽量分散到不同战役目录前缀
产出：pegww2/research/_scn-sample.tsv（类 / 文件 / 原文）
"""
import io
import os
import re
import sys
from collections import defaultdict

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
RES = os.path.join(WS, "pegww2", "research")
OUT = os.path.join(RES, "_scn-sample.tsv")
EXCLUDE = re.compile(r"(?i)(^info\.txt$|read ?me|report)")
_sink = io.StringIO()

PLAN = [
    ("txt 场景简报", 4, 180, 700),
    ("i 战役内简报", 3, 180, 700),
    ("bv 大胜评述", 2, 150, 900),
    ("log 评述", 1, 60, 400),
    ("tx 评述", 1, 60, 600),
    ("m 地图格名", 6, 4, 40),
    ("u 部队名", 6, 4, 40),
]


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def classify(name):
    n = name.lower()
    for suf, tag in (("_m.txt", "m 地图格名"), ("_u.txt", "u 部队名"), ("_i.txt", "i 战役内简报"),
                     ("_bv.txt", "bv 大胜评述"), ("_tv.txt", "tv 战术胜评述"), ("_l.txt", "l 败报"),
                     ("_v.txt", "v 胜报"), (".log", "log 评述"), (".tx", "tx 评述"),
                     (".t", "t 评述"), (".txt", "txt 场景简报")):
        if n.endswith(suf):
            return tag
    return "其他"


def main():
    d = os.path.join(GAME, "SCENARIO")
    byclass = defaultdict(list)
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        if not os.path.isfile(p) or not re.search(r"(?i)\.(txt|tx|t|log)$", f):
            continue
        if EXCLUDE.search(f):
            continue
        tag = classify(f)
        with open(p, "rb") as fh:
            raw = fh.read()
        for ln in re.split(rb"\r\n|\r|\n", raw):
            s = ln.decode("latin-1").strip()
            if s and re.search(r"[A-Za-z]", s):
                byclass[tag].append((f, s))

    rows = []
    for tag, n, lo, hi in PLAN:
        pool = [(f, s) for f, s in byclass.get(tag, []) if lo <= len(s) <= hi]
        # 去重：同串只留一次；按「文件名」分散
        seen, picked, prefixes = set(), [], set()
        for f, s in pool:
            if s in seen:
                continue
            pre = re.match(r"[A-Za-z0-9]{2,6}", f)
            pre = pre.group(0).lower() if pre else f.lower()
            if pre in prefixes and len(picked) < n:
                continue
            seen.add(s)
            picked.append((f, s))
            prefixes.add(pre)
            if len(picked) >= n:
                break
        if len(picked) < n:
            for f, s in pool:
                if s not in seen:
                    seen.add(s)
                    picked.append((f, s))
                if len(picked) >= n:
                    break
        for f, s in picked:
            rows.append((tag, f, s))

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# 文风验收样本（类 / 文件 / 原文）；文字由 latin-1 解码，展示无损\n")
        fh.write("类\t文件\t原文\n")
        for tag, f, s in rows:
            fh.write(f"{tag}\t{f}\t{s}\n")

    print(f"样本 {len(rows)} 条 → {os.path.relpath(OUT, WS)}")
    print()
    for tag, f, s in rows:
        print(f"[{tag}] {f}")
        print(f"   {s}")
        print()


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "scn-sample.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
