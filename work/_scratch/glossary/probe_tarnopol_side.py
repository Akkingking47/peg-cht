#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读探针：Tarnopol 两个中文名在**哪些文件**里出现，以及各文件的**视角**判定。

目的：改 `RM_usvsruss6v.txt` 之前先定范围（五条铁律之五）——
`捷尔诺波尔` 在 OUT/GAME 里出现在 5 个文件，必须逐一看视角，只改视角=德的那个。
"""
import os
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\glossary")
import faction_place_audit as F  # noqa: E402

TARGETS = ["RM_usvsruss6v.txt", "SALERNO2_u.txt", "USSR5_u.txt", "invsion_m.txt",
           "salerno2-R_u.txt", "119.TXT", "119V.txt", "119tV.txt", "LAH_IT_14_i.txt",
           "RM_usvsruss14_i.txt", "US41BV.TXT", "wdarrabv.txt"]

data = F.load_scenarios()
pin = F.load_pin()
side, origin, voice = F.resolve_sides(data, pin)

print("=" * 104)
print("Tarnopol 中文名分布 × 视角判定   （数据源：BK=testbed/backup/SCENARIO，GAME=%s）" % F.GAME)
print("=" * 104)
print("%-22s %-5s %-12s %-6s %-5s %s" % ("文件", "视角", "来源", "名单类", "口吻", "本文件含"))
for fn in TARGETS:
    if fn not in data:
        print("%-22s ⛔ 不在扫描集（BK 或 GAME 缺）" % fn)
        continue
    zh = data[fn][1]
    mark = ("捷" if "捷尔诺波尔" in zh else "·") + ("塔" if "塔尔诺波尔" in zh else "·")
    print("%-22s %-5s %-12s %-6s %-5s %s" % (
        fn, side.get(fn, "—"), origin.get(fn, "—"),
        "是" if F.is_list_file(fn) else "否", voice.get(fn, "—"), mark))

print("\n=== 注册表授权（glossary/layers/faction-places.tsv 中 ID=Tarnopol）===")
per_p, en2p, zh2p, nat_p, era_p = F.load_registry("faction-places.tsv", 0, 1, 3, 4)
tbl = per_p.get("Tarnopol", {})
for f, zh in tbl.items():
    print("   视角=%-3s 授权中文=%s" % (f, zh))
print("   ⚠️ 无「盟」条目 ⇒ 盟视角该 ID **不进检查**（`ok` 为空即 continue）")

print("\n=== 逐文件：是否会被审计报出 ===")
for fn in TARGETS:
    if fn not in data:
        continue
    f = side.get(fn)
    zh = data[fn][1]
    ok = {x for x in tbl.get(f, "").split("|") if x} if f else set()
    used = "捷尔诺波尔" if "捷尔诺波尔" in zh else ("塔尔诺波尔" if "塔尔诺波尔" in zh else "—")
    if not f:
        verdict = "跳过（无视角）"
    elif not ok:
        verdict = "跳过（该视角无授权条目）"
    elif used in ok or used == "—":
        verdict = "✅ 合规"
    else:
        verdict = "❌ 会报出（授权=%s）" % "|".join(sorted(ok))
    print("   %-22s %s" % (fn, verdict))
