# -*- coding: utf-8 -*-
"""另两份「残留」表的真实内容（只读）。"""
import io
import os
import re
import collections

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "glossary", "glossary-residual.tsv")
TODO = os.path.join(WS, "pegww2", "research", "_未译清单.tsv")

for path, label in ((RES, "glossary/glossary-residual.tsv"), (TODO, "pegww2/research/_未译清单.tsv")):
    print("=" * 72)
    print(label)
    print("=" * 72)
    raw = io.open(path, encoding="utf-8-sig").read().splitlines()
    print("总行 %d" % len(raw))
    for ln in raw[:4]:
        print("   RAW: %s" % ln[:180].replace("\t", " | "))
    body = [l for l in raw if l.strip() and not l.startswith("#")]
    hdr = body[0].split("\t")
    rows = [l.split("\t") for l in body[1:]]
    print("表头 %s · 数据行 %d" % (hdr, len(rows)))

    if path == RES:
        idx = {k: i for i, k in enumerate(hdr)}
        print("  kind: %s" % dict(collections.Counter(r[idx["kind"]] for r in rows if len(r) > idx["kind"])))
        print("  scope: %s" % dict(collections.Counter(r[idx["scope"]] for r in rows if len(r) > idx["scope"]).most_common(8)))
        print("  src: %s" % dict(collections.Counter(r[idx["src"]] for r in rows if len(r) > idx["src"]).most_common(8)))
        sb = [r for r in rows if len(r) > idx["should_be"] and r[idx["should_be"]].strip()]
        print("  should_be 非空（真有标准译名没用上）: %d / %d" % (len(sb), len(rows)))
        for r in sb[:10]:
            print("     %s => %s  [%s]" % (r[0][:34], r[idx["should_be"]][:20], r[idx["kind"]]))
        nobe = [r for r in rows if not (len(r) > idx["should_be"] and r[idx["should_be"]].strip())]
        for r in nobe[:8]:
            print("     (无标准名) %s  [%s] kind=%s" % (r[0][:38], r[idx["cat"]][:16], r[idx["kind"]]))
    else:
        # 该表首行是注释，第二行才是真表头
        hdr2 = body[0].split("\t")
        rows2 = rows
        print("  真实列: %s" % hdr2)
        if len(rows2[0]) >= 4:
            print("  按文件: %s" % dict(collections.Counter(r[1] for r in rows2 if len(r) > 1).most_common(10)))
            for r in rows2[:10]:
                print("     %s:%s  %s" % (r[1][:22], r[2] if len(r) > 2 else "", (r[3] if len(r) > 3 else "")[:90]))
    print()
