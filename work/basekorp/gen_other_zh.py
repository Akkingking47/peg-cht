# -*- coding: utf-8 -*-
"""BASEKORP 散文层 · other 块（348 条）译文生成。

Open AK Blitzkrieg / BKBK BaseKorps Blitzkrieg 战役的场景标签、任务简报、历史注释与评价语。
源：_other_src.txt（llm-todo 中不属于任何 *_todo.tsv 的剩余行）；
译文：other_dst_1..4.txt（分段保存，按序拼接）。
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

keys = []
with io.open(os.path.join(HERE, "_other_src.txt"), encoding="utf-8") as f:
    for ln in f:
        ln = ln.rstrip("\n")
        if not ln:
            continue
        keys.append(ln.split("\t", 1)[1] if "\t" in ln else ln)

DST = []
for i in (1, 2, 3, 4):
    with io.open(os.path.join(HERE, "other_dst_%d.txt" % i), encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if ln != "":
                DST.append(ln)

if len(DST) != len(keys):
    print("FATAL: dst=%d keys=%d" % (len(DST), len(keys)))
    n = min(len(DST), len(keys))
    for i in range(n):
        if DST[i] != DST[i]:
            pass
    # 打印尾部对照
    for i in range(max(0, n - 12), max(len(DST), len(keys))):
        k = keys[i] if i < len(keys) else "<none>"
        d = DST[i] if i < len(DST) else "<none>"
        print("%4d K=%s" % (i + 1, k[:80]))
        print("     D=%s" % d[:60])
    sys.exit(1)

for i, (s, d) in enumerate(zip(keys, DST), 1):
    if "\t" in d:
        print("FATAL: tab in dst at %d" % i)
        sys.exit(1)
    try:
        d.encode("gbk")
    except UnicodeEncodeError as e:
        print("FATAL: gbk at %d: %s" % (i, e))
        sys.exit(1)

with io.open(os.path.join(HERE, "zh-openak.tsv"), "w",
             encoding="utf-8", newline="\r\n") as f:
    f.write("src\tdst\r\n")
    for s, d in zip(keys, DST):
        f.write("%s\t%s\r\n" % (s, d))

print("zh-openak.tsv written: %d rows" % len(keys))
