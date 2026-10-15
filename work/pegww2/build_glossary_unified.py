#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨层术语表**构建器**：把「界面层 / 文档层 / 装备层 / 前作基准」的术语并成一张表。

输出 `_统一术语表.tsv`：`en | zh | 层 | 类别 | 依据 | 备注`
   · 同一 en 若在不同层出现不同译法 ⇒ 该行 `备注` 记 `⚠️冲突: 层=译法 …`（**暴露**，不掩盖）
   · `依据` 优先取术语基准表里的原依据（保留裁决理由，治本要留痕）

用法: python build_glossary_unified.py [--apply] [--lineage[=DIR]]

★ D-1 溯源（**缺省关闭**；关闭时产物 sha256 与开启前逐字节相同）：
    --lineage       成品旁出 <成品>.lineage.tsv（逐行：命中哪个层文件 / 表内第几行 / 哪个键）
    --lineage=DIR   sidecar 集中到 DIR
  dry-run（不加 --apply）不落盘 ⇒ 也不产 sidecar。格式与 src_kind 词表见 work/lineage.py。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lineage import parse_argv, rel, show_help, want_help  # noqa: E402  D-1 溯源（缺省关闭）

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
PRES = os.path.join(WS, "peg", "research")
DOCS_TERM = os.path.join(WS, "pegww2", "docs-zh", "_翻译须知与术语.md")
DST = os.path.join(RES, "_统一术语表.tsv")

# 层优先级（大者优先当"规范值"）：术语基准 > 界面(本作) > 文档 > 界面(前作) > 装备
PRIO = {"基准": 5, "UI": 4, "DOCS": 3, "PeG-UI": 2, "EQ": 1}


def load_tsv(path, ecol, zcol, layer, cat, rows, srcs=None):
    """`srcs` 给定时（D-1 溯源）与 `rows` 严格同序地记 `(源文件相对路径, 表内 1 起行号)`。"""
    if not os.path.isfile(path):
        return
    for ln0, l in enumerate(open(path, encoding="utf-8-sig"), 1):
        if l.startswith("#"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) <= max(ecol, zcol):
            continue
        en, zh = c[ecol].strip(), c[zcol].strip()
        if not en or not zh or en in ("行号", "原文", "en"):
            continue
        if re.fullmatch(r"\d+", en):
            continue
        rows.append((en, zh, layer, cat, ""))
        if srcs is not None:
            srcs.append((rel(path), ln0))


def main():
    if want_help(sys.argv):            # ⭐ D-1：`--help` 打印用法（含 --lineage）后退出
        show_help(__doc__); return 0
    lin, rest = parse_argv(sys.argv)   # ⭐ D-1：缺省 (None, argv) ⇒ 走完全不知道溯源的旧路径
    apply = "--apply" in rest
    rows = []
    srcs = []                          # ⭐ D-1：与 rows 严格同序的命中来源（零副作用平行表）
    # 术语基准（带类别/依据/备注）
    p = os.path.join(PRES, "ui-glossary.tsv")
    if os.path.isfile(p):
        for ln0, l in enumerate(open(p, encoding="utf-8-sig"), 1):
            if l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 4 and c[0].strip() and c[1].strip():
                rows.append((c[0].strip(), c[1].strip(), "基准", c[2].strip(), c[3].strip()))
                srcs.append((rel(p), ln0))
    load_tsv(os.path.join(RES, "WW2Gui-map.tsv"), 1, 2, "UI", "界面", rows, srcs)
    load_tsv(os.path.join(RES, "WW2Misc-map.tsv"), 1, 2, "UI", "界面", rows, srcs)
    load_tsv(os.path.join(RES, "WW2Tips-map.tsv"), 1, 2, "UI", "界面", rows, srcs)
    load_tsv(os.path.join(RES, "WW2NAME-map.tsv"), 0, 1, "EQ", "人名", rows, srcs)
    load_tsv(os.path.join(RES, "ww2-eqp-map.tsv"), 0, 1, "EQ", "装备", rows, srcs)
    load_tsv(os.path.join(PRES, "gui030-zh.tsv"), 1, 2, "PeG-UI", "界面", rows, srcs)
    # 文档层：markdown 表格 | 英文 | 译法 | 备注 |
    if os.path.isfile(DOCS_TERM):
        for ln0, l in enumerate(open(DOCS_TERM, encoding="utf-8"), 1):
            m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", l)
            if not m or m.group(1) in ("英文", "---") or set(m.group(1)) <= {"-"}:
                continue
            en, zh, note = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            if en.startswith("-") or zh.startswith("-"):
                continue
            rows.append((en, zh, "DOCS", "文档", note))
            srcs.append((rel(DOCS_TERM), ln0))

    # 归并
    by = {}
    for (en, zh, layer, cat, basis), src in zip(rows, srcs):
        d = by.setdefault(en, {"v": {}, "cat": cat, "basis": basis, "src": {}})
        d["v"].setdefault(zh, set()).add(layer)
        if src is not None:            # ⭐ D-1：该译法出自哪个层文件的第几行
            d["src"].setdefault(zh, src)
        if layer == "基准" and basis:
            d["basis"] = basis
        if layer == "UI":
            d["cat"] = cat if cat != "文档" else d["cat"]

    out = []
    prov = []                          # ⭐ D-1：与 out 同序的 sidecar 行 (key, 表, 表内行, kind)
    nconf = 0
    for en in sorted(by, key=lambda x: (x.lower())):
        d = by[en]
        vs = d["v"]
        # 规范值：优先级最高的层所用的译法
        best, bestp = None, -1
        for zh, layers in vs.items():
            p = max(PRIO.get(l, 0) for l in layers)
            if p > bestp:
                best, bestp = zh, p
        layers_all = "/".join(sorted({l for ls in vs.values() for l in ls}))
        note = ""
        if len(vs) > 1:
            nconf += 1
            note = "⚠️冲突: " + " ".join("%s=%s" % (l, z) for z, ls in vs.items() for l in sorted(ls))
        out.append((en, best, layers_all, d["cat"], d["basis"], note))
        # ⭐ D-1：同 en 多译法 ⇒ 该值靠「层优先级」压过他层（override）；译法即原文 ⇒ identity
        st, sl = d["src"].get(best, ("-", 0))
        prov.append((en, st, sl,
                     "identity" if best == en else ("override" if len(vs) > 1 else "exact")))

    print("术语条目 %d 条 · 其中跨层/跨值冲突 %d 条" % (len(out), nconf))
    if not apply:
        print("（dry-run；加 --apply 写 %s）" % os.path.relpath(DST, WS))
        return 0
    with open(DST, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 跨层统一术语表（构建器产出，勿手改；改译法请改各层 map 后重跑本脚本）\n")
        f.write("# 层：基准=前作术语表/UI=本作界面/DOCS=文档层/PeG-UI=前作界面/EQ=装备\n")
        f.write("en\tzh\t层\t类别\t依据\t备注\n")
        for r in out:
            f.write("\t".join(r) + "\n")
    print("已写 %s" % os.path.relpath(DST, WS))
    if lin is not None:                # ⭐ D-1：成品旁出 <成品>.lineage.tsv
        # 3 行表头（2 行注释 + 1 行列名）⇒ 第 n 行数据 = 成品第 n+4 行
        with lin.open(DST) as lg:
            for n, r in enumerate(prov, 4):
                lg.record(n, r[0], r[1], r[2], r[3])
        print("  + %s.lineage.tsv" % os.path.relpath(DST, WS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
