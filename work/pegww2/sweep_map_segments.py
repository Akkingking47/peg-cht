#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""梳理 · **段级一致性扫描**：同一段英文在映射表里是否被译成两种以上中文。

为什么需要它：`ww2-scn-map.tsv` 是**整行键控**的（`1 B/Habforce/Arab Legion` → 整行译文），
所以「同一个番号元素」在不同行里由不同人/不同批次译出时，**整行键不同 ⇒ 词库门看不见**，
只有把行按 `/` 拆成段、按**段位对齐**统计，才能发现「同词异译」。

实测已抓到（本作场景层）：
  · `Imperiali D` → 因佩里亚利师（3 G / 15 B 行） vs **帝国师**（6 R 行）
  · `Raemcke Bde.` → 第拉姆克旅 vs **雷姆克旅**
  · `Saharian Grouping` → 撒哈拉战斗群 vs **撒哈拉集群**
  · `1 African D` → 第1南非师 vs **第1非洲师**（后者错：South African = 南非）
  · `185 Folgore` → 第185“闪电”师 vs **第185福尔戈雷**

用法: python sweep_map_segments.py [--min 2] [--table ww2-scn-map] [--write]
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
EV = os.path.join(RES, "evidence")
# 纯符号/编号段：多值无意义，单列出来避免刷屏
SKIP_SEG = re.compile(r"^\[?[0-9A-Za-z]{0,3}\]?$|^[-–—/]+$|^\[[IVXL]+\]$")


def load(name):
    p = os.path.join(RES, name + ".tsv")
    if not os.path.isfile(p):
        return []
    rows = []
    for ln, l in enumerate(io.open(p, encoding="utf-8-sig"), 1):
        s = l.rstrip("\r\n")
        if not s or s.startswith("#"):
            continue
        c = s.split("\t")
        if len(c) >= 2 and c[0].strip() and c[0].strip() != "原文":
            rows.append((ln, c[0], c[1], c[2] if len(c) > 2 else ""))
    return rows


def load_exc():
    """读段级裁定表的「排除」列：该段在这些 en 行里**有意**不作统一（如 `VIII` 在
    含 `8th Division` 的行里指师序号而非集团军）⇒ 不计入真冲突。"""
    p = os.path.join(WS, "glossary", "layers", "seg-canon.tsv")
    d = {}
    if not os.path.isfile(p):
        return d
    for l in io.open(p, encoding="utf-8"):
        s = l.rstrip("\r\n")
        if not s or s.startswith("#"):
            continue
        c = s.split("\t")
        if len(c) > 5 and c[5].strip():
            d[c[0].strip()] = c[5].strip()
    return d


def main():
    min_ = 2
    only_real = "--only-real" in sys.argv
    global EXC
    EXC = load_exc()
    if "--out" in sys.argv:
        fp = sys.argv[sys.argv.index("--out") + 1]
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        sys.stdout = io.open(fp, "w", encoding="utf-8", newline="\n")
    if "--min" in sys.argv:
        min_ = int(sys.argv[sys.argv.index("--min") + 1])
    tables = [sys.argv[sys.argv.index("--table") + 1]] if "--table" in sys.argv \
        else ["ww2-scn-map", "ww2-eqp-map", "WW2NAME-map", "WW2Misc-map", "WW2Gui-map", "WW2Tips-map"]

    print("=" * 96)
    print("段级一致性扫描（同一段英文 → 多种中文）")
    print("=" * 96)
    for t in tables:
        rows = load(t)
        if not rows:
            continue
        seg = defaultdict(Counter)          # en_seg → Counter(zh_seg)
        srcs = defaultdict(Counter)         # (en_seg, zh_seg) → Counter(src)
        cpd = defaultdict(Counter)          # (en_seg, zh_seg) → Counter(是否复合尾段)
        excn = defaultdict(Counter)         # (en_seg, zh_seg) → Counter(是否命中裁定表排除)
        ex = defaultdict(list)              # (en_seg, zh_seg) → [整行…]
        nseg = naline = 0
        for ln, en, zh, src in rows:
            if "/" not in en or "/" not in zh:
                continue
            es = [x.strip() for x in en.split("/")]
            zs = [x.strip() for x in zh.split("/")]
            if len(es) != len(zs):
                naline += 1
                continue
            nseg += 1
            for i, (a, b) in enumerate(zip(es, zs)):
                if not a or not b or SKIP_SEG.match(a):
                    continue
                # 复合番号上下文：前段是裸数字（如 `2/7 R`、`2/7/9 ID`）——此时尾段中文
                # **有意**省掉「第/师」之类（`第2/7团`，而非 `第2/第7团`），不算不一致。
                is_c = 1 if (i > 0 and re.fullmatch(r"\d+", es[i - 1])) else 0
                seg[a][b] += 1
                srcs[(a, b)][src or "?"] += 1
                cpd[(a, b)][is_c] += 1
                er = EXC.get(a) or ""
                excn[(a, b)][1 if (er and re.search(er, en)) else 0] += 1
                if len(ex[(a, b)]) < 3:
                    ex[(a, b)].append(en)
        bad = [(a, c) for a, c in seg.items() if len(c) >= min_]
        bad.sort(key=lambda x: (-sum(x[1].values()), x[0]))
        # 「真冲突」= 至少两种译法都来自**词库**（人工确认的是槽位受限的**有意保留**）
        def real(a, c):
            return sum(1 for v in c if srcs[(a, v)].get("词库") or srcs[(a, v)].get("POLICY"))
        # 复合上下文差异：少数写法**全部**只出现在复合尾段位置 ⇒ 有意保留，不判缺陷
        def only_compound(a, c):
            top = c.most_common(1)[0][0]
            for v in c:
                if v == top:
                    continue
                if cpd[(a, v)].get(0):
                    return False
            return True
        # 复合上下文差异：**每个位置类别内只有一种写法**（`第2/7团`：独立位置 `第7团`、
        # 复合尾段 `7团`）⇒ 差异由上下文解释，不是缺陷。
        def ctx_ok(a, c):
            for k in (0, 1):
                if len({v for v in c if cpd[(a, v)].get(k)}) > 1:
                    return False
            return True
        # 标记差：出现在复合位置的组里，各写法**只差「第/师」这类标记**（`第9步兵师`／
        # `9步兵师`、`第9澳大利亚师`／`第9澳大利亚`）⇒ 复合约定使然（实测语料 `N/M 后缀`
        # 514 行里 397 行保留「第」、92 行省略，取决于尾段是番号还是建制名称，无语义歧义）。
        def marker_only(a, c):
            if not any(cpd[(a, v)].get(1) for v in c):
                return False
            norm = {re.sub(r"[第师\s]", "", v) for v in c}
            return len(norm) == 1
        # 裁定表「排除」列：该段的少数写法**全部**出现在约定排除的 en 行里 ⇒ 有意保留
        def exc_only(a, c):
            top = c.most_common(1)[0][0]
            for v in c:
                if v == top:
                    continue
                if excn[(a, v)].get(0) or not excn[(a, v)].get(1):
                    return False
            return True

        def explained(a, c):
            return ctx_ok(a, c) or marker_only(a, c) or exc_only(a, c)

        cpd_bad = [(a, c) for a, c in bad if real(a, c) >= 2 and explained(a, c)]
        real_bad = [(a, c) for a, c in bad if real(a, c) >= 2 and not explained(a, c)]
        print("\n【%s】段位可对齐行 %d · 对齐失败(段数不等) %d · 同词异译段 %d 组"
              "（其中**词库真冲突 %d 组** · 上下文/标记/裁定表已解释 %d 组）"
              % (t, nseg, naline, len(bad), len(real_bad), len(cpd_bad)))
        for a, c in (real_bad if only_real else bad):
            tag = "⚠️真冲突" if real(a, c) >= 2 else "（槽位受限/人工确认）"
            if real(a, c) >= 2 and explained(a, c):
                tag = "（上下文已解释）"
            print("  %-34s 共 %d 处 %s → %s"
                  % (a[:34], sum(c.values()), tag,
                     " ｜ ".join("%s×%d[%s]" % (v, n, "/".join(k[:2] for k in srcs[(a, v)]))
                                 for v, n in c.most_common())))
            for v, n in c.most_common():
                print("        %-22s ← %s" % (v[:22], "; ".join(x[:52] for x in ex[(a, v)])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
