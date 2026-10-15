#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批次 4 候选：残留专有名词的**宽松复用**扫描（仍以既有交付译法为唯一依据）

三档（从严到宽）：
  A 词集等价：与词典某条 src 的**单词多重集相同**（词序/大小写/标点差异）
  B 整词包含：残留串 ⊂ 词典 src（或反之），且边界落在词边界上（如 `River Aure` ↔ `Aure River`）
  C 去括号/前缀：去掉 `[ ]`、`-`、序号前缀后与词典命中

产出：_res_cand.tsv（src \t dst \t 档位 \t 匹配到的词典键）供**人工复核**，不直接入映射表。
用法: python probe_residual_reuse.py
"""
import collections
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DICT = r"D:\DSH\军事游戏汉化\work\xscn\_xscn_dict.tsv"
SNAP = os.path.join(HERE, "xscn-uniq-after3.tsv")

WORD = re.compile(r"[A-Za-z0-9]+")


def words(s):
    return tuple(sorted(w.lower() for w in WORD.findall(s)))


def main():
    dic = collections.defaultdict(list)
    with io.open(DICT, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 3 and c[1].strip():
                dic[c[0]].append((c[1], int(c[2])))
    # 词集索引（仅取"词数>=2"的键，避免单字噪声）
    by_words = collections.defaultdict(list)
    by_token = collections.defaultdict(list)      # 长词倒排索引（B 档用，避免 O(N*M)）
    for k in dic:
        w = words(k)
        if len(w) >= 2:
            by_words[w].append(k)
        for t in set(w):
            if len(t) >= 4:
                by_token[t].append(k)

    mapf = os.path.join(HERE, "comww2-xscn-map.tsv")
    used = set()
    with io.open(mapf, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i and ln.strip():
                used.add(ln.split("\t")[0])

    res = []
    with io.open(SNAP, encoding="utf-8", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if c[0] and c[0] not in used:
                res.append(c[0])
    print("残留 %d 条" % len(res))

    A, B, C, none = [], [], [], []
    for s in res:
        w = words(s)
        hitA = [k for k in by_words.get(w, []) if k != s]
        if hitA:
            k = sorted(hitA, key=lambda x: -len(dic[x]))[0]
            A.append((s, dic[k][0][0], k))
            continue
        # B: 整词包含（双向）
        # 只用"最长 token ≥4"做倒排候选，避免全表比对
        toks = sorted((t for t in WORD.findall(s.lower()) if len(t) >= 4), key=len, reverse=True)
        pool = set()
        for t in toks[:2]:
            pool.update(by_token.get(t, ()))
        cand = []
        for k in pool:
            if k == s or abs(len(k) - len(s)) < 3:
                continue
            if re.search(r"(?<![A-Za-z0-9])" + re.escape(s) + r"(?![A-Za-z0-9])", k) or \
               re.search(r"(?<![A-Za-z0-9])" + re.escape(k) + r"(?![A-Za-z0-9])", s):
                cand.append(k)
        if cand:
            k = sorted(cand, key=lambda x: -len(dic[x]))[0]
            B.append((s, dic[k][0][0], k))
            continue
        # C: 去括号/前缀后再试
        s2 = re.sub(r"^\[|\]$", "", s).strip()
        s2 = re.sub(r"^\d+\s+", "", s2).strip()
        if s2 != s and s2 in dic:
            C.append((s, dic[s2][0][0], s2))
            continue
        if s2 != s and words(s2) in by_words:
            k = sorted(by_words[words(s2)], key=lambda x: -len(dic[x]))[0]
            C.append((s, dic[k][0][0], k))
            continue
        none.append(s)

    print("A 词集等价 %d 条 | B 整词包含 %d 条 | C 去括号/前缀 %d 条 | 无候选 %d 条"
          % (len(A), len(B), len(C), len(none)))
    with io.open(os.path.join(HERE, "_res_cand.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\t档\tmatched_key\n")
        for tag, arr in (("A", A), ("B", B), ("C", C)):
            for s, d, k in arr:
                f.write("%s\t%s\t%s\t%s\n" % (s, d, tag, k))
    print("已写 _res_cand.tsv（供复核，未入映射表）")
    for tag, arr in (("A", A), ("B", B), ("C", C)):
        print()
        print("=== %s 档（前 40）===" % tag)
        for s, d, k in arr[:40]:
            print("   %-34s -> %-20s  [%s]" % (s[:34], d[:20], k[:30]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
