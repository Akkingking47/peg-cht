#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""舰名一致性审计：本作口径是「**舰名前缀保留 + 舰名译出 + 加「号」**」
（`USS Enterprise`⇒`USS 企业号`）。但术语库预填把一些舰名译成了「美国海军 X」等，且更长 ⇒ 挤坏 UI 面板。
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
MAP = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")
PREFIX = re.compile(r"^(USS|HMS|KMS|RM|RN|JN|IJN|ITS|ORP|HMAS|HMNZS|FS|USS\b)\s+")
NAVY_ZH = ("美国海军", "英国皇家海军", "皇家海军", "德国海军", "日本海军", "意大利海军", "海军")


def main():
    rows = []
    for i, l in enumerate(open(MAP, encoding="utf-8-sig")):
        if i < 4 or not l.strip():
            continue
        f = l.rstrip("\n").split("\t")
        if len(f) < 3 or not f[1].strip():
            continue
        src, zh, cls = f[0], f[1], f[2]
        if not PREFIX.match(src):
            continue
        pre = PREFIX.match(src).group(1)
        ok = zh.startswith(pre)
        rows.append((src, zh, cls, pre, ok))
    bad = [r for r in rows if not r[4]]
    print(f"以舰名前缀开头的条目: {len(rows)}  其中**译文未保留前缀**: {len(bad)}")
    print("-" * 96)
    for src, zh, cls, pre, ok in bad:
        print(f"  {src[:34]:36s} → {zh[:26]:28s} [{cls}]")
    print()
    print(f"✅ 已正确保留前缀: {len(rows) - len(bad)}")
    for src, zh, cls, pre, ok in [r for r in rows if r[4]][:10]:
        print(f"  {src[:34]:36s} → {zh[:26]}")


if __name__ == "__main__":
    main()
