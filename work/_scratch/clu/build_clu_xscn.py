# -*- coding: utf-8 -*-
r"""EFILE_Clu `.xscn` 映射表构建器：联合表 ＋ 子代理产物 ＋ 标题 ＋ 复核订正 → 严校验 → 两表。

输入:
  work\xscn\residual-clu-union.tsv     联合残槽（src freq efiles cand source）
  work\xscn\residual-chunks-clu-\chunk-NN.tsv   子代理输入（单列）
  work\xscn\residual-zh-clu\part-NN.tsv         子代理输出（src<TAB>dst）
  work\clu\clu-titles-zh.tsv           标题（src dst）
  work\clu\clu-xscn-overrides.tsv      本会话复核订正（src dst reason）

输出:
  work\clu\clu-xscn-map.tsv    **只含真改动**（rawfix --map 用）：src dst kind
  work\clu\clu-xscn-keep.tsv   口径保留（src==dst，不进 rawfix，供 .txt 层 keepset）
退出码非 0 = 校验未过，禁止落盘。
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
WX = r"D:\DSH\军事游戏汉化\work\xscn"
CHUNKS = os.path.join(WX, "residual-chunks-clu-")
PARTS = os.path.join(WX, "residual-zh-clu")

LATRUN = re.compile(r"[A-Za-z]+")
STRUCT = re.compile(r"[/\[\]()（）]")
# 结构符号数允许不一致的条目（显式登记理由）
STRUCT_EXC = {}


def rd_lines(p):
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        return f.read().replace("\r\n", "\n").split("\n")


def rd2(p):
    d = {}
    for i, ln in enumerate(rd_lines(p)):
        if i == 0 or not ln.strip():
            continue
        c = ln.split("\t")
        if len(c) >= 2:
            d[c[0]] = c[1]
    return d


def main():
    errs = []
    union = {}
    for i, ln in enumerate(rd_lines(os.path.join(WX, "residual-clu-union.tsv"))):
        if i == 0 or not ln.strip():
            continue
        c = ln.split("\t")
        union[c[0]] = c[3]                       # src -> 既有译法（可为空）
    dst = {k: v for k, v in union.items() if v}

    titles = rd2(os.path.join(HERE, "clu-titles-zh.tsv"))
    for k, v in titles.items():
        if k in dst and dst[k] != v:
            errs.append("标题与残槽表冲突 %r: %r vs %r" % (k, dst[k], v))
        dst[k] = v

    parts = sorted(f for f in os.listdir(PARTS) if f.startswith("part-") and f.endswith(".tsv"))
    for pf in parts:
        cf = os.path.join(CHUNKS, pf.replace("part-", "chunk-"))
        if not os.path.exists(cf):
            errs.append("%s 无对应 chunk" % pf)
            continue
        src_lines = [l for l in rd_lines(cf)]
        if src_lines and src_lines[-1] == "":
            src_lines.pop()
        out_lines = rd_lines(os.path.join(PARTS, pf))
        if out_lines and out_lines[-1] == "":
            out_lines.pop()
        if len(out_lines) != len(src_lines):
            errs.append("%s 行数 %d != 输入 %d" % (pf, len(out_lines), len(src_lines)))
            continue
        for n, (a, b) in enumerate(zip(src_lines, out_lines), 1):
            c = b.split("\t")
            if len(c) != 2:
                errs.append("%s:%d 不是恰好 1 个 TAB" % (pf, n))
                continue
            if c[0] != a:
                errs.append("%s:%d 原文列不符 %r != %r" % (pf, n, c[0][:40], a[:40]))
                continue
            if not c[1].strip():
                errs.append("%s:%d 译文为空 %r" % (pf, n, a[:40]))
                continue
            if a in dst and dst[a] != c[1]:
                errs.append("%s:%d 冲突 %r: %r vs %r" % (pf, n, a[:40], dst[a], c[1]))
                continue
            dst[a] = c[1]

    # 复核订正（覆盖子代理）
    ovp = os.path.join(HERE, "clu-xscn-overrides.tsv")
    if os.path.exists(ovp):
        for i, ln in enumerate(rd_lines(ovp)):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0] in dst and dst[c[0]] != c[1]:
                print("   · 复核订正：%r: %r -> %r（%s）"
                      % (c[0], dst[c[0]], c[1], c[2] if len(c) > 2 else ""))
                dst[c[0]] = c[1]

    missing = [k for k in union if k not in dst]
    if missing:
        errs.append("以下 %d 条仍无译文（前 20）：%s" % (len(missing), " | ".join(missing[:20])))
    kept, drop = [], set()
    for k, v in list(dst.items()):
        if v != v.strip():
            errs.append("译文有首尾空格: %r" % k)
            continue
        if v == k:
            kept.append(k)
            drop.add(k)
            continue
        bad = [t for t in LATRUN.findall(v) if t not in k]
        if bad:
            errs.append("译文含 src 之外的新拉丁 %s: %r -> %r" % (bad, k, v))
            continue
        try:
            v.encode("gbk")
        except UnicodeEncodeError:
            errs.append("译文 GBK 装不下: %r -> %r" % (k, v))
            continue
        if k not in STRUCT_EXC and len(STRUCT.findall(k)) != len(STRUCT.findall(v)):
            errs.append("结构符号数不符: %r(%d) -> %r(%d)"
                        % (k, len(STRUCT.findall(k)), v, len(STRUCT.findall(v))))
    if kept:
        print("   · 口径保留（src==dst，不进映射表）：%d 条 %s" % (len(kept), kept[:12]))
    for k in drop:
        dst.pop(k, None)

    if errs:
        print("!! 校验未过，共 %d 条问题：" % len(errs))
        for e in errs[:50]:
            print("   " + e)
        return 1

    mp = os.path.join(HERE, "clu-xscn-map.tsv")
    with io.open(mp, "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\tkind\n")
        for k in sorted(dst):
            f.write("%s\t%s\t%s\n" % (k, dst[k], "TITLE" if k in titles else "slot"))
    kp = os.path.join(HERE, "clu-xscn-keep.tsv")
    with io.open(kp, "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\n")
        for k in sorted(kept):
            f.write("%s\t%s\n" % (k, k))
    print("已写 %s（%d 条真改动，含标题 %d）" % (mp, len(dst), len(titles)))
    print("已写 %s（%d 条口径保留）" % (kp, len(kept)))
    print("联合残槽 %d 条全部覆盖 ✓" % len(union))
    return 0


if __name__ == "__main__":
    sys.exit(main())
