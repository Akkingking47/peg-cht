#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**Łódź 年代判定落地**（用户 2026-10-12：按场景年代定）。

Łódź 的德方名字随年代变：
  · 1939 年 9 月德占初期 ⇒ 仍作 **Lodsch**（中文惯译「罗兹」）
  · **1940 年 4 月**起 ⇒ 改名 **Litzmannstadt**（利茨曼施塔特）

逐个核对结果：
| 文件 | 场景/年代 | 判定 |
|---|---|---|
| `112.txt`（行3） | **1939 年 9 月**，党卫军装甲军入侵波兰 | **保持「罗兹」** ✔ 年代正确 |
| `DAK_Choice_m.txt`（行126） | DAK 战役抉择屏（该族简报 1940-05 ~ 1942-11） | 改 **利茨曼施塔特** |
| `DAK_SPChoice_m.txt`（行90） | 同上 | 改 **利茨曼施塔特** |
| `DAK_Choice_m.txt`（行139） | ⚠️ 实为 **Grozny（格罗兹尼）**，是审计子串误命中 | **不动**（审计已修） |
| `DAK_SPChoice_m.txt`（行174） | ⚠️ 同上 | **不动** |

用法: python fix_lodz_era.py [--apply]
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
CBK = os.path.join(WS, "backup", "before-lodz-era")
EDITS = [("DAK_Choice_m.txt", 125, "罗兹", "利茨曼施塔特"),
         ("DAK_SPChoice_m.txt", 89, "罗兹", "利茨曼施塔特")]


def main():
    apply_ = "--apply" in sys.argv
    rows, show = [], []
    for fn, idx, old, new in EDITS:
        en = io.open(os.path.join(BK, fn), encoding="cp1252", errors="replace").read().split("\n")
        zh = io.open(os.path.join(GAME, fn), encoding="gbk", errors="replace").read().split("\n")
        if idx >= len(zh) or zh[idx].strip() != old:
            print("   ⚠️ 跳过 %s idx%d：现值=%r（期望 %r）" % (fn, idx, zh[idx] if idx < len(zh) else None, old))
            continue
        rows.append(("SCENARIO", fn, str(idx), en[idx], new))
        show.append((fn, idx, en[idx], zh[idx], new))
    print("=== 待落 %d 条 ===" % len(rows))
    for fn, idx, a, b, c in show:
        print("   %s idx%d  英=%r  %s → %s" % (fn, idx, a, b, c))
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0
    t = io.open(OVF, encoding="utf-8").read()
    have = {tuple(l.split("\t")[:3]) for l in t.split("\n") if not l.startswith("#")}
    add = [r for r in rows if tuple(r[:3]) not in have]
    os.makedirs(CBK, exist_ok=True)
    b = os.path.join(CBK, os.path.basename(OVF))
    if not os.path.isfile(b):
        shutil.copy2(OVF, b)
    if add:
        if not t.endswith("\n"):
            t += "\n"
        t += "".join("\t".join(r) + "\n" for r in add)
        io.open(OVF, "w", encoding="utf-8", newline="\n").write(t)
    print("✅ 已写 %s（新增 %d 条）" % (OVF, len(add)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
