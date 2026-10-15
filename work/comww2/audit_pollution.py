# -*- coding: utf-8 -*-
"""诊断：COMWW2 映射表里的「污染条目」——来自被误读为 map 表的非 map 文件。

判据：条目 (src, dst) 满足任一
  A. dst 含拉丁字母且不含汉字        （正常译法必含汉字，除非官方口径保留）
  B. src 是纯数字 而 dst 不是
  C. src 与 dst 长度比异常（src 短 dst 长 >2.5 倍）
并给出每个条目的来源候选文件与在 COMWW2 原文中的存在性/频次。

用法: python audit_pollution.py [--apply-checklist]
"""
import collections
import glob
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = r"D:\DSH\军事游戏汉化\work"
MAP = os.path.join(HERE, "comww2-xscn-map.tsv")
BACKUP = r"D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_COMWW2\SCENARIO"

HAN = re.compile(r"[\u4e00-\u9fff]")
LAT = re.compile(r"[A-Za-z]")
# 真映射表（3 列 src\tdst\tnote）
REAL_MAPS = {
    "atomic\\atomic-xscn-map.tsv",
    "basekorp\\bk-xscn-map.tsv",
    "efile-nashornpbem\\xscn-map.tsv",
    "glossary\\ag-xscn-map.tsv",
    "xscn-openpg\\openpg-map.tsv",
    "comww2\\comww2-xscn-map.tsv",
}


def read2(p):
    out = []
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2:
                out.append((c[0], c[1]))
    return out


def main():
    # 1) 干净映射表：只取真 map 表 + 词典
    clean = {}
    for rel in sorted(REAL_MAPS):
        if rel.startswith("comww2"):
            continue
        p = os.path.join(WORK, rel)
        if not os.path.exists(p):
            continue
        n = 0
        for a, b in read2(p):
            if a not in clean and b.strip() and not LAT.search(b) or (a not in clean and b.strip() and a == b):
                clean[a] = b
                n += 1
        print("  真 map 表 %-40s %5d" % (rel, n))
    print("干净映射（真 map 表）%d 条" % len(clean))

    # 2) 词典
    dic = {}
    for i, ln in enumerate(io.open(os.path.join(WORK, "xscn", "_xscn_dict.tsv"), encoding="utf-8-sig")):
        if i == 0:
            continue
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= 3 and c[0] not in dic:
            dic[c[0]] = c[1]
    print("词典 %d 条" % len(dic))

    # 3) 逐表统计「提供了哪些、词典型的表提供的是什么」
    print("\n=== 各 glob 命中表『被误读』后贡献的条目特征 ===")
    GLOBS = ("*/*xscn*map*.tsv", "*/*xscn*.tsv", "*/*-map.tsv", "*/*map*.tsv")
    seen = set()
    suspects = collections.defaultdict(list)
    for pat in GLOBS:
        for p in sorted(glob.glob(os.path.join(WORK, pat))):
            rel = os.path.relpath(p, WORK)
            if rel in seen:
                continue
            seen.add(rel)
            if os.path.basename(p).startswith("_") or rel in REAL_MAPS:
                continue
            try:
                rows = read2(p)
            except Exception:
                continue
            if len(rows) < 50:
                continue
            bad = [(a, b) for a, b in rows if a not in dic and a not in clean]
            if bad:
                suspects[rel] = bad[:8]
                print("  ⚠ %-42s 贡献 %d 条（未在词典/真表中）例: %s" % (rel, len(bad), bad[:3]))

    # 4) 当前映射表里的污染条目
    cur = read2(MAP)
    print("\n当前映射表 %d 条" % len(cur))
    pol = []
    for s, d in cur:
        if d == s:
            continue
        if not HAN.search(d):
            pol.append((s, d, "A:dst无汉字"))
        elif re.fullmatch(r"\d+", s.strip()) and not re.fullmatch(r"\d+", d.strip()):
            pol.append((s, d, "B:纯数字src"))
        elif len(s) <= 8 and len(d) > len(s) * 2.5 + 6:
            pol.append((s, d, "C:长度异常"))
    print("污染候选 %d 条" % len(pol))
    for s, d, why in pol:
        print("   %-30s -> %-34s [%s]" % (s[:30], d[:34], why))

    with io.open(os.path.join(HERE, "_pollution_cand.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\twhy\n")
        for s, d, why in pol:
            f.write("%s\t%s\t%s\n" % (s, d, why))


if __name__ == "__main__":
    main()
