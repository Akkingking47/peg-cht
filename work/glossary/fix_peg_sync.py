#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**前作 PeG 同步**：把本作（PeG-WW2）的裁决回改到前作 `gen_gui030_zh.py`（用户 2026-10-12 批准）。

改 5 处（真源是脚本内的 `ZH` 字典；`gui030-zh.tsv` 是产出）：

| 行 | 原文 | 现值 → 改为 | 依据 |
|---|---|---|---|
| 95  | `Profile`                      | 概况 → **轮廓** | 原文＝单位轮廓/曝露度；与本作一致 |
| 259 | `Set Prestige`                 | 设置声望 → **设置威望** | Prestige 统一「威望」；⚠️ 脚本 BANNED 已列「声望」但**整串精确匹配**漏了这两条 |
| 261 | `Prestige Allocated Per Turn`  | 每回合分配声望 → **每回合分配威望** | 同上 |
| 307 | `Sharpshooter`                 | 神射手 → **精准射手** | 与本作一致；解开与 Marksman 的撞名（前作有 Airforce Marksman/Marksman 之分，行295 是 `Airforce Marksman`≠本作行295） |
| 488 | `Air Missions`                 | 出击次数 → **空中任务** | 与本作一致（面板/资源名 ⇒ 空中任务）。⚠️ 前作注释曾按"动作"归入「出击」，本次按用户裁决「以本作界面层为准」统一 |

用法: python fix_peg_sync.py [--apply]
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
P = os.path.join(WS, "work", "peg", "gen_gui030_zh.py")
BK = os.path.join(WS, "backup", "before-peg-prevsync")

EDITS = [
    (r'94: "远程防御", 95: "概况"', r'94: "远程防御", 95: "轮廓"'),
    (r'259: "设置声望"', r'259: "设置威望"'),
    (r'261: "每回合分配声望"', r'261: "每回合分配威望"'),
    (r'307: "神射手"', r'307: "精准射手"'),
    (r'488: "出击次数"', r'488: "空中任务"'),
    # 留痕：把 488 从"动作"清单里挪出来，并说明依据
    (r'#      `取消全部出击`、513 `出击中止！`、597/598 `执行已规划的出击`·`不执行任何出击`',
     '#      `取消全部出击`、513 `出击中止！`、597/598 `执行已规划的出击`·`不执行任何出击`\n'
     '#    ⚠️ 2026-10-12 前作同步：488 `Air Missions` 由「出击次数」改「空中任务」——\n'
     '#       依据用户裁决「争议术语以**本作界面层**为准」（本作行488 同用途＝空中任务）。'),
]


def main():
    apply_ = "--apply" in sys.argv
    t = io.open(P, encoding="utf-8").read()
    plan = []
    for old, new in EDITS:
        if old not in t:
            print("   ⚠️ 未命中：%s" % old[:60])
            continue
        if t.count(old) != 1:
            print("   ⚠️ 命中多次（%d），跳过：%s" % (t.count(old), old[:50]))
            continue
        plan.append((old, new))
    print("=== 前作同步改动 %d 处 ===" % len(plan))
    for old, new in plan:
        print("   %s\n     → %s" % (old.strip()[:88], new.strip().split("\n")[-1][:88]))
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0
    os.makedirs(BK, exist_ok=True)
    b = os.path.join(BK, os.path.basename(P))
    if not os.path.isfile(b):
        shutil.copy2(P, b)
        print("  备份 → %s" % b)
    for old, new in plan:
        t = t.replace(old, new, 1)
    io.open(P, "w", encoding="utf-8", newline="\n").write(t)
    print("✅ 已写 %s" % P)
    return 0


if __name__ == "__main__":
    sys.exit(main())
