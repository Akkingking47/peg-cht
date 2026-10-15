#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景列表「分组编号」提案生成器（**只读，不写游戏目录/真源**）。

产物：pegww2\research\_场景列表分组编号提案.tsv
判据：
  · 列表成员 = .SCN@0 == 0
  · 组内排序键 = _m.txt 行0 的**英文原名**按 cp1252 字节序（= 汉化前列表本来顺序）
  · 战场组 = 优先按**场景自身内容**；地图名仅作线索（本作存在一图多用，故**冲突项必须人工裁决**）
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
S = os.path.join(G, "SCENARIO")
U = os.path.join(G, "USERSCEN")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
OUT = os.path.join(WS, "pegww2", "research", "_场景列表分组编号提案.tsv")

# 地图 → 主战场（仅作线索；冲突项在 CONFLICT 里单列）
MAPGROUP = {
    "西线/西北欧": ["CAEN", "STLO", "ARRACT", "SEDAN", "METZ", "WINDSOR", "DUNKIRK",
                    "NORDWIND", "REMAGEN", "MADRID", "EURORMY", "LILLEHAM", "OAKRIDGE"],
    "东线": ["KONRAD", "KANEV", "KISHINEV", "KLIN", "VIIPURI", "LENIN", "NOVGOROD",
             "PROKHORV", "SEELOW", "SOUMUSSA", "VOLOKOL", "DESSAU", "CIECHANO", "CHIR"],
    "北非·地中海·意大利": ["SALERNO", "MALTA", "GARAMLAH", "RATOBRUK", "PTOBRUK",
                            "GREECE", "SAVANNAH", "TOBRUK"],
}
# ⚠️ 地图名与场景内容矛盾的条目（必须人工裁决，不能靠地图归组）
CONFLICT = {
    "saturn": "说明=朱可夫被击败（东线），但英文名栏='Windsor PeG:WW2'、地图=CHIR",
    "saturn-R": "说明=开赴诺曼底（西线），地图=CHIR（东线）",
    "windsor1": "说明=德军入侵冰岛（北欧），地图=WINDSOR；英文名栏=Windsor 1943 PeG:WW2",
    "windsor1-R": "说明=德军入侵冰岛（北欧），英文名栏=Kiev encirclement - Romny（东线）",
    "lah_it_ngran": "说明=「格兰」行动（北非昔兰尼加），地图=GARAMLAH；英文名栏='Message from:-'",
    "Red": "说明=红色浪潮涌起/1945 年，地图=DESSAU",
    "prok1-R": "说明=堡垒行动 1943-07-05，英文名栏=段落，地图=PROKHORV",
    "viipuri-R": "说明=维堡：重制版 1944-06-15，英文名栏=段落",
}


def fld(b, o, n=20):
    return b[o:o + n].split(b"\x00")[0].decode("latin-1")


def readtext(p, enc):
    t = open(p, "rb").read()
    if p.lower().endswith(".ply"):
        t = t.split(b"\x00")[0]
    return t.decode(enc, "replace")


def main():
    rows = []
    for d in (S, U):
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".scn"):
                continue
            b = open(os.path.join(d, fn), "rb").read()
            if len(b) < 11350 or b[0] != 0:
                continue
            stem = fn[:-4]
            en = zh = "(缺 _m.txt)"
            for c in (stem + "_m.txt", stem.upper() + "_m.txt"):
                pb = os.path.join(BK, c)
                if os.path.isfile(pb):
                    en = re.split(r"\r\n|\r|\n", readtext(pb, "cp1252"))[0].strip()
                pg = os.path.join(d, c)
                if os.path.isfile(pg):
                    zh = re.split(r"\r\n|\r|\n", readtext(pg, "gbk"))[0].strip()
            rows.append(dict(stem=stem, en=en, zh=zh, mp=fld(b, 11210).upper().replace(".MAP", "")))

    buckets = {g: [] for g in MAPGROUP}
    for r in rows:
        g = next((k for k, v in MAPGROUP.items() if r["mp"] in v), None)
        if g is None:
            g = "⚠️ 未归组"
            buckets.setdefault(g, [])
        buckets[g].append(r)

    out = ["# 「进行场景」列表 —— 按战场主题分组 + 组内序号（提案 · 未执行）",
           "# 列表成员＝.SCN@0==0；组内序号＝_m.txt 行0 英文原名 cp1252 字节序（＝汉化前列表本来顺序）",
           "# 战场组优先按场景内容；地图名仅线索 —— 本作存在一图多用，冲突项已在备注标出，须人工裁决",
           "# 组\t序号\tstem\t英文原名(排序键)\t现行中文名\t地图\t备注"]
    total = 0
    for g in ("西线/西北欧", "东线", "北非·地中海·意大利", "⚠️ 未归组"):
        if g not in buckets:
            continue
        buckets[g].sort(key=lambda r: r["en"].encode("cp1252", "replace"))
        for i, r in enumerate(buckets[g], 1):
            total += 1
            note = []
            if r["stem"] in CONFLICT:
                note.append("⚠️ 需裁决：" + CONFLICT[r["stem"]])
            if r["en"].startswith("(缺"):
                note.append("⚠️ 无 _m.txt（实机无名栏）")
            if r["stem"] in ("ATM_scn29", "ATM_scn34"):
                note.append("⚠️ 空壳（无 _m.txt 且说明文件缺失，建议不入列表）")
            out.append("%s\t%s-%02d\t%s\t%s\t%s\t%s\t%s" % (
                g, g[:2].upper(), i, r["stem"], r["en"][:70], r["zh"][:30], r["mp"], " ".join(note)))
    open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("已写 %s" % OUT)
    print("总计 %d 条" % total)
    for g in buckets:
        print("  %-18s %d" % (g, len(buckets[g])))
    print("\n⚠️ 需人工裁决的条目：")
    for k, v in CONFLICT.items():
        print("   %-14s %s" % (k, v))


if __name__ == "__main__":
    main()
