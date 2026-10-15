#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 22 个舰名：统一为「**前缀 + 舰名 + 号**」（本作口径；术语库预填的「美国海军 X」既不合口径也更长 ⇒ 挤坏 UI）。

例：`USS New Jersey` 美国海军 新泽西 → **USS 新泽西号**
    `HMS Ajax`       皇家海军阿贾克斯号 → **HMS 阿贾克斯号**
    `RM N. Da Recco` 意海军尼科洛索·达雷科号 → **RM 尼科洛索·达雷科号**
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-scn-map.tsv")
OUT = os.path.join(RES, "_scn-fill-shipnames.tsv")

PREFIX = re.compile(r"^(USS|HMS|KMS|RM|RN|JN|IJN|ITS|ORP|HMAS|HMNZS|FS)\s+")
NAVY = ("英国皇家海军", "美国海军", "皇家海军", "德国海军", "日本海军", "意大利海军", "意海军", "美海军", "美军", "美舰", "海军")


def main():
    rows = []
    for i, l in enumerate(open(MAP, encoding="utf-8-sig")):
        if i < 4 or not l.strip():
            continue
        f = l.rstrip("\n").split("\t")
        if len(f) < 3 or not f[1].strip():
            continue
        src, zh = f[0], f[1]
        m = PREFIX.match(src)
        if not m or zh.startswith(m.group(1)):
            continue
        name = zh.strip()
        for n in NAVY:
            if name.startswith(n):
                name = name[len(n):].strip()
        name = name.strip(" 　")
        if name.endswith("号"):
            name = name[:-1]
        if not name:
            continue
        new = f"{m.group(1)} {name}号"
        rows.append((src, zh, new))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 舰名统一为「前缀 + 舰名 + 号」\n原文\t译文\n")
        for s, o, n in rows:
            f.write(f"{s}\t{n}\n")
    print(f"舰名待修正 {len(rows)} 条 → {os.path.relpath(OUT, WS)}")
    for s, o, n in rows:
        print(f"  {s[:32]:34s} {o[:22]:24s} → {n}")


if __name__ == "__main__":
    main()
