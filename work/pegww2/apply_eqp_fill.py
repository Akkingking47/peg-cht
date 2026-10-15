#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2：把 ww2-eqp-fill.tsv（原文串模式的人工确认覆盖）应用到 ww2-eqp-map.tsv。

另做一次**机械规范化**：弯引号 “ ” → 「 」（与全项目体例一致），只动引号字符，不改词。
"""
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-eqp-map.tsv")
FILL = os.path.join(RES, "ww2-eqp-fill.tsv")
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


def main():
    fills = {}
    with open(FILL, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if not s or s.startswith("#") or s.split("\t")[0].strip() == "原文":
                continue
            f2 = s.split("\t")
            if len(f2) >= 2:
                fills[f2[0]] = (f2[1], f2[2] if len(f2) >= 3 else "")
    head, rows = [], []
    with open(MAP, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if s.startswith("#") or s.split("\t")[0].strip() == "原文":
                head.append(s)
            else:
                rows.append(s.split("\t"))

    n_over, n_quote, n_miss = 0, 0, []
    for f2 in rows:
        if len(f2) < 3:
            continue
        # ① 人工覆盖
        if f2[0] in fills:
            old = f2[1]
            f2[1], f2[2] = fills[f2[0]][0], "人工确认"
            if old != f2[1]:
                print(f"  覆盖 {f2[0][:44]:46s} {old[:26]:28s} → {f2[1][:26]}")
                n_over += 1
        # ② 引号规范化（只动 “ ”）—— 注意本表是 3 列：原文/译文/来源
        if "“" in f2[1] or "”" in f2[1]:
            f2[1] = f2[1].replace("“", "「").replace("”", "」")
            if len(f2) > 2:
                f2[2] = (f2[2] + "+引号规范") if f2[2].strip() else "引号规范"
            n_quote += 1
    used = {f2[0] for f2 in rows if len(f2) >= 3}
    for k in fills:
        if k not in used:
            n_miss.append(k)
    with open(MAP, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(head + ["\t".join(x) for x in rows]) + "\n")
    print(f"\n  人工覆盖 {n_over} 行 · 引号规范化 {n_quote} 行 · fill 未命中 {len(n_miss)}")
    for k in n_miss:
        print(f"    ⚠ 未命中（原文串对不上）: {k!r}")


if __name__ == "__main__":
    main()
    with open(os.path.join(RES, "evidence", "eqp-fill.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
