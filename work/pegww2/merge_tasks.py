#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS · 把分片任务表的译文合并回主译表。

分片表由 `make_chunks.py` 生成，表头第 1 行含源文件名：
    `# <rel> · 第 i/n 片（k 段）——只填第三列`
本脚本按该表头匹配，把所有 `_task-*.tsv` 里属于 <rel> 的已填译文按**段号**合并进
`_fill\\<rel>.tsv`（主表的原文列与段号列一字不动）。

用法: python merge_tasks.py <rel>
"""
import glob
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
FILL = os.path.join(WS, "pegww2", "docs-zh", "_fill")


def merge_one(rel):
    r"""把属于 <rel> 的所有分片译文按段号并入 `_fill\<rel>.tsv`；返回并入段数。

    ⭐ 分片定位优先用 **tag 索引**（`_chunks-index.tsv`），**不依赖任务表首行注释**：
    子代理曾改写首行注释（`PeGWW2`→`PeG-WW2`），导致按表头匹配失败、整片译文没并进去。
    """
    main_tsv = os.path.join(FILL, rel + ".tsv")
    if not os.path.isfile(main_tsv):
        return 0
    # 1) 从索引取本 rel 的 tag 前缀
    tags = []
    index_path = os.path.join(FILL, "_chunks-index.tsv")
    if os.path.isfile(index_path):
        for l in open(index_path, encoding="utf-8"):
            if l.startswith("#") or not l.strip():
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 3 and c[2] == rel:
                tags.append(c[0])
    files = []
    for tg in set(tags):
        files += glob.glob(os.path.join(FILL, "_task-%s-*.tsv" % tg))
    if not files:                       # 2) 索引缺失时回退到表头匹配
        for p in sorted(glob.glob(os.path.join(FILL, "_task-*.tsv"))):
            with open(p, encoding="utf-8") as f:
                if rel in f.readline():
                    files.append(p)
    files = sorted(set(files))
    lines = [l.rstrip("\n") for l in open(main_tsv, encoding="utf-8")]
    head = [l for l in lines if l.startswith("#") or l.split("\t")[0].strip() in ("段号", "行号")]
    order, rows = [], {}
    for l in lines:
        if l in head:
            continue
        if "\t" not in l:
            continue
        k, rest = l.split("\t", 1)
        k = k.strip()
        if not k:
            continue
        if "\t" in rest:
            orig, zh = rest.rsplit("\t", 1)
        else:
            orig, zh = rest, ""
        order.append(k)
        rows[k] = [k, orig, zh]
    merged = 0
    used = []
    invalid = []
    for p in files:
        with open(p, encoding="utf-8") as f:
            used.append(os.path.basename(p))
            for l in f:
                if l.startswith("#") or l.split("\t")[0].strip() in ("段号", "行号"):
                    continue
                c = l.rstrip("\n").split("\t")
                # ⚠️ 两个坑叠加：① 原文里可能含**真制表符**（老 txt 做列对齐用）；
                #    ② 任务表行常带**行尾多余制表符**。故不能按 tab 切分、也不能简单 rsplit。
                #    正解：**以主表原文为前缀**匹配 —— 认前缀 ⇒ 其后（去掉分隔 tab）即译文。
                if "\t" not in l:
                    invalid.append((os.path.basename(p), l.strip()[:12], "无制表符"))
                    continue
                key, rest = l.rstrip("\n").split("\t", 1)
                key = key.strip()
                if key not in rows:
                    invalid.append((os.path.basename(p), key, "段号不在主表"))
                    continue
                main_orig = rows[key][1]
                if rest.startswith(main_orig):
                    zh = rest[len(main_orig):]
                    if zh.startswith("\t"):
                        zh = zh[1:]
                    zh = zh.rstrip("\t")
                else:
                    invalid.append((os.path.basename(p), key, "原文列与主表不一致"))
                    continue
                if zh.strip():
                    rows[key][2] = zh
                    merged += 1
    if invalid:
        print("    ⚠️ 拒收 %d 行（未并入）：" % len(invalid))
        for fn, k, why in invalid[:8]:
            print("       %s 段%s %s" % (fn, k, why))
    with open(main_tsv, "w", encoding="utf-8", newline="\n") as f:
        for h in head:
            f.write(h + "\n")
        for k in order:
            f.write("\t".join(rows[k]) + "\n")
    done = sum(1 for k in order if rows[k][2].strip())
    print("合并 %-58s 用片 %d 个 · 并入 %d 段 ⇒ 已译 %d/%d" % (
        rel[:58], len(used), merged, done, len(order)))
    return merged


def main():
    rel = sys.argv[1]
    n = merge_one(rel)
    # ⭐ 回灌自动化（治本件续）：合片成功后**自动把新译名并入分层词库**
    #    （`work/glossary/ingest_layers.py`）。非阻塞：失败只提示，不打断合并。
    if n > 0:
        try:
            import subprocess
            WS = r"D:\DSH\军事游戏汉化"
            r = subprocess.run([sys.executable, os.path.join(WS, "work", "glossary", "ingest_layers.py"), "--apply"],
                               capture_output=True, text=True, encoding="utf-8", timeout=900)
            tail = [x for x in (r.stdout or "").split("\n") if x.strip()][-3:]
            print("   ↻ 已回灌词库（ingest_layers.py）%s" % ("；".join(t.strip() for t in tail) if tail else ""))
            print("     ⚠️ 词库已变 ⇒ 请跑 work/glossary/layer_gate.py（或 --baseline）后再构建/投放")
        except Exception as e:
            print("   （回灌词库跳过：%s）" % e)
    return 0 if n >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
