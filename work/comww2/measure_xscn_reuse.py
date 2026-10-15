#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""COMWW2 `.xscn` 串表 × 既有各 efile 映射表 —— 测跨 efile 复用率（MECHANICS §16）

用法: python measure_xscn_reuse.py
产出: _xscn_covered.tsv（可直接复用）/ _xscn_todo.tsv（需新译，按 freq 降序）
"""
import glob
import io
import os
import sys

WORK = r"D:\DSH\军事游戏汉化\work"
HERE = os.path.join(WORK, "comww2")


def load_map2(path):
    """两列或三列 src/dst[/note] -> {src: dst}；全列 split 取 c[1]（§19.3 坑）。"""
    m = {}
    base = os.path.basename(path)
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0] and c[1].strip() and c[0] not in m:
                m[c[0]] = c[1]
    return m


def main():
    # 1) COMWW2 唯一串
    uniq = []
    with io.open(os.path.join(HERE, "xscn-uniq.tsv"), encoding="utf-8", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2:
                uniq.append((c[0], int(c[1]), c[3] if len(c) > 3 else ""))

    # 2) 既有映射表（排除 comww2 自己）
    cands = []
    for pat in ("*/*xscn*map*.tsv", "*/*xscn*.tsv", "*/*-map.tsv", "*/*map*.tsv"):
        cands += glob.glob(os.path.join(WORK, pat))
    maps, rows = [], 0
    for p in sorted(set(cands)):
        if os.path.basename(p).startswith("_"):
            continue
        if os.path.dirname(p).lower().endswith("comww2"):
            continue
        try:
            m = load_map2(p)
        except Exception as e:
            print("  跳过 %s (%s)" % (os.path.basename(p), e))
            continue
        if len(m) < 50:
            continue
        maps.append((os.path.relpath(p, WORK), m))
        rows += len(m)
    print("载入 %d 张表，共 %d 条:" % (len(maps), rows))
    for n, m in maps:
        print("   %-46s %6d" % (n, len(m)))

    # 3) 覆盖统计
    union = {}
    src_of = {}
    for n, m in maps:
        for k, v in m.items():
            if k not in union:
                union[k] = v
                src_of[k] = n
    covered, todo = [], []
    for s, fr, ex in uniq:
        if s in union and union[s] != s:          # 有真译文
            covered.append((s, union[s], fr, src_of[s], ex))
        else:
            todo.append((s, fr, ex))

    cov_c = sum(len(s) for s, _, _, _, _ in covered)
    todo_c = sum(len(s) for s, _, _ in todo)
    print()
    print("COMWW2 .xscn 唯一串 %d" % len(uniq))
    print("  ✅ 可复用译文 %4d 条 / %6d 字符" % (len(covered), cov_c))
    print("  ⬜ 需新译     %4d 条 / %6d 字符" % (len(todo), todo_c))
    print("  复用率 %.1f%%（按条）/ %.1f%%（按字符）"
          % (100.0 * len(covered) / max(1, len(uniq)), 100.0 * cov_c / max(1, cov_c + todo_c)))

    with io.open(os.path.join(HERE, "_xscn_covered.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\tfreq\tfrom\texample\n")
        for s, d, fr, n, ex in sorted(covered, key=lambda x: -x[2]):
            f.write("%s\t%s\t%d\t%s\t%s\n" % (s, d, fr, n, ex))
    with io.open(os.path.join(HERE, "_xscn_todo.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("src\tfreq\texample\n")
        for s, fr, ex in sorted(todo, key=lambda x: (-x[1], x[0])):
            f.write("%s\t%d\t%s\n" % (s, fr, ex))
    print("已写 _xscn_covered.tsv / _xscn_todo.tsv")

    # 4) todo 构成
    import collections
    import re
    HAN = re.compile(r"[\u4e00-\u9fff]")
    b = collections.Counter()
    for s, fr, ex in todo:
        L = len(s)
        if not re.search(r"[A-Za-z]", s):
            b["纯数字/符号"] += 1
        elif L <= 8:
            b["短(<=8)"] += 1
        elif L <= 30:
            b["中(9-30)"] += 1
        elif L <= 80:
            b["长(31-80)"] += 1
        else:
            b["超长(>80)"] += 1
    print("todo 构成:", dict(b))
    print("  最高频 30 条:")
    for s, fr, ex in sorted(todo, key=lambda x: -x[1])[:30]:
        print("    %4d× %s" % (fr, s[:90]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
