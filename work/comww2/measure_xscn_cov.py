#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""COMWW2 `.xscn` 覆盖率（数据源＝work/xscn/_xscn_dict.tsv 全局词典）

用法: python measure_xscn_cov.py
产出: _xscn_covered.tsv（可直接复用，含来源 efile 数）
      _xscn_todo.tsv（需新译，按 freq 降序）
      _xscn_todo_conflict.txt（词典里有多种译法、需人工裁定的 todo 项）
"""
import collections
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DICT = r"D:\DSH\军事游戏汉化\work\xscn\_xscn_dict.tsv"


WORK = r"D:\DSH\军事游戏汉化\work"
# ⚠️ 2026-09-29 修：原 glob 过宽（`*/*xscn*.tsv`、`*/*map*.tsv`），会把
#    **待译清单**（`efile-nashornpbem\xscn-todo.tsv`，格式 `序号\t原文`）
#    与**唯一串表**（`ao\xscn-uniq.tsv`，格式 `src\tfreq\tgroups\texample`）
#    误读成映射表 ⇒ 产出 `104 → Labinski  Jewish Quarter` 这类**错位译法**，
#    且因优先级高于人工批次而**覆盖正确译法并写入游戏文件**。
#    现改为：只认真正的 xscn 映射表（3 列 src\tdst\note）+ 内容守卫（dst 必含汉字或恒等）。
MAP_GLOBS = ("*/*xscn-map.tsv", "*/*xscn-map*.tsv")
HAN = re.compile(r"[\u4e00-\u9fff]")


def load_maps():
    """既有各 efile 映射表（补齐词典未覆盖的部分；排除 comww2 自己）。
    ⚠️ 三列表必须全列 split 取 c[1]（MECHANICS §19.3）。
    ⚠️ 内容守卫：dst 必须含汉字，或 src==dst（口径保留）——否则拒收并报告。"""
    import glob
    out = {}
    rejected = 0
    for pat in MAP_GLOBS:
        for p in sorted(glob.glob(os.path.join(WORK, pat))):
            base = os.path.basename(p)
            if base.startswith("_") or os.path.dirname(p).lower().endswith("comww2"):
                continue
            try:
                with io.open(p, encoding="utf-8-sig", newline="") as f:
                    rows = f.read().replace("\r\n", "\n").split("\n")
            except Exception:
                continue
            if len(rows) < 50:
                continue
            n = 0
            for i, ln in enumerate(rows):
                if i == 0 or not ln.strip():
                    continue
                c = ln.split("\t")
                if len(c) < 2 or not c[0] or not c[1].strip():
                    continue
                if c[0] in out:
                    continue
                if not HAN.search(c[1]) and c[1].strip() != c[0].strip():
                    rejected += 1                      # 错位/未译 ⇒ 拒收
                    continue
                out[c[0]] = c[1]
                n += 1
            print("   补载 %-44s %6d" % (os.path.relpath(p, WORK), n))
    if rejected:
        print("   ⚠ 内容守卫拒收 %d 条（dst 无汉字且非恒等，疑似错位）" % rejected)
    return out


def main():
    # 词典：src -> [(dst, #efile)]（已按支持数降序）
    dic = collections.defaultdict(list)
    with io.open(DICT, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 3:
                dic[c[0]].append((c[1], int(c[2])))
    print("全局词典 src %d；补载既有映射表：" % len(dic))
    extra = load_maps()
    for k, v in extra.items():
        if k not in dic and v != k:
            dic[k] = [(v, 0)]
    print("合并后 src %d" % len(dic))

    uniq = []
    with io.open(os.path.join(HERE, "xscn-uniq.tsv"), encoding="utf-8", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2:
                uniq.append((c[0], int(c[1]), c[3] if len(c) > 3 else ""))

    covered, todo, conf = [], [], []
    for s, fr, ex in uniq:
        v = dic.get(s)
        if v:
            covered.append((s, v[0][0], fr, v[0][1], ex))
            if len(v) > 1:
                conf.append((s, " | ".join("%s(%d)" % t for t in v)))
        else:
            todo.append((s, fr, ex))

    cc = sum(len(s) for s, _, _, _, _ in covered)
    tc = sum(len(s) for s, _, _ in todo)
    print("COMWW2 .xscn 唯一串 %d" % len(uniq))
    print("  ✅ 词典命中译文 %4d 条 / %6d 字符" % (len(covered), cc))
    print("  ⬜ 需新译       %4d 条 / %6d 字符" % (len(todo), tc))
    print("  复用率 %.1f%%（条）/ %.1f%%（字符）"
          % (100.0 * len(covered) / max(1, len(uniq)),                 100.0 * cc / max(1, cc + tc)))
    print("  其中词典多译法（需裁定）%d 条" % len(conf))

    with io.open(os.path.join(HERE, "_xscn_covered.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\tfreq\tefiles\texample\n")
        for s, d, fr, n, ex in sorted(covered, key=lambda x: -x[2]):
            f.write("%s\t%s\t%d\t%d\t%s\n" % (s, d, fr, n, ex))
    with io.open(os.path.join(HERE, "_xscn_todo.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("src\tfreq\texample\n")
        for s, fr, ex in sorted(todo, key=lambda x: (-x[1], x[0])):
            f.write("%s\t%d\t%s\n" % (s, fr, ex))
    with io.open(os.path.join(HERE, "_xscn_todo_conflict.txt"), "w", encoding="utf-8", newline="") as f:
        for s, v in conf:
            f.write("%s\t%s\n" % (s, v))
    print("已写 _xscn_covered.tsv / _xscn_todo.tsv / _xscn_todo_conflict.txt")

    b = collections.Counter()
    for s, fr, ex in todo:
        if not re.search(r"[A-Za-z]", s):
            b["纯数字/符号"] += 1
        elif len(s) <= 8:
            b["短<=8"] += 1
        elif len(s) <= 30:
            b["中9-30"] += 1
        elif len(s) <= 80:
            b["长31-80"] += 1
        else:
            b["超长>80"] += 1
    print("todo 构成:", dict(b))
    print("  freq>=5 的条目 %d 条（占 todo 实例覆盖的主干）"
          % sum(1 for s, fr, ex in todo if fr >= 5))
    return 0


if __name__ == "__main__":
    sys.exit(main())
