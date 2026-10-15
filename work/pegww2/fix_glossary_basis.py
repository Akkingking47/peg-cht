#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""订正**术语基准表**（`peg/research/ui-glossary.tsv`）：把 2026-10-12 的裁决写回真源。

改动（用户 2026-10-12 批准）：
  · 行 112 `Profile`      概况 → **轮廓**（原「概况」通俗化过头 ⇒ 义失）
  · 行 164 原重复的 Profile 行 ⇒ 改写为 `Sharpshooter 精准射手`
  · 追加 `Marksman 神射手` 行（与 Sharpshooter 明确区分，防再次撞名）

用法: python fix_glossary_basis.py [--apply]
"""
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
P = os.path.join(WS, "peg", "research", "ui-glossary.tsv")
BK = os.path.join(WS, "backup", "glossary-before-profile-fix", "ui-glossary.tsv")

R112 = "Profile\t轮廓\t数值\t机制\t★2026-10-12 订正（原「概况」通俗化过头、义失）；原文＝单位轮廓/曝露度"
R164 = "Sharpshooter\t精准射手\t指挥官技能\t机制\t★2026-10-12 订正（原「神射手」与 Marksman 撞名）；手册：远程射击不减半"
ADD = "Marksman\t神射手\t指挥官技能\t机制\t与 Sharpshooter（精准射手）区分"


def main():
    lines = open(P, encoding="utf-8").read().split("\n")
    plan = []
    for i, l in enumerate(lines):
        c = l.split("\t")
        if not c or not c[0].strip():
            continue
        if i == 111 and c[0].strip() == "Profile":
            plan.append((i, l, R112))
        elif i == 163 and c[0].strip() == "Profile":
            plan.append((i, l, R164))
    print("=== 基准表订正计划 %d 条 + 追加 1 条 ===" % len(plan))
    for i, old, new in plan:
        print("  行%-4d 旧: %s" % (i + 1, old[:60]))
        print("         新: %s" % new[:88])
    print("  追加: %s" % ADD)
    if "--apply" not in sys.argv:
        print("\n（dry-run；加 --apply）")
        return 0
    os.makedirs(os.path.dirname(BK), exist_ok=True)
    if not os.path.isfile(BK):
        shutil.copy2(P, BK)
    for i, old, new in plan:
        assert lines[i] == old, "行%d 已变" % (i + 1)
        lines[i] = new
    lines.append(ADD)
    open(P, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("  ✅ 已写 %s（备份 %s）" % (P, BK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
