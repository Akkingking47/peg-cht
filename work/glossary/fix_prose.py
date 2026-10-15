#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补译 · 散文 6 行（按词库既有口径：制作署名/元数据**保留**，不译）。

用法: python fix_prose.py [--apply]
"""
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
sys.path.insert(0, os.path.join(WS, "work", "pegww2"))
from tsv_esc import esc  # noqa: E402

MAP = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup")
TRANS = [
    ("SCENARIO/BoB_BoB04_i.txt", 27, "注：水上飞机可在任何盟军陆上机场或航空母舰上修理与补给。"),
    ("SCENARIO/DAK_DAK8_i.txt", 8, "作战提示：德军 88 毫米炮单位对付坦克与碉堡非常出色。"),
    ("SCENARIO/DAK_DAKTU02_i.txt", 5, "如果你能成功，他们除了投降别无选择。"),
    ("SCENARIO/GAW08_i.txt", 3, "巴黎近在眼前，你必须摧毁法国以及英国的陆、空、海军力量。"),
    ("SCENARIO/usvsussr10.txt", 0, "盟军夺取符拉迪沃斯托克"),
    ("SCENARIO/usvsussr9.txt", 2, "盟军希望入侵萨哈林岛(Sakhalin Island)，打苏联人一个措手不及"),
]


def main():
    apply_ = "--apply" in sys.argv
    rows = []
    for rel, idx, zh in TRANS:
        d, f = rel.split("/")
        p = os.path.join(BK, d, f)
        if not os.path.isfile(p):
            print("   ⚠️ 无备份 %s" % rel)
            continue
        parts = io.open(p, encoding="latin-1").read().split("\n")
        if idx >= len(parts):
            print("   ⚠️ 行号越界 %s" % rel)
            continue
        en = parts[idx].rstrip("\r\n")
        rows.append((esc(en), esc(zh), "补译-散文"))
        print("   %-28s 行%-3d" % (f, idx + 1))
        print("      原: %r" % en[:96])
        print("      译: %s" % zh)
    print("\n=== 待追加 %d 条 ===" % len(rows))
    if not apply_:
        print("（dry-run；加 --apply）")
        return 0
    have = set()
    for l in io.open(MAP, encoding="utf-8-sig"):
        if not l.startswith("#"):
            have.add(l.split("\t")[0])
    add = [r for r in rows if r[0] not in have]
    with io.open(MAP, "a", encoding="utf-8", newline="\n") as w:
        for k, z, s in add:
            w.write("%s\t%s\t%s\n" % (k, z, s))
    print("✅ 已追加 %d 条到 %s" % (len(add), MAP))
    return 0


if __name__ == "__main__":
    sys.exit(main())
