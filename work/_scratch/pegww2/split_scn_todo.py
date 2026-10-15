#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层：把待填条目切成**互不冲突的批次**（供并行翻译，避免同时写一个文件）。

为什么这么切：
  · 命名类（`_m` 地图格名 / `_u` 部队名）**只需纯译**，不需要判文体/视角 ⇒ 可立即并行
  · 散文类（txt/i/bv/v/tv/l/log/tx）**必须先判视角国别与文体** ⇒ 等「战役→视角对照表」出来再排
  · 一个原文可能同时出现在多个类里（如 `Kalatsch (#1)` 同时在 m 与 u）⇒ **只归一个桶**，
    因为 map 是**按串键控**的，一处译好即全处生效，绝不能让两个任务重复翻同一串。

分桶优先级（先判「是不是句子」）：
  像句子（≥5 词 或 含句末标点）  → prose
  否则含 m                      → m
  否则含 u                      → u
  否则                          → prose
产出：`_scn-todo-<bucket>.tsv`（原文 / 译文(空) / 类 / 出现文件数 / 出现次数）
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsv_esc import esc, unesc  # noqa: E402

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-scn-map.tsv")
STAT = os.path.join(RES, "_scn-stats.tsv")
_sink = io.StringIO()


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def is_sentence(s):
    words = s.split()
    return len(words) >= 5 or bool(re.search(r"[.!?]\s*$", s))


def main():
    stats = {}
    with open(STAT, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            f2 = line.rstrip("\r\n").split("\t")
            if len(f2) >= 4:
                stats[unesc(f2[0])] = (f2[1], int(f2[2]), int(f2[3]))

    todo = []
    audit = []                    # 预填样本（供人审）
    with open(MAP, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if not s or s.startswith("#") or s.split("\t")[0].strip() == "原文":
                continue
            f2 = s.split("\t")
            if len(f2) < 3:
                continue
            src, zh, tag = unesc(f2[0]), unesc(f2[1]), f2[2].strip()
            cls, nf, n = stats.get(src, ("?", 0, 0))
            if not zh.strip():
                todo.append((src, cls, nf, n))
            elif tag in ("词库", "PeG"):
                audit.append((src, zh, tag, cls, nf, n))

    buckets = defaultdict(list)
    for src, cls, nf, n in todo:
        classes = set(cls.split("+"))
        sentence = is_sentence(src)
        if sentence:
            b = "prose"
        elif "m 地图格名" in classes:
            b = "m"
        elif "u 部队名" in classes:
            b = "u"
        else:
            b = "prose"
        buckets[b].append((src, cls, nf, n))

    print("=" * 88)
    print("待填分桶（互不重叠，合计 = 全部待填）")
    print("=" * 88)
    tot = 0
    for b in ("m", "u", "prose"):
        rows = buckets[b]
        occ = sum(r[3] for r in rows)
        tot += len(rows)
        out = os.path.join(RES, f"_scn-todo-{b}.tsv")
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# 场景层待填批次: {b}（原文 / 译文(留空待填) / 类 / 出现文件数 / 出现次数）\n")
            f.write("# ⚠️ 只改「译文」列；不得增删行；UTF-8 无 BOM；TAB 分隔；译文内不得含 TAB/换行\n")
            f.write("原文\t译文\t类\t出现文件数\t出现次数\n")
            for src, cls, nf, n in sorted(rows, key=lambda r: -r[3]):
                f.write(f"{esc(src)}\t\t{cls}\t{nf}\t{n}\n")
        print(f"  {b:6s} 唯一串 {len(rows):>6d} · 占出现次数 {occ:>6d} → {os.path.basename(out)}")
    print(f"  合计 {tot}（应 = 待填总数）")

    # 预填审计样本（前 60 条，按出现次数排序，便于发现系统性错配）
    audit.sort(key=lambda r: -r[5])
    out = os.path.join(RES, "_scn-prefill-audit.tsv")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 预填审计样本（词库/前作预填，按出现次数排序）——供人工抽查错配\n")
        f.write("原文\t预填译文\t来源\t类\t出现文件数\t出现次数\n")
        for r in audit[:400]:
            f.write("\t".join(str(x) for x in r) + "\n")
    print(f"  预填审计样本 {min(400, len(audit))}/{len(audit)} 条 → {os.path.basename(out)}")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "scn-buckets.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
