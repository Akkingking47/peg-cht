#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补 `RM_usvsruss6v.txt` 的 2 处 Tarnopol —— **漏掉的第 7 个同族文件**。

依据：`work/glossary/faction_place_audit.py` 报出的 2 处真阳性
      （`glossary/evidence/faction-place-audit.txt`）。

同族 6 个（`119.TXT` / `119V.txt` / `119tV.txt` / `RM_usvsruss14_i.txt` /
`US41BV.TXT` / `wdarrabv.txt`）已于 2026-10-12 由 `fix_faction_history.py`
修为「塔尔诺波尔」；本文件是**漏掉的第 7 个**。

## 先定范围（五条铁律之五：改同词前先定范围并全库扫残留）

全库（BK/OUT/GAME）扫两种写法 —— 含「捷尔诺波尔」共 **5** 个文件，
逐一看**视角判定**后**只有本文件**是德方视角：

| 文件 | 视角 | 来源 | 处置 |
|---|---|---|---|
| `RM_usvsruss6v.txt` | **德** | 同场景 | ⭐ **本批要改**（注册表授权德方=「塔尔诺波尔」） |
| `SALERNO2_u.txt` | 盟 | scn国别 | 跳过 —— 注册表**无「盟」条目**，该 ID 不进检查 |
| `salerno2-R_u.txt` | 盟 | scn国别 | 跳过 —— 同上 |
| `USSR5_u.txt` | 未判定 | — | 跳过 —— 名单类(`_u`)；苏方剧本，现行译名不违和 |
| `invsion_m.txt` | 未判定 | — | 跳过 —— 名单类(`_m`) |

⇒ **只改这 1 个文件 2 行，不做全库替换。**（`塔尔诺波尔` 一侧 7 个文件全部已合规）

## 机制

走 `pegww2/research/_scn-file-overrides.tsv`（per-file 覆盖表）——
`gen_scn.py` 第 132–140 行按「子目录+文件名+行号」定点改写，**优先级高于整串键控**，
因此不会误伤别处同名正文（W17/W21 教训）。

**本脚本只写覆盖表，不碰游戏目录**（铁律三：备份与覆盖分两条命令）。
落盘由 `deploy_tarnopol_6v.py` 在**临时目录重建 → 回读校验 → 才写正式**。

用法: python fix_tarnopol_6v.py [--apply]
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
COPYBK = os.path.join(WS, "backup", "before-tarnopol-6v")

# (文件, 0-based 行号, 现用, 改为)
EDITS = [
    ("RM_usvsruss6v.txt", 0, "捷尔诺波尔", "塔尔诺波尔"),
    ("RM_usvsruss6v.txt", 1, "捷尔诺波尔", "塔尔诺波尔"),
]


def main():
    apply_ = "--apply" in sys.argv
    rows, show = [], []
    for fn, idx, old, new in EDITS:
        pb, pg = os.path.join(BK, fn), os.path.join(GAME, fn)
        if not os.path.isfile(pb) or not os.path.isfile(pg):
            print("   ⛔ 缺文件：%s / %s" % (pb, pg))
            return 1
        en = io.open(pb, encoding="cp1252", errors="replace").read().split("\n")
        zh = io.open(pg, encoding="gbk", errors="replace").read().split("\n")
        if idx >= len(zh) or old not in zh[idx]:
            print("   ⚠️ 跳过 %s 行%d：未见「%s」（现值 %r）" % (fn, idx, old, zh[idx] if idx < len(zh) else None))
            continue
        if len(en) != len(zh):
            print("   ⛔ %s 行数不一致（BK %d / GAME %d）" % (fn, len(en), len(zh)))
            return 1
        nl = zh[idx].replace(old, new)
        rows.append(("SCENARIO", fn, str(idx), en[idx], nl))
        show.append((fn, idx, zh[idx], nl, en[idx]))
    print("=" * 96)
    print("Tarnopol 第 7 个同族文件 · 待落 per-file 覆盖 %d 条" % len(rows))
    print("=" * 96)
    for fn, idx, a, b, e in show:
        print("   %-22s 行%-3d 原文 %r" % (fn, idx, e))
        print("   %-22s      %s → %s" % ("", a, b))
    if not rows:
        print("\n⚠️ 无待写条目（已做过？）")
        return 0
    if not apply_:
        print("\n（dry-run；加 --apply 才写覆盖表）")
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
    # 回读校验
    back = io.open(OVF, encoding="utf-8").read()
    miss = [r for r in rows if "\t".join(r[:3]) + "\t" not in back]
    print("✅ 已写 %s（新增 %d 条 · 已有 %d 条；备份 %s）" % (OVF, len(add), len(rows) - len(add), b))
    print("   回读校验 %s" % ("✅ 通过" if not miss else "❌ 缺 %d 条" % len(miss)))
    return 0 if not miss else 1


if __name__ == "__main__":
    sys.exit(main())
