# -*- coding: utf-8 -*-
"""
阶段 4 · 层 1（.xscn）合并器。

把 work\\gus\\zh\\xscn\\batch-NN.tsv 与原始 work\\gus\\batch\\batch-NN.tsv 对齐，
校验 src 一致、dst 非空，合并成一张 xscn-map.tsv（带表头，供 xscn.py 用）。

纪律（MEMORY.md 硬纪律 15）：
  ① 映射表**第一行必须是表头**（xscn.py 的 load_map 会跳过第 0 行）
  ② 写表时**剔除所有 dst == src 的行**（否则 cmd_apply 会把「保留原文」按 GBK 重写）
  ③ 内容含 cp1250 变音符的 src 保留原文时，走 rawfix 语义（这里只落盘，不写文件）
"""
import os, re, sys, io, collections

W = r"D:\DSH\军事游戏汉化\work\gus"
SRCDIR = os.path.join(W, "batch")           # 原始批次（src freq groups example hint）
ZHDIR = os.path.join(W, "zh", "xscn")       # 译稿
OUT = os.path.join(W, "xscn-map.tsv")
REPORT = os.path.join(W, "_merge_report.txt")

LATIN = re.compile(r"[A-Za-z]")


def read_tsv(path):
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for ln in f.read().splitlines():
            if not ln.strip():
                continue
            cols = ln.rstrip("\r").split("\t")
            # 跳过表头行（原文与译稿都带表头，且译稿表头列数与数据行不一致）
            if cols and cols[0].strip().lower() in ("src", "原文"):
                continue
            rows.append(cols)
    return rows


def main():
    if not os.path.isdir(ZHDIR):
        print("译稿目录不存在:", ZHDIR); return 1

    srcs = sorted(f for f in os.listdir(SRCDIR) if re.match(r"batch-\d+\.tsv$", f))
    zhs = sorted(f for f in os.listdir(ZHDIR) if re.match(r"batch-\d+\.tsv$", f))
    print("原始批次 %d 个 / 译稿 %d 个" % (len(srcs), len(zhs)))

    missing = [f for f in srcs if f not in zhs]
    extra = [f for f in zhs if f not in srcs]

    # 收集所有 src->dst
    trans = {}
    conflict = []
    empty_dst = []
    total_rows = 0
    for sf in srcs:
        rowsin = read_tsv(os.path.join(SRCDIR, sf))
        if sf in zhs:
            rowsout = read_tsv(os.path.join(ZHDIR, sf))
            # 输出的第 1 列是 src，最后一列是 dst
            m = {}
            for r in rowsout:
                if len(r) < 2:
                    continue
                m[r[0].strip()] = r[-1].strip()
        else:
            m = {}
        for r in rowsin:
            total_rows += 1
            s = r[0].strip()
            d = m.get(s, "").strip()
            if not d:
                empty_dst.append((sf, s)); continue
            if s in trans and trans[s] != d and d != s:
                conflict.append((s, trans[s], d))
            trans[s] = d
        if sf in zhs:
            n = sum(1 for r in rowsin if m.get(r[0].strip(), "").strip())
            print("  %s: 输入 %4d / 已译 %4d" % (sf, len(rowsin), n))

    print("\n总行数 %d / 已译唯一串 %d" % (total_rows, len(trans)))
    if missing: print("缺译稿批次: %s" % ", ".join(missing))
    if extra:   print("多余译稿批次: %s" % ", ".join(extra))
    print("空 dst: %d 条" % len(empty_dst))
    print("同串不同译（冲突）: %d 条" % len(conflict))

    # 合表：剔除 dst == src
    keep, dropped = [], 0
    for s, d in sorted(trans.items()):
        if d == s:
            dropped += 1; continue
        keep.append((s, d))
    print("剔除 dst==src（保留原文）: %d 条；实际写入 %d 条" % (dropped, len(keep)))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\n")                       # ← 表头，防止 load_map 吃掉第一条
        for s, d in keep:
            f.write("%s\t%s\n" % (s, d))
    print("已写 ->", OUT)

    with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write("原始批次 %d / 译稿 %d\n" % (len(srcs), len(zhs)))
        f.write("总行数 %d / 已译唯一串 %d\n" % (total_rows, len(trans)))
        f.write("缺译稿批次: %s\n" % ", ".join(missing))
        f.write("空 dst %d 条\n" % len(empty_dst))
        f.write("冲突 %d 条\n" % len(conflict))
        if empty_dst:
            f.write("\n[空 dst 明细]\n")
            for sf, s in empty_dst[:200]: f.write("  %s\t%s\n" % (sf, s))
        if conflict:
            f.write("\n[冲突明细]\n")
            for s, a, b in conflict[:200]: f.write("  %s\t%s\t%s\n" % (s, a, b))
    print("报告 ->", REPORT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
