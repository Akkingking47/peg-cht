#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**待定缩写 · 查史料后定稿**（生成补充提案 TSV）。

用户 2026-10-12：「可以的。查史料订吧」

【定稿译法 + 依据】
 ① `AASC` → `陆军勤务部队(AASC)`
    AWM 档案「HQ AASC [Australian Army Service Corps] **2 Armoured Division**」——
    本行正位于「…/2」第2装甲师编制内（同组 1R/2、7R/2、1KDG/2、1KRR/2）✓
 ② `1/SATC` `2/SATC` `3/SATC` → `第N/南非装甲运输队`
    词库既有 `SATC → 南非装甲运输队`（本项目既定译法，保持一致）
 ③ `KTR 9` → `第9野战炮兵团(KTR 9)`
    芬兰 Kenttätykistörykmentti＝野战炮兵团（芬兰国家档案馆编制表）；场景＝苏奥穆萨尔米（芬兰）✓
 ④ `USSAF` → `美国陆军航空队`
    同文件相邻两行即作此译；`USSAF` 系 `USAAF` 拼写笔误
 ⑤ `1/XXI` `5/XXI` `2/XXI` → `第N/第21军`；`4A/XXI` → `4A/第21军`
    同文件既有先例 `1/XX → 第1/第20`（军团罗马序号译作数字＋「军」）；XXI＝意军第21军
 ⑥ `atB/HG D` → `atB/赫尔曼·戈林师`
    词库既有 `Hermann Goering → 赫尔曼·戈林师`；`atB` 按本文件体例保留（同文件 `Novara B`、`1 Br` 亦保留）
 ⑦ `HMS B/Carpathian Rifle Brigade/ Polish` → `HMS B/喀尔巴阡步枪旅/波兰`
    词库既有「喀尔巴阡步枪师」；`HMS B` 舰名不明⇒保留
 ⑧ `1ERY/1R` → `第1东赖丁义勇骑兵团/1R`；`1FFY/1R` → `第1法夫-福法尔义勇骑兵团/1R`
    ERY＝East Riding Yeomanry（东赖丁义勇骑兵团）· FFY＝Fife & Forfar Yeomanry（法夫-福法尔义勇骑兵团）；
    后缀 `/1R` 含义未定⇒保留（另有 `[BEF]` 变体同法处理）
 ⑨ `SRAF` → `苏联空军(SRAF)`
    位置证据：`LAH_IT_13`（普罗霍罗夫卡）尾部与「第169坦克旅/第26坦克旅」等**苏军**单位同组；
    SRAF 仅见于 4 个苏德战场文件 ⇒ Soviet Red Air Force

【查过但**决定保留**（不译，另附报告）】
 `PSZ`（词库体例＝后缀保留，如 `44 Piechota PSZ→44 步兵 PSZ`）·`TNG`/`NG`（词库自映射保留，
 且 `158TNGD→第158TNGD`）·`TFH`（证据矛盾：词库有 `TFH→第19装甲军`，但本处为美军编成）·
 `HvH`/`Roz`（不可考，同文件 `Pag` 亦保留）·`MTF`（疑苏式地图标注 МТФ＝乳牛场，证据不足）

用法: python gen_pending_supplement.py
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
BK = os.path.join(WS, "pegww2", "testbed", "backup")
OUT = os.path.join(WS, "work", "glossary", "_番号第二批-提案-补充2.tsv")

# 规则：(文件, 原文正则, 译法函数)；子目录固定 SCENARIO
RULES = [
    ("tobruk-R_u.txt", r"^AASC$", lambda m: "陆军勤务部队(AASC)"),
    ("RM_usvsruss19_i.txt", r"^AASC$", lambda m: "陆军勤务部队(AASC)"),
    ("DAK_SPS04_u.txt", r"^([123])/SATC$", lambda m: "%s/南非装甲运输队" % m.group(1)),
    ("SUOMUSS.TXT", r"^KTR (\d+)$", lambda m: "第%s野战炮兵团(KTR %s)" % (m.group(1), m.group(1))),
    ("suomuss-R_u.txt", r"^KTR (\d+)$", lambda m: "第%s野战炮兵团(KTR %s)" % (m.group(1), m.group(1))),
    ("NORDWIND.TXT", r"^USSAF$", lambda m: "美国陆军航空队"),
    ("nordwind-R_u.txt", r"^USSAF$", lambda m: "美国陆军航空队"),
    ("wdela2_u.txt", r"^([0-9]+)/XXI$", lambda m: "%s/第21军" % m.group(1)),
    ("wdela2_u.txt", r"^([0-9]+A)/XXI$", lambda m: "%s/第21军" % m.group(1)),
    ("DAK_TU06_u.txt", r"^atB/HG D$", lambda m: "atB/赫尔曼·戈林师"),
    ("DAK_SPE02_u.txt", r"^HMS B/Carpathian Rifle Brigade/ Polish$",
     lambda m: "HMS B/喀尔巴阡步枪旅/波兰"),
    ("LAH_IT_08_u.txt", r"^SRAF$", lambda m: "苏联空军(SRAF)"),
    ("LAH_IT_12_u.txt", r"^SRAF$", lambda m: "苏联空军(SRAF)"),
    ("LAH_IT_13_u.txt", r"^SRAF$", lambda m: "苏联空军(SRAF)"),
    ("LAH_IT_Kherson_u.txt", r"^SRAF$", lambda m: "苏联空军(SRAF)"),
    (None, r"^1ERY(/1R)?$", lambda m: "第1东赖丁义勇骑兵团" + (m.group(1) or "")),
    (None, r"^1FFY(/1R)?$", lambda m: "第1法夫-福法尔义勇骑兵团" + (m.group(1) or "")),
    (None, r"^1ERY/1R \[BEF\]$", lambda m: "第1东赖丁义勇骑兵团/1R [BEF]"),
    (None, r"^1FFY/1R \[BEF\]$", lambda m: "第1法夫-福法尔义勇骑兵团/1R [BEF]"),
]
WHY = {"AASC": "AWM 档案：HQ AASC(Australian Army Service Corps) 2 Armoured Division——本行在第2装甲师编制内",
       "SATC": "词库既有 SATC→南非装甲运输队",
       "KTR": "芬兰 Kenttätykistörykmentti＝野战炮兵团（芬兰国家档案馆编制表）",
       "USSAF": "同文件相邻行作「美国陆军航空队」；USSAF 系 USAAF 笔误",
       "XXI": "同文件既有先例 1/XX→第1/第20（罗马序号译作数字＋军）；XXI＝意军第21军",
       "HG": "词库既有 Hermann Goering→赫尔曼·戈林师；atB 按本文件体例保留",
       "Carpathian": "词库既有「喀尔巴阡步枪师」；HMS B 舰名不明⇒保留",
       "SRAF": "位置证据：与苏军坦克旅同组（LAH_IT_13 普罗霍罗夫卡）⇒ Soviet Red Air Force",
       "ERY": "ERY＝East Riding Yeomanry（东赖丁义勇骑兵团）；后缀 /1R 含义未定⇒保留",
       "FFY": "FFY＝Fife & Forfar Yeomanry（法夫-福法尔义勇骑兵团）；后缀 /1R 含义未定⇒保留"}


def why_for(en):
    for k, v in WHY.items():
        if k in en:
            return v
    return "查史料定稿"


def main():
    rows, files = [], []
    allf = sorted(os.listdir(os.path.join(GAME, "SCENARIO")))
    for fn_pat, pat, tr in RULES:
        targets = [fn_pat] if fn_pat else allf
        rx = re.compile(pat)
        for fn in targets:
            if not fn or not fn.lower().endswith(".txt"):
                continue
            gp = os.path.join(GAME, "SCENARIO", fn)
            if not os.path.isfile(gp):
                continue
            zh = io.open(gp, encoding="gbk", errors="replace").read().split("\n")
            bp = os.path.join(BK, "SCENARIO", fn)
            en_src = io.open(bp, encoding="cp1252", errors="replace").read().split("\n") if os.path.isfile(bp) else None
            for i, l in enumerate(zh):
                s = l.strip()
                m = rx.match(s)
                if not m:
                    continue
                en = en_src[i].rstrip("\r\n") if en_src and i < len(en_src) else s
                nt = tr(m)
                if nt == s:
                    continue
                rows.append(("SCENARIO", fn, str(i), en, nt, why_for(en)))
                if fn not in files:
                    files.append(fn)
    print("=== 生成待落 %d 条 · %d 个文件 ===" % (len(rows), len(files)))
    for r in rows:
        print("   %-22s 行%-4s %-30s → %s" % (r[1], r[2], r[3][:30], r[4][:34]))
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as w:
        w.write("# 待定缩写 · 查史料定稿（captain 生成）\n")
        w.write("# 列：子目录 / 文件 / 行号(0-based) / 期望原文 / 拟译 / 依据\n")
        for r in rows:
            w.write("\t".join(r) + "\n")
    print("\n→ %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
