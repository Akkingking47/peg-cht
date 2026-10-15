#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层：**重复译名检查**（抓「复制粘贴错译」）。

原理：两个**不同原文**得到**同一译文**时，多为复制粘贴错误
      （实测抓到的：`Minenräumboot Dantzig` 与 `Minenräumboot Dresden` 都成了「但泽号扫雷艇」）。
⚠️ 但有**合法重复**：音近异名（`Irwin`/`Owen`→欧文）、同义简写（`dummy`/`Dummy`）、
   同一实体的不同拼写（`Beisfjord`/`Beisfjorden`）⇒ 输出里按「译文长度」与「原文相似度」排序，优先看长译名。

用法: python dup_check.py [只列前N组=40]
"""
import os
import re
import sys
from collections import defaultdict

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-scn-map.tsv")


def sim(a, b):
    """相似度：最长公共前缀 + 最长公共后缀，占较长串的比例（对付「只差一个词」的情形）"""
    n = 0
    for x, y in zip(a, b):
        if x.lower() != y.lower():
            break
        n += 1
    m = 0
    for x, y in zip(reversed(a), reversed(b)):
        if x.lower() != y.lower():
            break
        m += 1
    return (n + m) / max(1, max(len(a), len(b)))


def lev(a, b):
    """Levenshtein 距离（小串够用）"""
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def norm_tok(t):
    return re.sub(r"[^0-9A-Za-z]", "", t).lower()


def real_diff(a, b, minlen=4):
    """返回「真正不同」的词对：去掉标点后不同，且编辑距离 > 2（排除拼写噪声/标点差异）"""
    wa = [norm_tok(w) for w in a.split() if len(norm_tok(w)) >= minlen]
    wb = [norm_tok(w) for w in b.split() if len(norm_tok(w)) >= minlen]
    sa, sb = set(wa), set(wb)
    only_a = sorted(sa - sb)
    only_b = sorted(sb - sa)
    out = []
    for x in only_a:
        best, bd = None, 99
        for y in only_b:
            d = lev(x, y)
            if d < bd:
                best, bd = y, d
        if best is None or bd <= 2:      # 只差 1–2 个字母 ⇒ 拼写噪声，放过
            continue
        out.append((x, best, bd))
    return out


def main():
    top = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    by = defaultdict(set)
    with open(MAP, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if not s or s.startswith("#") or s.split("\t")[0].strip() == "原文":
                continue
            f2 = s.split("\t")
            if len(f2) >= 3 and f2[1].strip() and f2[2].strip() != "保留":
                by[f2[1].strip()].add(f2[0])
    groups = [(zh, sorted(srcs)) for zh, srcs in by.items() if len(srcs) > 1]

    print("⭐ 复制粘贴错译高危组（精筛）")
    print("   判据：两条原文几乎相同（相似度 ≥0.65），却共用同一译文；且差异词是**真正不同**的")
    print("         拉丁词（去标点后不同、编辑距离 >2）—— `Dantzig`/`Dresden` 正是此型")
    print("=" * 96)
    hits = []
    for zh, srcs in groups:
        for i in range(len(srcs)):
            for j in range(i + 1, len(srcs)):
                a, b = srcs[i], srcs[j]
                s = sim(a, b)
                if not (0.65 <= s < 1.0):
                    continue
                # ⚠️ 前置过滤：去标点+去空格后完全相同 ⇒ 只是排版变体（如 `1e DLM` vs `1eDLM`）⇒ 放过
                na = re.sub(r"[^0-9a-z]", "", a.lower())
                nb = re.sub(r"[^0-9a-z]", "", b.lower())
                if na == nb:
                    continue
                rd = real_diff(a, b)
                if rd:
                    hits.append((s, zh, a, b, rd))
    hits.sort(key=lambda h: -h[0])
    print(f"  命中 {len(hits)} 组")
    for s, zh, a, b, rd in hits[:top]:
        print(f"\n  相似度 {s:.2f}  「{zh[:46]}」")
        print(f"    A: {a[:90]}")
        print(f"    B: {b[:90]}")
        for x, y, d in rd:
            print(f"       ↳ 差异词: {x!r} vs {y!r}（编辑距离 {d}）")


if __name__ == "__main__":
    main()
