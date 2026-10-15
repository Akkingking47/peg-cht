#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用户 2026-10-12 裁决执行：**争议术语以界面层为准** ＋ 战斗记录统一「击毁」。

裁决：
  A. 术语以**界面层**为准（更贴合游戏叙事与玩家理解）
     · `River Assault`    强渡 → **渡河突击**（界面层既有值）
     · `Ground Taker`     地面占领者 → **攻坚专家**
     · `Ranger`           突击队员 → **突击队**（改基准表，界面层既有值）
     · `Indirect Defense` 远程防御（界面层既有值，无需改）
  B. 战斗记录组统一**击毁**：`Tactical Air Killed` 战术空军击杀 → **击毁战术空军**

⚠️ **只改原文对得上的行**（用户要求"从原文译文对照入手"）：
   · 只有原文含 `river assault` 的行才把「强渡」换成「渡河突击」；
     原文不含的那些（`Warta Crossing`＝强渡瓦尔塔河、`Dniepr Crossing`）**一律保留**——
     那里的「强渡」是"渡河"这个动词义，不是 `River Assault` 这个特种装备名。

用法: python apply_term_rulings.py [--apply]
"""
import io
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
FILL = os.path.join(WS, "pegww2", "docs-zh", "_fill")
DOCS_TERM = os.path.join(WS, "pegww2", "docs-zh", "_翻译须知与术语.md")
PRES = os.path.join(WS, "peg", "research")
BK = os.path.join(WS, "backup", "before-term-rulings")

RIVER_EN = re.compile(r"river\s*assault", re.I)


def plan_fills():
    plan = []
    for dp, _, fs in os.walk(FILL):
        for f in fs:
            if f.startswith("_") or not f.endswith(".tsv") or f.endswith(".cells.tsv"):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, FILL)
            ls = open(p, encoding="utf-8").read().split("\n")
            for i, l in enumerate(ls):
                if l.startswith("#") or l.split("\t")[0].strip() in ("行号", "段号"):
                    continue
                c = l.split("\t")
                if len(c) < 3:
                    continue
                en, zh = c[1], c[-1]
                new = zh
                if RIVER_EN.search(en) and "强渡" in zh:
                    new = zh.replace("强渡", "渡河突击")
                if en.strip().startswith("Ground Taker") and "地面占领者" in zh:
                    new = new.replace("地面占领者", "攻坚专家")
                if new != zh:
                    nc = list(c)
                    nc[-1] = new
                    plan.append((p, rel, i, l, "\t".join(nc), en.strip()[:46]))
    return plan


def main():
    apply_ = "--apply" in sys.argv
    plan = plan_fills()
    print("=== A/B 类：译表改动 %d 处（涉及 %d 份）===" % (len(plan), len({x[0] for x in plan})))
    for p, rel, i, old, new, en in plan[:8]:
        print("   %-44s 行%-6d 原:%-34s → %s" % (rel[-44:], i, en, new.split("\t")[-1].strip()[:40]))
    if len(plan) > 8:
        print("   …（其余 %d 处同类）" % (len(plan) - 8))

    # 术语表 + 基准表 + 界面表
    extra = []
    for p, pat, old, new in (
        (DOCS_TERM, None, "| River Assault（原 Bridging） | 强渡 |", "| River Assault（原 Bridging） | 渡河突击 |"),
        (os.path.join(PRES, "ui-glossary.tsv"), None, "Ranger\t突击队员\t编制\t军语\t—", "Ranger\t突击队\t编制\t军语\t★2026-10-12 裁决：以界面层为准（行596＝突击队）"),
    ):
        if os.path.isfile(p):
            t = open(p, encoding="utf-8").read()
            if old in t:
                extra.append((p, old, new))
    # 界面表：战斗记录统一击毁
    p = os.path.join(RES, "WW2Gui-map.tsv")
    for l in open(p, encoding="utf-8-sig"):
        c = l.rstrip("\n").split("\t")
        if c and c[0].strip() == "499" and len(c) >= 3 and c[2].strip() == "战术空军击杀":
            extra.append((p, l.rstrip("\n"), "\t".join(c[:2] + ["击毁战术空军"] + c[3:])))
    print()
    print("=== 另需改动的表 %d 处 ===" % len(extra))
    for p, old, new in extra:
        print("   %-22s %s → %s" % (os.path.basename(p), old.strip()[:44], new.strip()[:48]))
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0

    os.makedirs(BK, exist_ok=True)
    for path in {x[0] for x in plan} | {x[0] for x in extra}:
        b = os.path.join(BK, os.path.basename(path))
        if not os.path.isfile(b):
            shutil.copy2(path, b)
    for path in {x[0] for x in plan}:
        ls = open(path, encoding="utf-8").read().split("\n")
        for pp, rel, i, old, new, en in plan:
            if pp == path:
                assert ls[i] == old, "行%d 已变" % i
                ls[i] = new
        open(path, "w", encoding="utf-8", newline="\n").write("\n".join(ls))
    for path, old, new in extra:
        t = open(path, encoding="utf-8").read()
        assert old in t, "未命中：%s" % old[:40]
        open(path, "w", encoding="utf-8", newline="\n").write(t.replace(old, new, 1))
    print("\n✅ 已改 %d 份译表 + %d 个表项；备份 → %s" % (len({x[0] for x in plan}), len(extra), BK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
