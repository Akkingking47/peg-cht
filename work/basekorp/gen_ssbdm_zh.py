# -*- coding: utf-8 -*-
"""BASEKORP 散文层 · ssbdm 块（166 条）译文生成（分批累积）。

ssbdm = 「17. SS [BdM] Campaign」架空战役（女元首 Ilse Koch 主导的女性党卫军征服欧洲，27 场景）。
源：_ssbdm_src.txt（= ssbdm_todo.tsv 的 src 顺序）。
译文：ssbdm_dst_NN.txt（按文件名序拼接，可分批追加）；本脚本取 keys 的前 len(DST) 条配对，
已译部分写入 zh-ssbdm.tsv，未译部分保持原文（由 translate_prose.py 兜底）。
"""
import io
import os
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))

keys = []
with io.open(os.path.join(HERE, "_ssbdm_src.txt"), encoding="utf-8") as f:
    for ln in f:
        ln = ln.rstrip("\n")
        if not ln:
            continue
        keys.append(ln.split("\t", 1)[1] if "\t" in ln else ln)

DST = []
for fp in sorted(glob.glob(os.path.join(HERE, "ssbdm_dst_*.txt"))):
    with io.open(fp, encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if ln != "":
                DST.append(ln)

if len(DST) > len(keys):
    print("FATAL: dst=%d > keys=%d" % (len(DST), len(keys)))
    sys.exit(1)

for i, d in enumerate(DST, 1):
    if "\t" in d:
        print("FATAL: tab in dst at %d" % i)
        sys.exit(1)
    try:
        d.encode("gbk")
    except UnicodeEncodeError as e:
        print("FATAL: gbk at %d: %s" % (i, e))
        sys.exit(1)

with io.open(os.path.join(HERE, "zh-ssbdm.tsv"), "w",
             encoding="utf-8", newline="\r\n") as f:
    f.write("src\tdst\r\n")
    for s, d in zip(keys, DST):
        f.write("%s\t%s\r\n" % (s, d))

print("zh-ssbdm.tsv written: %d / %d rows (%.1f%%)" % (
    len(DST), len(keys), 100.0 * len(DST) / len(keys)))
