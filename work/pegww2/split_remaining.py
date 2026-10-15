#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层：**按「真源里仍未填」的行动态切片**（替代固定切片，自愈不重不漏）。

为什么：固定切片一旦边界位移（历史上因表头归属写错导致），就会出现「片与已填区错位 / 有行永远轮不到」。
本脚本每次从 `ww2-scn-map.tsv` 现算：**译文为空且来源≠保留** 的行 ⇒ 分桶 ⇒ 切片。
⇒ 每轮切出来的片**必然都是未做的工作**；已完成的自然消失。

⚠️ **轮次标签**：片号每轮会重置，若沿用同名会覆盖上一轮的 fill 归档 ⇒ 必须传 tag（如 r2）：
   `_scn-todo-<bucket>-<tag>-NN.tsv` → 对应 `_scn-fill-<bucket>-<tag>-NN.tsv`

用法: python split_remaining.py [每片行数=600] [轮次标签=r1]
"""
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-scn-map.tsv")
STAT = os.path.join(RES, "_scn-stats.tsv")
BUCKETS = ("m", "u", "prose")


def is_sentence(s):
    return len(s.split()) >= 5 or bool(re.search(r"[.!?]\s*$", s))


def main():
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    tag = sys.argv[2] if len(sys.argv) > 2 else "r1"
    stats = {}
    with open(STAT, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            f2 = line.rstrip("\r\n").split("\t")
            if len(f2) >= 4:
                stats[f2[0]] = (f2[1], f2[2], f2[3])

    remain = {b: [] for b in BUCKETS}
    tot = 0
    with open(MAP, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if not s or s.startswith("#") or s.split("\t")[0].strip() == "原文":
                continue
            f2 = s.split("\t")
            if len(f2) < 3 or not f2[0].strip():
                continue
            # ⚠️ 变量名不要用 tag —— 它已被用作「轮次标签」，曾因此把来源列的值（新译）写进文件名
            zh, src_tag = f2[1].strip(), f2[2].strip()
            if zh or src_tag == "保留":
                continue
            # 键是转义形式；桶判定用原文内容即可（不含 TAB 的判定不受转义影响）
            key = f2[0]
            cls, nf, n = stats.get(key, ("", "0", "0"))
            classes = set(cls.split("+"))
            tot += 1
            if is_sentence(key):
                b = "prose"
            elif "m 地图格名" in classes:
                b = "m"
            elif "u 部队名" in classes:
                b = "u"
            else:
                b = "prose"
            remain[b].append((key, cls, nf, n))

    print(f"真源中仍未填: {tot} 行")
    for b in BUCKETS:
        # 清理**本轮**旧片（不动其它轮次的归档）
        for fn in os.listdir(RES):
            if fn.startswith(f"_scn-todo-{b}-{tag}-") and fn.endswith(".tsv"):
                os.remove(os.path.join(RES, fn))
        rows = sorted(remain[b], key=lambda r: -int(r[3]))
        n = 0
        for i in range(0, len(rows), size):
            n += 1
            out = os.path.join(RES, f"_scn-todo-{b}-{tag}-{n:02d}.tsv")
            with open(out, "w", encoding="utf-8", newline="\n") as f:
                f.write(f"# 场景层待填批次: {b}（原文 / 译文(留空待填) / 类 / 出现文件数 / 出现次数）\n")
                f.write("# ⚠️ 只改「译文」列；不得增删行；UTF-8 无 BOM；TAB 分隔；译文内不得含 TAB/换行\n")
                f.write("原文\t译文\t类\t出现文件数\t出现次数\n")
                for key, cls, nf, cnt in rows[i:i + size]:
                    f.write(f"{key}\t\t{cls}\t{nf}\t{cnt}\n")
        print(f"  {b:6s} 未填 {len(rows):>5d} ⇒ 切 {n:>2d} 片")


if __name__ == "__main__":
    main()
