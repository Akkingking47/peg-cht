#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""撤回 tier-4（scn国别）误判造成的误改 + 建立**人工视角钉**。

事件：`oakridge-R_m.txt` 的标题是「西线-23 华沙-波兹南行动 (**RTB#30**)」——
  **RTB＝通往柏林＝苏军战役** ⇒ 苏方视角，用波方名「波兹南」**本来就对**。
  但 `.scn` @22=3（德）⇒ tier-4 兜底把该文件判成德方 ⇒ 我据此误改了 3 行。
教训：**tier-4 的语义是"场景国别"，不等于"谁的文本"**（德苏对战场景里 @22 常是敌方/主方）。
⇒ ① 撤回该文件被误改的 3 行（保留原有"标题"覆盖）；
   ② 新增 `glossary/layers/side-override.tsv`（人工视角钉）优先于 tier-4。

用法: python fix_side_override.py [--apply]
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
SIDE = os.path.join(WS, "glossary", "layers", "side-override.tsv")
CBK = os.path.join(WS, "backup", "before-side-override")
DROP = {("SCENARIO", "oakridge-R_m.txt", "6"), ("SCENARIO", "oakridge-R_m.txt", "10"),
        ("SCENARIO", "oakridge-R_m.txt", "24")}
PINS = [
    ("oakridge-R", "苏", "标题含 `RTB#30`（Road to Berlin＝苏军战役）；`.scn` @22=3 是德方/主方索引，不代表文本视角"),
]


def main():
    apply_ = "--apply" in sys.argv
    lines = io.open(OVF, encoding="utf-8").read().split("\n")
    keep, dropped = [], []
    for l in lines:
        c = l.split("\t")
        if len(c) >= 3 and (c[0], c[1], c[2]) in DROP:
            dropped.append(l)
            continue
        keep.append(l)
    print("=== ① 待撤回 %d 条 ===" % len(dropped))
    for l in dropped:
        print("   %s" % l[:96])
    print("\n=== ② 待新增视角钉 %d 条 ===" % len(PINS))
    for stem, f, why in PINS:
        print("   %-14s → %s（%s）" % (stem, f, why[:52]))
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0
    os.makedirs(CBK, exist_ok=True)
    b = os.path.join(CBK, os.path.basename(OVF))
    if not os.path.isfile(b):
        shutil.copy2(OVF, b)
    io.open(OVF, "w", encoding="utf-8", newline="\n").write("\n".join(keep))
    print("✅ 覆盖表已撤回（剩 %d 行）" % len(keep))
    if not os.path.isfile(SIDE):
        with io.open(SIDE, "w", encoding="utf-8", newline="\n") as w:
            w.write("# 人工视角钉（**人工维护**）：优先于自动判定的三层 + `.scn` 国别兜底\n")
            w.write("# 用途：纠正『场景国别 ≠ 文本视角』造成的误判\n")
            w.write("# 列：stem(或前缀) | 阵营 | 依据\n")
            for stem, f, why in PINS:
                w.write("%s\t%s\t%s\n" % (stem, f, why))
        print("✅ 已建 %s" % SIDE)
    else:
        print("（视角钉文件已存在，未覆盖）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
