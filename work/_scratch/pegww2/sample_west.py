#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2：按**称呼形式**（三查法的第一查）抽取补充样本 —— 修正版。

修正原因：上一版按「提到哪个国家」挑 ⇒ 挑出的仍是德军视角句子（口径 §一 明确警告「提到≠视角」）。
正确判据：**说话人怎么称呼上级** ——
  `Herr …`       ⇒ 德语系视角
  `Comrade …`    ⇒ 苏/共体系视角
  仅 `General/Sir/Commander` 且**无** Herr/Comrade ⇒ 西方（美/英/加等）视角
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
RES = os.path.join(WS, "pegww2", "research")
OUT = os.path.join(RES, "_scn-sample-west.tsv")
_sink = io.StringIO()


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

BUCKETS = [
    ("西方(无敬语)", lambda s: (not re.search(r"(?i)\b(?:Herr|Comrade)\b", s))
     and bool(re.search(r"(?i)\b(?:General|Sir|Commander)\b", s))),
    ("苏/共", lambda s: bool(re.search(r"(?i)\bComrade\b", s))),
    ("德语系", lambda s: bool(re.search(r"(?i)\bHerr\b", s))),
]


def main():
    d = os.path.join(GAME, "SCENARIO")
    files = [f for f in sorted(os.listdir(d))
             if f.lower().endswith((".txt", ".tx", ".t", ".log"))
             and not re.search(r"(?i)(^info\.txt$|read ?me|report)", f)]
    picked = {name: [] for name, _ in BUCKETS}
    for f in files:
        with open(os.path.join(d, f), "rb") as fh:
            txt = fh.read().decode("latin-1")
        for ln in re.split(r"\r\n|\r|\n", txt):
            s = ln.strip()
            if not (120 <= len(s) <= 560):
                continue
            if re.match(r"(?i)^(version|gameset|equipment|note|source|btw)\b", s):
                continue
            for name, pred in BUCKETS:
                if len(picked[name]) < 4 and pred(s) and s not in [x[1] for x in picked[name]]:
                    picked[name].append((f, s))
    for name, _ in BUCKETS:
        print("=" * 92)
        print(f"【{name}】")
        print("=" * 92)
        for f, s in picked[name]:
            print(f"[{f}]")
            print(f"   {s}")
            print()
    if not os.path.isfile(OUT):
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# 按称呼形式分桶的补充样本（latin-1 解码）\n桶\t文件\t原文\n")
            for name, _ in BUCKETS:
                for f, s in picked[name]:
                    fh.write(f"{name}\t{f}\t{s}\n")
        print(f"[out] {os.path.relpath(OUT, WS)}")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "scn-sample-west.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
