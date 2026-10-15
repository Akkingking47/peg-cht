#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成本作（PeG / PeG-WW2）的人工术语表，供总库构建器并入。

产出：`work/glossary/pegww2-glossary.tsv`
     列：`en | zh | cat | scope | src`（构建器再补 status/conf/zh_in）

**为什么要单独生成而不是手写**：内容来自三处真源，可重跑、可审计：
  · `peg/research/ui-glossary.tsv`        → 界面/机制术语（207 条，含裁决订正）
  · `pegww2/docs-zh/_翻译须知与术语.md`    → 文档层术语（面向玩家手册）
  · 本脚本内**手工登记**的：装备牵引后缀族、装备特性名、战斗记录组、装备名订正

⚠️ 新 scope（`PEGWW2_UI` / `PEGWW2_DOCS` / `PEGWW2_EQP`）与既有
   `EFILE_OLGWW2/OPENPG/NASHORNPBEM` **并列，互不覆盖** —— 总库是「按 scope 分列」的，
   同一英文在不同 scope 合法有不同译法（例：`Air Transport` 在 OLGWW2 是**运输机**，
   在本作是**空运**这个动作；`Ranger` 在 OLGWW2 是**游骑兵**（美军），本作是**突击队**）。

用法: python make_pegww2_glossary.py [--apply]
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
UI = os.path.join(WS, "peg", "research", "ui-glossary.tsv")
DOCS = os.path.join(WS, "pegww2", "docs-zh", "_翻译须知与术语.md")
DST = os.path.join(WS, "work", "glossary", "pegww2-glossary.tsv")

CAT = {"兵种": "UNIT", "编制": "UNIT", "装备名": "EQUIP", "舰艇": "EQUIP", "阵营": "NATION"}

# —— 手工登记（有据可查，见 pegww2/方法/术语统一-治本.md 与 research/_同类译法问题-审计.md）——
SUFFIX = [  # 装备牵引后缀族（德语/法语/波兰语/俄语/芬兰语/匈牙利语…同一语义）
    ("w/Truck", "卡车牵引"), ("w/Camion", "卡车牵引"), ("w/LKW", "卡车牵引"),
    ("w/Gruzovik", "卡车牵引"), ("w/Ciezarowka", "卡车牵引"), ("w/Teherkocsi", "卡车牵引"),
    ("w/Kuorma", "库尔马卡车牵引"), ("w/Kuoma", "库尔马卡车牵引"),
    ("w/Wagon", "马车牵引"), ("w/Charrette", "马车牵引"), ("w/Szeker", "马车牵引"),
    ("w/Vogn", "马车牵引"), ("w/Vagon", "马车牵引"),
    ("w/Pferden", "骡马牵引"),          # ← 2026-10-12 由「马拉」订正：同族一律「XX牵引」
    ("w/Carro", "车辆牵引"), ("w/Jeep", "吉普车牵引"), ("w/Krad", "摩托车牵引"),
    ("w/M", "M3A1 运载"), ("w/Bren", "布伦机枪车运载"),
]
SPECIALS = [  # 特种装备名（PFS: EQUIPMENT SPECIAL ABILITIES）
    ("Ignore Entrenchments", "无视工事"), ("Bridging Engineers", "架桥工兵"),
    ("Paratroop", "伞兵"), ("Deploy and Supply", "部署与补给"),
    ("River Assault", "渡河突击"), ("Light Infantry", "轻步兵"),
    ("Destroys Entrenchments", "摧毁工事"), ("Entrenches Quickly", "快速构筑工事"),
]
BATTLE = [  # 战斗记录组（PFS: UNIT BATTLE RECORD LABELS）—— 组内统一「击毁」
    ("Air Defense Killed", "击毁防空"), ("Anti-tank Killed", "击毁反坦克"),
    ("Artillery Killed", "击毁炮兵"), ("Infantry Killed", "击毁步兵"),
    ("Recon Killed", "击毁侦察"), ("Tanks Killed", "击毁坦克"),
    ("Tactical Air Killed", "击毁战术空军"),   # ← 2026-10-12 由「战术空军击杀」订正
    ("Planes Killed", "击落飞机"),             # 飞机用「击落」，同组唯一例外（正确搭配）
    ("Kills", "击毁数"),
]
EQP_FIX = [("Elefant", "象式"), ("Ferdinand", "斐迪南")]   # ← 两单位不再同名


def main():
    rows, seen = [], set()

    def add(en, zh, cat, scope, src):
        en, zh = en.strip(), zh.strip()
        if not en or not zh or (en, scope) in seen:
            return
        seen.add((en, scope))
        rows.append((en, zh, cat, scope, src))

    # A. 界面/机制术语
    nA = 0
    if os.path.isfile(UI):
        for l in io.open(UI, encoding="utf-8-sig"):
            if l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 3 and c[0].strip() and c[1].strip():
                add(c[0], c[1], CAT.get(c[2].strip(), "TERM"), "PEGWW2_UI", "ui")
                nA += 1
    # B. 文档层术语（markdown 表格）
    nB = 0
    if os.path.isfile(DOCS):
        for l in io.open(DOCS, encoding="utf-8"):
            m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", l)
            if not m or m.group(1).strip() in ("英文", "---"):
                continue
            en = re.sub(r"[（(][^）)]*[）)]\s*$", "", m.group(1).strip())
            if en and not en.startswith("-"):
                add(en, m.group(2), "TERM", "PEGWW2_DOCS", "docs")
                nB += 1
    # C/D/E/F. 手工登记
    for en, zh in SUFFIX:
        add(en, zh, "TERM", "PEGWW2_EQP", "equip:suffix")
    for en, zh in EQP_FIX:
        add(en, zh, "EQUIP", "PEGWW2_EQP", "equip")
    for en, zh in SPECIALS + BATTLE:
        add(en, zh, "TERM", "PEGWW2_UI", "ui")
    print("界面术语 %d · 文档术语 %d · 后缀 %d · 装备订正 %d · 特性+战斗记录 %d ⇒ 去重后 %d 条"
          % (nA, nB, len(SUFFIX), len(EQP_FIX), len(SPECIALS + BATTLE), len(rows)))
    for scope in ("PEGWW2_UI", "PEGWW2_DOCS", "PEGWW2_EQP"):
        print("   %-14s %d 条" % (scope, sum(1 for r in rows if r[3] == scope)))
    if "--apply" not in sys.argv:
        print("（dry-run；加 --apply 写 %s）" % DST)
        return 0
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with io.open(DST, "w", encoding="utf-8", newline="\n") as f:
        f.write("en\tzh\tcat\tscope\tsrc\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    print("已写 %s" % DST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
