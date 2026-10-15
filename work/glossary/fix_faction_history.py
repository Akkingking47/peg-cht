#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**按史料称法**修正场景文本（用户 2026-10-12 口径：不看原文拼写，看历史上各方怎么叫）。

依据：`work/glossary/faction_place_audit.py` 输出（`glossary/evidence/faction-place-audit.txt`）。
本批只落**明确无争议**的 14 处：

| 地名/作战 | 视角 | 现用 → 史称 | 处数 | 依据 |
|---|---|---|---|---|
| Tarnopol | 德 | 捷尔诺波尔 → **塔尔诺波尔** | 6 | 德/奥方名 Tarnopol（1939 波兰时期亦用） |
| Posen | 德 | 波兹南 → **波森** | 2 | 德方名 Posen |
| Cernauti | 德 | 切尔诺夫策 → **切尔诺维茨** | 3 | 德/奥方名 Czernowitz |
| Kattowitz | 德 | 卡托维兹 → **卡托维茨** | 1 | 德方名 Kattowitz |
| Danzig | 德/苏 | 格但斯克 → **但泽** | 1 | 德方名 Danzig；苏方战时亦用 Данциг |
| Kursk（作战） | 苏 | 「堡垒」攻势 → **「库尔斯克」攻势** | 1 | 苏方战史名；德方代号才是「堡垒」 |

**故意不改（留给用户定年代）**：`Lodz` 5 处 —— 1939 年德占初期仍作 **Lodsch**，
1940 年 4 月才改名 **Litzmannstadt**（利茨曼施塔特）；改不改取决于场景年代。

用法: python fix_faction_history.py [--apply]
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
COPYBK = os.path.join(WS, "backup", "before-faction-history")

# (文件, 0-based 行号, 现用, 改为)
EDITS = [
    ("119.TXT", 2, "捷尔诺波尔", "塔尔诺波尔"),
    ("119V.txt", 0, "捷尔诺波尔", "塔尔诺波尔"),
    ("119tV.txt", 0, "捷尔诺波尔", "塔尔诺波尔"),
    ("RM_usvsruss14_i.txt", 2, "捷尔诺波尔", "塔尔诺波尔"),
    ("US41BV.TXT", 0, "捷尔诺波尔", "塔尔诺波尔"),
    ("wdarrabv.txt", 0, "捷尔诺波尔", "塔尔诺波尔"),
    ("DAK_Choice_m.txt", 126, "波兹南", "波森"),
    ("DAK_SPChoice_m.txt", 75, "波兹南", "波森"),
    ("DAK_Choice_m.txt", 171, "切尔诺夫策", "切尔诺维茨"),
    ("DAK_SPChoice_m.txt", 135, "切尔诺夫策", "切尔诺维茨"),
    ("DR08TV.txt", 1, "切尔诺夫策", "切尔诺维茨"),
    ("G7Pzra703_i.txt", 2, "卡托维兹", "卡托维茨"),
    ("RTB28_m.txt", 0, "格但斯克", "但泽"),
    ("RM_usvsruss15b.txt", 0, "「堡垒」(Zitadelle)攻势", "「库尔斯克」(Zitadelle)攻势"),
]


def main():
    apply_ = "--apply" in sys.argv
    rows, show = [], []
    for fn, idx, old, new in EDITS:
        en = io.open(os.path.join(BK, fn), encoding="cp1252", errors="replace").read().split("\n")
        zh = io.open(os.path.join(GAME, fn), encoding="gbk", errors="replace").read().split("\n")
        if idx >= len(zh) or old not in zh[idx]:
            print("   ⚠️ 跳过 %s 行%d：未见「%s」" % (fn, idx, old))
            continue
        nl = zh[idx].replace(old, new)
        rows.append(("SCENARIO", fn, str(idx), en[idx], nl))
        show.append((fn, idx, zh[idx], nl))
    print("=== 待落 per-file 覆盖 %d 条 ===" % len(rows))
    for fn, idx, a, b in show:
        print("   %-24s 行%-4d %s" % (fn, idx, a[:76]))
        print("   %-24s      → %s" % ("", b[:76]))
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0
    t = io.open(OVF, encoding="utf-8").read()
    have = {tuple(l.split("\t")[:3]) for l in t.split("\n") if not l.startswith("#")}
    add = [r for r in rows if tuple(r[:3]) not in have]
    os.makedirs(COPYBK, exist_ok=True)
    b = os.path.join(COPYBK, os.path.basename(OVF))
    if not os.path.isfile(b):
        shutil.copy2(OVF, b)
    if add:
        if not t.endswith("\n"):
            t += "\n"
        t += "".join("\t".join(r) + "\n" for r in add)
        io.open(OVF, "w", encoding="utf-8", newline="\n").write(t)
    print("✅ 已写 %s（新增 %d 条；备份 %s）" % (OVF, len(add), b))
    return 0


if __name__ == "__main__":
    sys.exit(main())
