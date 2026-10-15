#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""apply 之后的待译清单重建 + 归一化模糊匹配增益测量

输出：_xscn_todo2.tsv（现状非中文唯一串，未在映射表中，按 freq 降序）
      _norm_hits.tsv （归一化后能命中的条目：src \t 归一键 \t 命中译文 \t 来源）
用法: python rebuild_todo.py
"""
import collections
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DICT = r"D:\DSH\军事游戏汉化\work\xscn\_xscn_dict.tsv"
MAP = os.path.join(HERE, "comww2-xscn-map.tsv")

NORM = lambda x: re.sub(r"\s+", " ", x.strip().rstrip(".").lower())


def rd(path, enc="utf-8-sig", cols=2):
    out = []
    with io.open(path, encoding=enc, newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= cols:
                out.append(c[:cols])
    return out


def main():
    import glob as _g
    snaps = sorted(_g.glob(os.path.join(HERE, "xscn-uniq-after*.tsv")),
                   key=lambda p: os.path.getmtime(p))
    cur_f = snaps[-1] if snaps else os.path.join(HERE, "xscn-uniq.tsv")
    print("用最新快照 %s" % os.path.basename(cur_f))
    cur = rd(cur_f, cols=4)      # src freq groups example
    # ⚠️ 2026-09-29 修：基准不能用整张映射表（否则「规则引擎上一轮的产出」会被当成
    #    已覆盖，导致本轮 todo 只剩它处理不了的，规则引擎输出 0 条 —— 循环依赖）。
    #    正确基准＝**词典覆盖**（`_xscn_covered.tsv`，来自已交付件实证），
    #    归一化/规则引擎/人工批次的产出都属于「本轮生成物」，不算基准。
    used = {k for k, _ in rd(os.path.join(HERE, "_xscn_covered.tsv"))}
    todo = [(c[0], int(c[1])) for c in cur if c[0] not in used]
    todo.sort(key=lambda x: -x[1])
    print("现状非中文唯一串 %d ；词典已覆盖 %d ；**规则引擎作业面 %d**" % (len(cur), len(used), len(todo)))
    cc = sum(len(s) for s, _ in todo)
    print("未覆盖字符数 %d" % cc)

    # freq 分档
    b = collections.Counter()
    for s, f in todo:
        if f >= 8:
            b["freq>=8"] += 1
        elif f >= 5:
            b["freq5-7"] += 1
        elif f >= 3:
            b["freq3-4"] += 1
        elif f == 2:
            b["freq2"] += 1
        else:
            b["freq1"] += 1
    print("freq 分布:", dict(b))

    # 归一化匹配
    dic = collections.defaultdict(list)
    for s, d, n in rd(DICT, cols=3):
        dic[NORM(s)].append((d, int(n)))
    hit, miss = [], []
    for s, f in todo:
        k = NORM(s)
        if k in dic:
            hit.append((s, k, dic[k][0][0], f))
        else:
            miss.append((s, f))
    print("归一化命中 %d 条（%d 字符）" % (len(hit), sum(len(s) for s, _, _, _ in hit)))

    with io.open(os.path.join(HERE, "_xscn_todo3.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("src\tfreq\n")
        for s, fr in todo:
            f.write("%s\t%d\n" % (s, fr))
    with io.open(os.path.join(HERE, "_norm_hits2.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("src\tnormkey\tdst\tfreq\n")
        for s, k, d, fr in hit:
            f.write("%s\t%s\t%s\t%d\n" % (s, k, d, fr))

    print()
    print("=== 未覆盖中 freq>=4 的条目（供批次 2）===")
    for s, f in todo:
        if f >= 4:
            print("   %3d× %s" % (f, s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
