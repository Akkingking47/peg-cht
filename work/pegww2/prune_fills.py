#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS · 译表「合流」：按当前可译判定裁剪 _fill 行，并按段号保住既有译文。

用途：工具的**可译判定**修正后（例如新增屏蔽 `{\\*…}` SmartTag 元数据），旧译表里会残留
      「已不可译」的行。段号空间没变（未改词法），所以只要按**段号**把译文搬到新表即可。
副作用：同时删除该源**过期的分片任务表**（`_task-*.tsv` 表头含该 rel 的）。

用法: python prune_fills.py <rel> [<rel> ...]
"""
import glob
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
FILL = os.path.join(WS, "pegww2", "docs-zh", "_fill")
sys.path.insert(0, os.path.join(WS, "work", "pegww2"))
import doc_rtf as R          # noqa: E402


def prune(rel):
    # ⚠️⚠️ **只对 RTF 源有效**：`R.eligible_ids()` 是 RTF 的可译判定；把它用在 `.txt` 上
    #      会把每行都判成"不可译"⇒ **整份译表被裁空**（踩过：两份 .txt 译表共 220 段译文被裁掉）。
    if not rel.endswith(".rtf"):
        print("  ⏭ 跳过 %s（非 RTF 源，不能用 RTF 可译判定裁剪）" % rel[:56])
        return
    # ⭐ 裁剪前**必须先合并**：曾因先裁剪、把未合并的分片译稿一起删掉（`_task-D201-02.tsv` 93 段丢失）
    try:
        import merge_tasks
        merge_tasks.merge_one(rel)
    except Exception as e:
        print("  ⚠️ 预合并失败（继续裁剪，请人工确认）%s: %s" % (rel, e))
    fill = os.path.join(FILL, rel + ".tsv")
    if not os.path.isfile(fill):
        print("  ⚠️ 无译表: %s" % rel)
        return
    try:
        ok = R.eligible_ids(rel)
    except Exception as e:
        print("  ❌ 取可译集失败 %s: %s" % (rel, e))
        return
    lines = [l.rstrip("\n") for l in open(fill, encoding="utf-8")]
    head = [l for l in lines if l.startswith("#") or l.split("\t")[0].strip() in ("段号", "行号")]
    kept, dropped, kept_zh = [], 0, 0
    for l in lines:
        if l in head:
            continue
        c = l.split("\t")
        if len(c) < 2 or not c[0].strip().isdigit():
            continue
        if int(c[0]) in ok:
            kept.append(l)
            if len(c) > 2 and c[2].strip():
                kept_zh += 1
        else:
            dropped += 1
    with open(fill, "w", encoding="utf-8", newline="\n") as f:
        for h in head:
            f.write(h + "\n")
        for l in kept:
            f.write(l + "\n")
    # 删过期分片
    rm = 0
    for p in glob.glob(os.path.join(FILL, "_task-*.tsv")):
        try:
            if rel in open(p, encoding="utf-8").readline():
                os.remove(p)
                rm += 1
        except Exception:
            pass
    print("  %-56s 保留 %3d 段（含已译 %3d）· 裁掉不可译 %3d · 删过期分片 %d" % (
        rel[:56], len(kept), kept_zh, dropped, rm))


if __name__ == "__main__":
    for r in sys.argv[1:]:
        prune(r)
