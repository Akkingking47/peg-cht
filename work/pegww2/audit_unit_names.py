#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""找出「部队编制名(`_u.txt`) 混入地名」的场景（**只读**）。

判据：
  `_u.txt` 行0＝名栏，行1+＝**该场的单位名**（如「缴获 T-34/76A」「第115装甲营/第15装甲掷弹兵师」「工兵」）。
  若行1+ 里**过半**条目同时出现在别处的地名池（`_m.txt` 行1+ / `<stem>.TXT` 行1+）⇒ 判定「单位名槽里是地名」。

产出：`pegww2/research/_编制名污染-审计.tsv`
用法: python audit_unit_names.py
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
RES = os.path.join(WS, "pegww2", "research")
OUT = os.path.join(RES, "_编制名污染-审计.tsv")
DIRS = [os.path.join(G, "SCENARIO"), os.path.join(G, "USERSCEN")]

IDX = {}
for d in DIRS:
    if os.path.isdir(d):
        for n in os.listdir(d):
            if os.path.isfile(os.path.join(d, n)):
                IDX.setdefault(n.lower(), os.path.join(d, n))

PLACE = re.compile(r"(?i)(河|湖|海|湾|山|岛|港|滩头|高地|机场|采石场|盐沼|桥|峡|沼泽|平原|半岛|岬|运河)")
UNIT = re.compile(r"(?i)(/|团|营|师|旅|连|排|班|队|旅|缴获|工兵|装甲|步兵|炮兵|掷弹|侦察|伞兵|骑兵|高射|反坦克|要塞|R$|师部|集团军|军)")


def lines(p):
    try:
        return io.open(p, encoding="gbk", errors="replace").read().splitlines()
    except Exception:
        return []


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    # 地名池
    place_pool = set()
    for k, p in IDX.items():
        if k.endswith("_m.txt") or k.endswith(".txt") and not k.endswith("_u.txt") and not k.endswith("_i.txt"):
            pass
    for k, p in IDX.items():
        base = os.path.basename(p).lower()
        if base.endswith("_m.txt") or (base.endswith(".txt") and not re.search(r"(_u|_i|_v|_l|_bv|_tv)\.txt$", base)):
            for x in lines(p)[1:]:
                if x.strip():
                    place_pool.add(x.strip())

    rows = []
    for k, p in sorted(IDX.items()):
        if not k.endswith("_u.txt"):
            continue
        ls = lines(p)
        body = [x.strip() for x in ls[1:] if x.strip()]
        if len(body) < 3:
            continue
        unit_n = sum(1 for x in body if UNIT.search(x) and not PLACE.search(x))
        place_n = sum(1 for x in body if x in place_pool and not UNIT.search(x))
        # 判据：地名占比 ≥ 50% 且 单位名占比 ≤ 20%
        if place_n / len(body) >= 0.5 and unit_n / len(body) <= 0.2:
            rows.append([os.path.basename(p), ls[0].strip() if ls else "-", str(len(body)),
                         "地名%d/单位%d" % (place_n, unit_n), " / ".join(body[:6])])

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 「部队编制名(_u.txt 行1+) 混入地名」审计（只读）\n")
        f.write("# 判据：_u.txt 行1+ 中过半条目同时出现在地名池(_m.txt/.TXT 行1+) ⇒ 单位名槽被地名污染\n")
        f.write("文件\t行0（名栏）\t条目数\t占比\t前6条\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    print("疑似被地名污染的单位名文件：%d 个" % len(rows))
    for r in rows[:40]:
        print("  %-22s 行0=%-24s %s" % (r[0], r[1][:24], r[3]))
    print("→ %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
