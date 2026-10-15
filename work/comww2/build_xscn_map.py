#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""合成 COMWW2 `.xscn` 映射表：词典已覆盖部分 ∪ 人工批次

输入：_xscn_covered.tsv（工作区导出）· xscn-new-N.tsv（人工批次，可多份）
输出：comww2-xscn-map.tsv（两列 src\tdst，供 `xscn.py --efile COMWW2 apply --map`）
校验：空译文 / 含制表符 / GBK 不可编码 / 批次键不在唯一串表中 —— 一律报错中止
"""
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "comww2-xscn-map.tsv")
HAN = re.compile(r"[\u4e00-\u9fff]")


def ok_dst(s, d):
    """译文合法性守卫（2026-09-29 加，堵 `104 → Labinski  Jewish Quarter` 那类错位）。
    合格 = 含汉字（真译文）或 src==dst（口径保留）。
    """
    d = d.strip()
    if not d:
        return False
    if d == s.strip():
        return True
    return bool(HAN.search(d))


def rd2(path, enc="utf-8-sig"):
    rows = []
    with io.open(path, encoding=enc, newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2:
                rows.append((c[0], c[1]))
    return rows


def main():
    # 校验基准：**当前**唯一串表（apply 后的状态才算数；原表见 xscn-uniq.tsv）
    uniq = set()
    for f2 in ("xscn-uniq.tsv", "xscn-uniq-after.tsv"):
        q = os.path.join(HERE, f2)
        if os.path.exists(q):
            uniq |= {k for k, _ in rd2(q)}
    # ⚠️ 优先级：词典（`_xscn_covered`）> 归一化（词典派生）> 人工批次（只填空缺）
    #    理由：词典＝**已交付件实证译法**，属「承上游口径」；人工批次是新增，不得覆盖既有。
    m = {}
    n_rej = 0
    for s, d in rd2(os.path.join(HERE, "_xscn_covered.tsv")):
        if s in m:
            continue
        if not ok_dst(s, d):
            n_rej += 1
            print("  ⚠ 词典档拒收（dst 非译文）%r -> %r" % (s, d))
            continue
        m[s] = d
    n_cov = len(m)
    if n_rej:
        print("  词典档共拒收 %d 条" % n_rej)
    for p in sorted(glob.glob(os.path.join(HERE, "xscn-new-norm.tsv"))):
        for s, d in rd2(p):
            if s not in uniq or not d.strip():
                continue
            if not ok_dst(s, d):
                print("  ⚠ 归一化档拒收（dst 非译文）%r -> %r" % (s, d))
                continue
            if s in m and m[s] != d:
                print("  ~ 归一化与词典不一致（取词典）%r: 词典=%s / 归一=%s" % (s, m[s], d))
            m.setdefault(s, d)
    n_new = 0
    for p in sorted(glob.glob(os.path.join(HERE, "xscn-new-*.tsv"))):
        if os.path.basename(p) == "xscn-new-norm.tsv":
            continue
        bad = 0
        for s, d in rd2(p):
            if s not in uniq:
                print("  !! %s: 键不在唯一串表 -> %r" % (os.path.basename(p), s))
                bad += 1
                continue
            if not ok_dst(s, d) or "\t" in d:
                print("  !! %s: 译文非法 %r -> %r" % (os.path.basename(p), s, d))
                bad += 1
                continue
            try:
                d.encode("gbk")
            except UnicodeEncodeError:
                print("  !! %s: GBK 不可编码 %r -> %r" % (os.path.basename(p), s, d))
                bad += 1
                continue
            if s in m and m[s] != d:
                print("  ~ 人工批次与既有不一致（取既有）%r: 既有=%s / 人工=%s" % (s, m[s], d))
                continue
            if s not in m:
                n_new += 1
            m[s] = d
        print("  批次 %-20s %3d 条%s" % (os.path.basename(p), len(rd2(p)),
                                        "" if not bad else " (错误 %d)" % bad))
        if bad:
            raise SystemExit(1)
    with io.open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\n")
        for s in sorted(m):
            f.write("%s\t%s\n" % (s, m[s]))
    print("映射表 %d 条（词典 %d + 新增 %d）-> %s" % (len(m), n_cov, n_new, os.path.basename(OUT)))

    # 残留：todo 里 freq>=8 但未被覆盖的
    big = []
    for s, fr in rd2(os.path.join(HERE, "_xscn_todo.tsv")):
        if s not in m and int(fr) >= 8:
            big.append((s, int(fr)))
    big.sort(key=lambda x: -x[1])
    print("残留 freq>=8 未覆盖 %d 条:" % len(big))
    for s, fr in big:
        print("     %3d× %s" % (fr, s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
