#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2：修正 `_scn-file-overrides.tsv` 里**文件名大小写与磁盘不符**的序号覆盖行。

事故（2026-10-11 深夜，必须留档）：
  `apply_scn_numbers.py` 用 **stem 小写**拼文件名（`konrad_m.txt`）写进覆盖表，
  但磁盘上是 **`KONRAD_m.txt`**，而 `gen_scn.py` 用**真实文件名**做 key ⇒ 78 条里
  **56 条大写名的覆盖静默失效**（只有 `dessau_m.txt` 这类本来就小写的生效）。
  ⭐ 同型于 W1「静默错配」：**审计/应用脚本与消费端用了不同的 key 口径**。

本脚本：删掉带序号的旧行，用**磁盘真实文件名**重写一遍；幂等；默认 dry-run。
"""
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
RES = os.path.join(WS, "pegww2", "research")
OVF = os.path.join(RES, "_scn-file-overrides.tsv")
NUMRE = re.compile(r"^(西线|东线|北非)-\d\d ")


def main():
    apply_ = "--apply" in sys.argv
    lines = [l.rstrip("\n") for l in open(OVF, encoding="utf-8") if l.strip()]
    head = [l for l in lines if l.startswith("#")]
    rows = [l for l in lines if not l.startswith("#")]
    keep, numrows = [], []
    for l in rows:
        c = l.split("\t")
        if len(c) >= 5 and NUMRE.match(c[4]):
            numrows.append(c)
        else:
            keep.append(l)
    # 建「真实文件名」索引
    real = {}
    for sub in ("SCENARIO", "USERSCEN"):
        d = os.path.join(G, sub)
        if os.path.isdir(d):
            for fn in os.listdir(d):
                real[(sub, fn.lower())] = fn
    fixed, unreachable = [], []
    for c in numrows:
        sub, fn, idx, orig, zh = c[0], c[1], c[2], c[3], c[4]
        act = real.get((sub, fn.lower()))
        if not act:
            unreachable.append(fn)
            continue
        if act != fn:
            print("  修正文件名大小写：%-22s → %s" % (fn, act))
        fixed.append("\t".join([sub, act, idx, orig, zh]))

    print("=" * 100)
    print(f"覆盖表文件名大小写修正  模式={'[APPLY]' if apply_ else '[DRY-RUN]'}")
    print("=" * 100)
    print(f"  原带序号行 {len(numrows)} · 文件名修正 {sum(1 for c in numrows if real.get((c[0], c[1].lower())) != c[1])} · 找不到文件 {len(unreachable)}")
    if unreachable:
        print("    ⚠️ 找不到：", unreachable[:8])
    print(f"  非序号行保留 {len(keep)} 行，新写序号行 {len(fixed)} 行")

    if not apply_:
        print("\n  ⇒ dry-run，未写入。加 --apply 落盘。")
        return 0
    if not os.path.isfile(OVF + ".pre-case"):
        shutil.copy2(OVF, OVF + ".pre-case")
        print(f"  备份 ⇒ {os.path.relpath(OVF + '.pre-case', WS)}")
    # 头部（含列名）原样保留，其余按「非序号行 + 新序号行」重写
    head_block = [l for l in lines if l.startswith("#")]
    # 保留原文件里的列名行（无 # 的 '子目录\t文件\t行号\t期望原文\t译文'）
    colname = [l for l in rows if l.split("\t")[0].strip() in ("子目录", "子目录/文件") ]
    body = [l for l in keep if l not in colname]
    with open(OVF, "w", encoding="utf-8", newline="\n") as f:
        for l in head_block + colname:
            f.write(l + "\n")
        for l in body:
            f.write(l + "\n")
        for l in fixed:
            f.write(l + "\n")
    back = open(OVF, encoding="utf-8").read()
    miss = [c[1] for c in fixed if f"{c[1]}\t0\t" not in back]
    print(f"  回读校验 {'✅ 通过' if not miss else '❌ ' + str(miss[:5])}")
    return 0 if not miss else 1


if __name__ == "__main__":
    sys.exit(main())
