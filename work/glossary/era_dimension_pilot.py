#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**年代维度 · 试点落地**（用户 2026-10-12 问：「词库这些翻译是否可以按年代划分？有没有必要？」）

结论（有证据）：**有必要，但只对"同阵营、跨年代改名/改编制"的少数条目**——
  · 不同阵营的叫法差异（`Danzig`德/`Gdańsk`波、`Viipuri`芬/`Vyborg`苏）**已由「阵营」维度覆盖**，无需年代；
  · **同阵营跨年代改名**才是真缺口：`Lodz`（德方 1939=Lodsch／1940-04 起=Litzmannstadt）、
    `Königsberg`（苏方 1945 仍用 Кёнигсберг）→`Kaliningrad`（1946+）；
  · 场景年代可提取率实测 **22%**（690/3073）⇒ 年代检查只能是**提示级**（有年代就查，没有就跳过）。

本脚本：
 ① 把 `faction-places.tsv` 的「时期」列**升级为机器可读判据**：`<1940-04` / `>=1940-04` / `*`
 ② 给审计器加**年代检查**（`faction_place_audit.py` 内实现，见其 `era_of()`/`check_era()`）
 ③ 输出试点报告

用法: python era_dimension_pilot.py [--apply]
"""
import io
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
PLACES = os.path.join(WS, "glossary", "layers", "faction-places.tsv")
CBK = os.path.join(WS, "backup", "before-era-dim")

# 年代判据写法（第 6 列「时期」）：`<YYYY-MM` / `>=YYYY-MM` / `*`（不适用/双方一致）
ERA_ROWS = {
    # (地名ID, 阵营) : (该方称法, 中文译名, 其它写法, 时期判据, 依据)
    ("Lodz", "德"): ("Litzmannstadt / Lodsch", "利茨曼施塔特|罗兹", "Litzmannstadt, Lodsch, Lodz",
                     ">=1940-04 → 利茨曼施塔特 ； <1940-04 → 罗兹",
                     "⭐年代双名：1939-09 波兰战役场景（如 112.txt）作「罗兹」；1940-04 后（如 DAK 抉择屏）作「利茨曼施塔特」"),
    ("Koenigsberg", "苏"): ("Кёнигсберг", "柯尼斯堡", "Koenigsberg", "<=1945 → 柯尼斯堡",
                            "苏方 1945 攻占时仍称 Кёнигсберг"),
    ("Kaliningrad", "苏"): ("Калининград", "加里宁格勒", "Kaliningrad", ">=1946 → 加里宁格勒",
                            "1946 年改名"),
}


def main():
    apply_ = "--apply" in sys.argv
    lines = io.open(PLACES, encoding="utf-8").read().split("\n")
    out, hit = [], 0
    for l in lines:
        c = l.split("\t")
        if len(c) >= 7 and (c[0], c[1]) in ERA_ROWS:
            nat, zh, alt, era, why = ERA_ROWS[(c[0], c[1])]
            l = "\t".join((c[0], c[1], nat, zh, alt, era, why))
            hit += 1
        out.append(l)
    print("=== 年代判据化：改写 %d 行（第 6 列「时期」现为机器可读）===" % hit)
    for (pid, fac), (nat, zh, alt, era, why) in ERA_ROWS.items():
        print("   %-14s %-3s 时期判据：%s" % (pid, fac, era))
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0
    os.makedirs(CBK, exist_ok=True)
    b = os.path.join(CBK, os.path.basename(PLACES))
    if not os.path.isfile(b):
        shutil.copy2(PLACES, b)
    io.open(PLACES, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("✅ 已写 %s（备份 %s）" % (PLACES, b))
    return 0


if __name__ == "__main__":
    sys.exit(main())
