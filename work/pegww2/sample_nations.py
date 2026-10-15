#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2：抽取**非德苏视角**补充样本（验证 §二 各国称呼/语域口径）。

判据：按「视角国别」的关键词命中挑文件，并优先取**含称呼或 `our` 归属**的句子。
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
RES = os.path.join(WS, "pegww2", "research")
OUT = os.path.join(RES, "_scn-sample-nations.tsv")
_sink = io.StringIO()

# 国别 -> 用于**判定视角**的特征词（出现在句子/文件里）
TARGETS = [
    ("美", r"(?i)\b(?:American|US |U\.S\.|Third Army|Patton|Eisenhower|GI|Yank)\b"),
    ("英/加", r"(?i)\b(?:British|Montgomery|Eighth Army|8th Army|Commonwealth|Canadian|Tommy)\b"),
    ("意", r"(?i)\b(?:Italian|Regia Marina|Mussolini|Italian army|Bersaglieri|Alpini)\b"),
    ("波", r"(?i)\b(?:Polish|Poland|LWP|Anders|Home Army|Warsaw Uprising)\b"),
    ("希/南", r"(?i)\b(?:Greek|Greece|Partisan|Tito|Chetnik)\b"),
    ("法", r"(?i)\b(?:French|Free French|de Gaulle|FFL|Vichy)\b"),
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


def main():
    d = os.path.join(GAME, "SCENARIO")
    files = [f for f in sorted(os.listdir(d)) if f.lower().endswith((".txt", ".tx", ".t", ".log"))]
    rows = []
    for nat, pat in TARGETS:
        best = None
        for f in files:
            if re.search(r"(?i)(^info\.txt$|read ?me|report)", f):
                continue
            with open(os.path.join(d, f), "rb") as fh:
                txt = fh.read().decode("latin-1")
            # 取同时含「视角特征词」与「称呼/归属词」的长句
            for ln in re.split(r"\r\n|\r|\n", txt):
                s = ln.strip()
                if not (150 <= len(s) <= 620):
                    continue
                if not re.search(pat, s):
                    continue
                if not re.search(r"(?i)\b(?:General|Commander|Sir|our|we|comrade)\b", s):
                    continue
                best = (f, s)
                break
            if best:
                break
        if best:
            rows.append((nat, best[0], best[1]))

    for nat, f, s in rows:
        # 只留首个断句为样本（避免过长）
        print(f"[{nat}视角] {f}")
        print(f"   {s}")
        print()

    if os.path.isfile(OUT):
        print("（注：样本文件已存在，未覆盖）")
    else:
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# 非德苏视角补充样本（latin-1 解码，无损）\n国别\t文件\t原文\n")
            for nat, f, s in rows:
                fh.write(f"{nat}\t{f}\t{s}\n")
        print(f"[out] {os.path.relpath(OUT, WS)}")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "scn-sample-nations.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
