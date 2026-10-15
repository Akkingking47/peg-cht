#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS · 把**已完成**（译表无空译）的源全部建出成品并过门。

- RTF 源 → `doc_rtf.do(rel, 'build')` + `verify`
- TXT 源 → `doc_translate.do_txt(path, rel, 'build')` + `verify`
- XLS  见 `doc_xls.ps1` / `verify_xls.ps1`（Excel COM，另行调用）

用法: python build_all.py [--apply]   不带 --apply 为 dry-run
"""
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
sys.path.insert(0, os.path.join(WS, "work", "pegww2"))
import doc_rtf as R            # noqa: E402
import doc_translate as T      # noqa: E402

FILL = os.path.join(WS, "pegww2", "docs-zh", "_fill")


def completed():
    out = []
    for dp, _, fs in os.walk(FILL):
        for f in fs:
            if f.startswith("_") or not f.endswith(".tsv") or f.endswith(".cells.tsv"):
                continue
            p = os.path.join(dp, f)
            rows, empty = [], 0
            for l in open(p, encoding="utf-8"):
                if l.startswith("#") or l.split("\t")[0].strip() in ("段号", "行号"):
                    continue
                c = l.rstrip("\n").split("\t")
                if len(c) >= 3 and c[0].strip().isdigit():
                    rows.append(c)
                    if not c[2].strip():
                        empty += 1
            if rows and empty == 0:
                out.append((os.path.relpath(p, FILL)[:-4], len(rows)))
    return sorted(out)


def main():
    # ⭐ 词库门（治本件第 3 步）：DOCS 构建前先过门（只拦新增偏离与词库缺失）
    try:
        sys.path.insert(0, os.path.join(WS, "work", "glossary"))
        import layer_gate
        ok, _m = layer_gate.quick_check()
        if not ok:
            print("  ⛔ 词库门未过 ⇒ 拒绝构建（先跑 work/glossary/layer_gate.py --full）")
            return 1
    except Exception as e:
        print("  （词库门跳过：%s）" % e)
    apply_ = "--apply" in sys.argv
    done = completed()
    print("已完成源 %d 个" % len(done))
    rtf = [r for r, _ in done if r.endswith(".rtf")]
    txt = [r for r, _ in done if not r.endswith(".rtf")]
    if apply_:
        sys.argv = [sys.argv[0], "build", ""] + ["--apply"]
    for rel in rtf:
        R.do(rel, "build")
    for rel in txt:
        T.do_txt(os.path.join(T.DOCS, rel), rel, "build")
    print()
    bad = []
    for rel in rtf:
        if R.do(rel, "verify"):
            bad.append(rel)
    for rel in txt:
        if T.do_txt(os.path.join(T.DOCS, rel), rel, "verify"):
            bad.append(rel)
    print()
    print("== 建出 %d 份 · 过门失败 %d 份 %s" % (len(done), len(bad), bad if bad else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
