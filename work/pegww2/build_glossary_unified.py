#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨层术语表**构建器**：把「界面层 / 文档层 / 装备层 / 前作基准」的术语并成一张表。

输出 `_统一术语表.tsv`：`en | zh | 层 | 类别 | 依据 | 备注`
   · 同一 en 若在不同层出现不同译法 ⇒ 该行 `备注` 记 `⚠️冲突: 层=译法 …`（**暴露**，不掩盖）
   · `依据` 优先取术语基准表里的原依据（保留裁决理由，治本要留痕）

用法: python build_glossary_unified.py [--apply]
"""
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
PRES = os.path.join(WS, "peg", "research")
DOCS_TERM = os.path.join(WS, "pegww2", "docs-zh", "_翻译须知与术语.md")
DST = os.path.join(RES, "_统一术语表.tsv")

# 层优先级（大者优先当"规范值"）：术语基准 > 界面(本作) > 文档 > 界面(前作) > 装备
PRIO = {"基准": 5, "UI": 4, "DOCS": 3, "PeG-UI": 2, "EQ": 1}


def load_tsv(path, ecol, zcol, layer, cat, rows):
    if not os.path.isfile(path):
        return
    for l in open(path, encoding="utf-8-sig"):
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


def main():
    rows = []
    # 术语基准（带类别/依据/备注）
    p = os.path.join(PRES, "ui-glossary.tsv")
    if os.path.isfile(p):
        for l in open(p, encoding="utf-8-sig"):
            if l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 4 and c[0].strip() and c[1].strip():
                rows.append((c[0].strip(), c[1].strip(), "基准", c[2].strip(), c[3].strip()))
    load_tsv(os.path.join(RES, "WW2Gui-map.tsv"), 1, 2, "UI", "界面", rows)
    load_tsv(os.path.join(RES, "WW2Misc-map.tsv"), 1, 2, "UI", "界面", rows)
    load_tsv(os.path.join(RES, "WW2Tips-map.tsv"), 1, 2, "UI", "界面", rows)
    load_tsv(os.path.join(RES, "WW2NAME-map.tsv"), 0, 1, "EQ", "人名", rows)
    load_tsv(os.path.join(RES, "ww2-eqp-map.tsv"), 0, 1, "EQ", "装备", rows)
    load_tsv(os.path.join(PRES, "gui030-zh.tsv"), 1, 2, "PeG-UI", "界面", rows)
    # 文档层：markdown 表格 | 英文 | 译法 | 备注 |
    if os.path.isfile(DOCS_TERM):
        for l in open(DOCS_TERM, encoding="utf-8"):
            m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", l)
            if not m or m.group(1) in ("英文", "---") or set(m.group(1)) <= {"-"}:
                continue
            en, zh, note = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            if en.startswith("-") or zh.startswith("-"):
                continue
            rows.append((en, zh, "DOCS", "文档", note))

    # 归并
    by = {}
    for en, zh, layer, cat, basis in rows:
        d = by.setdefault(en, {"v": {}, "cat": cat, "basis": basis})
        d["v"].setdefault(zh, set()).add(layer)
        if layer == "基准" and basis:
            d["basis"] = basis
        if layer == "UI":
            d["cat"] = cat if cat != "文档" else d["cat"]

    out = []
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

    print("术语条目 %d 条 · 其中跨层/跨值冲突 %d 条" % (len(out), nconf))
    if "--apply" not in sys.argv:
        print("（dry-run；加 --apply 写 %s）" % os.path.relpath(DST, WS))
        return 0
    with open(DST, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 跨层统一术语表（构建器产出，勿手改；改译法请改各层 map 后重跑本脚本）\n")
        f.write("# 层：基准=前作术语表/UI=本作界面/DOCS=文档层/PeG-UI=前作界面/EQ=装备\n")
        f.write("en\tzh\t层\t类别\t依据\t备注\n")
        for r in out:
            f.write("\t".join(r) + "\n")
    print("已写 %s" % os.path.relpath(DST, WS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
