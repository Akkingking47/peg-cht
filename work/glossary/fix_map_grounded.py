#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**按地图/编制复核后的改正**（用户 2026-10-12：「要结合使用的地图看，直接按词库既有翻译有错译风险」）。

复核方法：读该场景的 **地图名 + 英文原件 + 邻域国别/编制** 再定缩写。

【改正】
 ① `SATC` ×3 `DAK_SPS04_u.txt`（地图＝**蒙巴萨**，东非战役）：
    英文原件模式 `<号>/<上级>`（`1 R/SA`、`1 Br/SA`、`1 aaR/SA`）⇒ SATC 是**上级编成**
    ＝ **South African Tank Corps 南非装甲兵团**（南非国家档案馆有该编制档案）
    ⚠️ 原按词库作「南非**装甲运输**队」——错译，现改正
 ② `AASC` ×2 `tobruk-R_u.txt` / `RM_usvsruss19_i.txt`（地图＝**托布鲁克**）：
    同组 `1KDG/2`、`1KRR/2`、`1RHA/2`、`1RNF/2` **全为 `/2`＝英军第2装甲师**，而 AASC **无上级**；
    英军对应编制是 **RASC**（项目内查无 RASC）；AWM 那条 "HQ AASC … **2 Armoured Division**" 是**澳大利亚**的、
    号码巧合 ⇒ **两种读法（澳军勤务部队 / 英军编制笔误）都成立** ⇒ **撤回译文，保持拉丁**（宁可不译，不可错译）
 ③ `TNG`/`NG` `OAKRIDGE.TXT`（地图＝**西线-22 橡树岭**）：
    邻域地名 **哈里曼/煤田镇/马斯科特/勒努瓦城** 全在**田纳西州** ⇒ `TNG`＝**田纳西国民警卫队**、`NG`＝**国民警卫队**
    （原按词库"保留"⇒ 现按地图**译出**）
 ④ `HG师`/`HG D` `DAK_TU06_u.txt`（地图＝**突尼斯**）：同文件已有「赫尔曼·戈林师」⇒ 统一
 ⑤ `MTF` `RTB33_m.txt`（地图＝**敖德萨撤退**，四周全是村落名）⇒ 是**地名标注**：
    苏式地图常见 **МТФ（молочно-товарная ферма 乳牛场/畜牧场）** ⇒ 「畜牧场(MTF)」

【查过但维持原判】
 `SRAF`＝苏联空军 ✓（4 文件皆苏德战场，与苏军坦克旅同组）· `KTR 9`＝芬兰野战炮兵团 ✓（苏奥穆萨尔米）
 `XXI`＝第21军 ✓（第二次阿拉曼）· `ERY/FFY` ✓（敦刻尔克 1940；`/1R` 未确认⇒保留）
 `PSZ`（格洛斯特/海狮，波兰部队；词库体例＝后缀保留）· `TFH`/`HvH`/`Roz`（地图无法判定⇒保留）

用法: python fix_map_grounded.py [--apply]
"""
import io
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
CBK = os.path.join(WS, "backup", "before-map-grounded")
DROP = [("SCENARIO", "tobruk-R_u.txt", "29"), ("SCENARIO", "RM_usvsruss19_i.txt", "36")]
SET = [
    ("DAK_SPS04_u.txt", 39, "第1/南非装甲兵团"),
    ("DAK_SPS04_u.txt", 40, "第2/南非装甲兵团"),
    ("DAK_SPS04_u.txt", 41, "第3/南非装甲兵团"),
    ("OAKRIDGE.TXT", 80, "国民警卫队"),
    ("OAKRIDGE.TXT", 81, "国民警卫队"),
    ("OAKRIDGE.TXT", 82, "国民警卫队"),
    ("OAKRIDGE.TXT", 83, "田纳西国民警卫队"),
    ("OAKRIDGE.TXT", 84, "田纳西国民警卫队"),
    ("OAKRIDGE.TXT", 85, "田纳西国民警卫队"),
    ("DAK_TU06_u.txt", 62, "第1团/赫尔曼·戈林师"),
    ("DAK_TU06_u.txt", 63, "第2团/赫尔曼·戈林师"),
    ("RTB33_m.txt", 20, "畜牧场(MTF)"),
]


def main():
    apply_ = "--apply" in sys.argv
    t = io.open(OVF, encoding="utf-8").read()
    lines = t.split("\n")
    keep, dropped = [], []
    for l in lines:
        c = l.split("\t")
        if len(c) >= 3 and (c[0], c[1], c[2]) in DROP:
            dropped.append(l)
            continue
        keep.append(l)
    print("=== ① 撤回（保持拉丁）%d 条 ===" % len(dropped))
    for l in dropped:
        print("   %s" % l[:88])
    # 覆盖/新增 SET
    idx_map = {}
    for fn, i, zh in SET:
        idx_map[(fn, str(i))] = zh
    out, done = [], set()
    for l in keep:
        c = l.split("\t")
        if len(c) >= 5 and (c[1], c[2]) in idx_map:
            en = io.open(os.path.join(BK, c[1]), encoding="cp1252", errors="replace").read().split("\n")[int(c[2])]
            l = "\t".join(("SCENARIO", c[1], c[2], en.rstrip("\r\n"), idx_map[(c[1], c[2])], "按地图/编制复核改正"))
            done.add((c[1], c[2]))
        out.append(l)
    add = []
    for fn, i, zh in SET:
        if (fn, str(i)) in done:
            continue
        p = os.path.join(BK, fn)
        if not os.path.isfile(p):
            print("   ⚠️ 无备份 %s" % fn)
            continue
        en = io.open(p, encoding="cp1252", errors="replace").read().split("\n")[i]
        add.append("\t".join(("SCENARIO", fn, str(i), en.rstrip("\r\n"), zh, "按地图/编制复核改正")))
    print("\n=== ② 改正/新增 %d 条 ===" % (len(SET)))
    for fn, i, zh in SET:
        print("   %-22s 行%-4d → %s" % (fn, i, zh))
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0
    os.makedirs(CBK, exist_ok=True)
    b = os.path.join(CBK, os.path.basename(OVF))
    if not os.path.isfile(b):
        shutil.copy2(OVF, b)
    if add:
        if not out[-1].endswith("\n"):
            out[-1] += "\n"
        out += add
    io.open(OVF, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("✅ 已写 %s（撤回 %d · 改正/新增 %d）" % (OVF, len(dropped), len(SET)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
